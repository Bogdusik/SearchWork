import logging
from collections.abc import Awaitable, Callable

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_current_user
from database import get_db
from models import AlertSettings, User
from schemas import AlertSettingsIn, AlertSettingsOut
from services import ntfy_service

logger = logging.getLogger(__name__)


class _NoInputEchoRoute(APIRoute):
    """Validation errors normally echo the rejected value, which here can be the private ntfy topic."""

    def get_route_handler(self) -> Callable[[Request], Awaitable[Response]]:
        handler = super().get_route_handler()

        async def handler_without_input_echo(request: Request) -> Response:
            try:
                return await handler(request)
            except RequestValidationError as exc:
                cleaned = [{k: v for k, v in err.items() if k not in ("input", "ctx")} for err in exc.errors()]
                raise RequestValidationError(cleaned) from None

        return handler_without_input_echo


limiter = Limiter(key_func=get_remote_address)
router = APIRouter(route_class=_NoInputEchoRoute)


async def _get_settings(db: AsyncSession, user_id: int) -> AlertSettings | None:
    result = await db.execute(select(AlertSettings).where(AlertSettings.user_id == user_id))
    return result.scalar_one_or_none()


def _apply(settings: AlertSettings, body: AlertSettingsIn) -> None:
    if settings.query != body.query or settings.locations != body.locations:
        # A different search returns different jobs: take a fresh silent baseline instead of pushing them all.
        settings.baseline_at = None
    for field, value in body.model_dump().items():
        setattr(settings, field, value)


@router.get("/alerts", response_model=AlertSettingsOut | None, status_code=status.HTTP_200_OK)
async def get_alerts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _get_settings(db, current_user.id)


@router.put("/alerts", response_model=AlertSettingsOut, status_code=status.HTTP_200_OK)
async def put_alerts(
    body: AlertSettingsIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    settings = await _get_settings(db, current_user.id)
    if settings is None:
        settings = AlertSettings(user_id=current_user.id)
        db.add(settings)
        _apply(settings, body)
        try:
            await db.commit()
        except IntegrityError:
            # A concurrent first PUT from the same user inserted the row; update that one instead.
            await db.rollback()
            settings = await _get_settings(db, current_user.id)
            if settings is None:
                raise
            _apply(settings, body)
            await db.commit()
    else:
        _apply(settings, body)
        await db.commit()
    await db.refresh(settings)
    return settings


@router.post("/alerts/test", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("3/minute")
async def send_test_push(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    settings = await _get_settings(db, current_user.id)
    if settings is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Save alert settings first")
    try:
        await ntfy_service.send_push(
            topic=settings.ntfy_topic,
            title="SearchWork test",
            message="Job alerts are connected. You will get a push like this for new matching jobs.",
            tags=["white_check_mark"],
        )
    except ntfy_service.NtfyError as exc:
        logger.warning("Test push failed for user %s: %s", current_user.id, exc)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Could not reach ntfy") from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)
