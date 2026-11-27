import asyncio
import logging
from datetime import datetime

import pytest
from sqlalchemy import select
from unittest.mock import AsyncMock, patch

from models import AlertSettings, CVProfile, SeenJob, User
from services import alert_service
from services.ntfy_service import NtfyError
from tests.conftest import TestSession, TEST_USER_ID

TOPIC = "sw-test-topic-9f3k2"


def make_job(n: int, **overrides) -> dict:
    job = {
        "external_id": str(n), "source": "adzuna", "title": f"Junior Dev {n}", "company": f"Corp {n}",
        "location": "Glasgow", "salary_min": 28000, "salary_max": 35000,
        "url": f"https://example.com/job/{n}", "description": f"Python role {n}",
    }
    job.update(overrides)
    return job


async def add_cv(user_id: int = TEST_USER_ID) -> None:
    async with TestSession() as session:
        session.add(CVProfile(user_id=user_id, raw_text="synthetic cv", skills=["Python"],
                              job_titles=["Developer"], keywords=["FastAPI"]))
        await session.commit()


async def mark_seen(*jobs: dict, user_id: int = TEST_USER_ID) -> None:
    async with TestSession() as session:
        for job in jobs:
            session.add(SeenJob(user_id=user_id, external_id=job["external_id"], source=job["source"]))
        await session.commit()


async def seen_keys(user_id: int = TEST_USER_ID) -> set[tuple[str, str]]:
    async with TestSession() as session:
        rows = (await session.execute(select(SeenJob).where(SeenJob.user_id == user_id))).scalars().all()
        return {(r.external_id, r.source) for r in rows}


BASELINE_DONE = datetime(2026, 11, 1, 9, 0, 0)


def settings_for(user_id: int = TEST_USER_ID, **overrides) -> AlertSettings:
    values = dict(user_id=user_id, enabled=True, query="junior developer", locations=["Glasgow"],
                  min_score=70, ntfy_topic=TOPIC, baseline_at=BASELINE_DONE)
    values.update(overrides)
    return AlertSettings(**values)


def scores_by_id(mapping: dict[str, int | Exception]):
    async def fake_score(cv_skills: list[str], description: str) -> dict:
        job_id = description.rsplit(" ", 1)[-1]
        value = mapping[job_id]
        if isinstance(value, Exception):
            raise value
        return {"score": value, "matched": ["Python"], "missing": []}
    return fake_score


async def run_scan(jobs: list[dict], score_fn=None, settings: AlertSettings | None = None, push_side_effect=None):
    fetch = AsyncMock(return_value=jobs)
    score = AsyncMock(side_effect=score_fn or scores_by_id({}))
    push = AsyncMock(side_effect=push_side_effect)
    with patch("routers.jobs._fetch_for_location", fetch), \
         patch("services.alert_service.score_job_match", score), \
         patch("services.alert_service.ntfy_service.send_push", push):
        async with TestSession() as session:
            result = await alert_service.scan_user(session, settings or settings_for())
    return result, fetch, score, push


@pytest.mark.asyncio
async def test_scan_without_cv_records_nothing_and_calls_nothing():
    result, fetch, score, push = await run_scan([make_job(1)])

    assert result.skipped_no_cv is True
    assert await seen_keys() == set()
    fetch.assert_not_awaited()
    score.assert_not_awaited()
    push.assert_not_awaited()


@pytest.mark.asyncio
async def test_first_scan_records_all_jobs_without_scoring_or_pushing():
    await add_cv()
    settings = settings_for(baseline_at=None)

    result, _, score, push = await run_scan([make_job(1), make_job(2)], settings=settings)

    assert result.baseline is True
    assert settings.baseline_at is not None
    assert await seen_keys() == {("1", "adzuna"), ("2", "adzuna")}
    score.assert_not_awaited()
    push.assert_not_awaited()


@pytest.mark.asyncio
async def test_scan_pushes_new_matches_highest_score_first_with_job_details():
    await add_cv()
    await mark_seen(make_job(0))

    _, _, _, push = await run_scan(
        [make_job(1), make_job(2), make_job(3, salary_min=None, salary_max=None)],
        scores_by_id({"1": 75, "2": 90, "3": 40}),
    )

    assert [c.kwargs["title"] for c in push.await_args_list] == ["Junior Dev 2 at Corp 2", "Junior Dev 1 at Corp 1"]
    first = push.await_args_list[0].kwargs
    assert first["topic"] == TOPIC
    assert first["click_url"] == "https://example.com/job/2"
    assert "90" in first["message"]
    assert "Glasgow" in first["message"]
    assert "£28,000" in first["message"]


@pytest.mark.asyncio
async def test_scan_records_scored_jobs_below_threshold_as_seen():
    await add_cv()
    await mark_seen(make_job(0))

    await run_scan([make_job(1)], scores_by_id({"1": 10}))

    assert ("1", "adzuna") in await seen_keys()


@pytest.mark.asyncio
async def test_scan_does_not_rescore_or_repush_seen_jobs():
    await add_cv()
    await mark_seen(make_job(0), make_job(1))

    _, _, score, push = await run_scan([make_job(1), make_job(2)], scores_by_id({"2": 95}))

    assert score.await_count == 1
    assert score.await_args.args[1] == "Python role 2"
    assert [c.kwargs["click_url"] for c in push.await_args_list] == ["https://example.com/job/2"]


@pytest.mark.asyncio
async def test_failed_scoring_leaves_job_unseen_and_it_is_scored_again_next_scan():
    await add_cv()
    await mark_seen(make_job(0))

    _, _, _, push = await run_scan([make_job(1), make_job(2)],
                                   scores_by_id({"1": RuntimeError("claude down"), "2": 80}))

    assert await seen_keys() == {("0", "adzuna"), ("2", "adzuna")}
    assert [c.kwargs["click_url"] for c in push.await_args_list] == ["https://example.com/job/2"]

    _, _, score, push = await run_scan([make_job(1), make_job(2)], scores_by_id({"1": 85}))

    assert score.await_count == 1
    assert ("1", "adzuna") in await seen_keys()
    assert [c.kwargs["click_url"] for c in push.await_args_list] == ["https://example.com/job/1"]


@pytest.mark.asyncio
async def test_job_seen_by_another_user_is_still_new():
    await add_cv()
    async with TestSession() as session:
        other = User(email="other@example.com", hashed_password="hashed")
        session.add(other)
        await session.commit()
        other_id = other.id
    await mark_seen(make_job(1), user_id=other_id)
    await mark_seen(make_job(0))

    _, _, score, push = await run_scan([make_job(1)], scores_by_id({"1": 88}))

    assert score.await_count == 1
    assert push.await_count == 1


@pytest.mark.asyncio
async def test_more_than_five_matches_sends_top_five_and_one_summary():
    await add_cv()
    await mark_seen(make_job(0))
    jobs = [make_job(n) for n in range(1, 8)]

    _, _, _, push = await run_scan(jobs, scores_by_id({str(n): 70 + n for n in range(1, 8)}))

    titles = [c.kwargs["title"] for c in push.await_args_list]
    assert titles[:5] == [f"Junior Dev {n} at Corp {n}" for n in (7, 6, 5, 4, 3)]
    assert len(titles) == 6
    assert "+2 more matches in SearchWork" in (push.await_args_list[5].kwargs["title"]
                                               + push.await_args_list[5].kwargs["message"])


@pytest.mark.asyncio
async def test_exactly_five_matches_sends_no_summary():
    await add_cv()
    await mark_seen(make_job(0))

    _, _, _, push = await run_scan([make_job(n) for n in range(1, 6)],
                                   scores_by_id({str(n): 80 for n in range(1, 6)}))

    assert push.await_count == 5


@pytest.mark.asyncio
async def test_no_matches_sends_no_push():
    await add_cv()
    await mark_seen(make_job(0))

    _, _, _, push = await run_scan([make_job(1)], scores_by_id({"1": 69}))

    push.assert_not_awaited()


@pytest.mark.asyncio
async def test_scan_applies_uk_eligibility_and_junior_filters():
    await add_cv()
    await mark_seen(make_job(0))
    jobs = [
        make_job(1),
        make_job(2, title="Senior Engineer"),
        make_job(3, location="Berlin, Germany"),
        make_job(4, description="Python role 4 SC cleared required"),
    ]

    _, _, score, _ = await run_scan(jobs, scores_by_id({"1": 50}))

    assert score.await_count == 1
    assert await seen_keys() == {("0", "adzuna"), ("1", "adzuna")}


@pytest.mark.asyncio
async def test_empty_locations_scan_default_cities():
    from routers.jobs import DEFAULT_LOCATIONS

    await add_cv()

    _, fetch, _, _ = await run_scan([], settings=settings_for(locations=[]))

    assert sorted(c.args[1] for c in fetch.await_args_list) == sorted(DEFAULT_LOCATIONS)


@pytest.mark.asyncio
async def test_failed_push_does_not_stop_other_pushes_or_leak_topic(caplog):
    await add_cv()
    await mark_seen(make_job(0))

    with caplog.at_level(logging.DEBUG):
        _, _, _, push = await run_scan([make_job(1), make_job(2)], scores_by_id({"1": 80, "2": 90}),
                                       push_side_effect=[NtfyError("ntfy returned 500"), None])

    assert push.await_count == 2
    assert {("1", "adzuna"), ("2", "adzuna")} <= await seen_keys()
    assert TOPIC not in caplog.text


@pytest.mark.asyncio
async def test_first_scan_with_no_jobs_still_completes_baseline_so_later_jobs_are_pushed():
    await add_cv()
    settings = settings_for(baseline_at=None)

    first, _, _, _ = await run_scan([], settings=settings)
    second, _, score, push = await run_scan([make_job(1)], scores_by_id({"1": 90}), settings=settings)

    assert first.baseline is True
    assert second.baseline is False
    assert score.await_count == 1
    assert [c.kwargs["click_url"] for c in push.await_args_list] == ["https://example.com/job/1"]


@pytest.mark.asyncio
async def test_scoring_runs_at_most_five_claude_calls_at_once():
    await add_cv()
    in_flight = 0
    peak = 0

    async def slow_score(cv_skills: list[str], description: str) -> dict:
        nonlocal in_flight, peak
        in_flight += 1
        peak = max(peak, in_flight)
        await asyncio.sleep(0.01)
        in_flight -= 1
        return {"score": 10, "matched": [], "missing": []}

    _, _, score, _ = await run_scan([make_job(n) for n in range(1, 21)], slow_score)

    assert score.await_count == 20
    assert peak == alert_service.MAX_CONCURRENT_SCORING == 5


@pytest.mark.asyncio
async def test_failing_job_source_is_skipped_and_other_sources_still_alert():
    from routers import jobs as job_search

    await add_cv()
    source_names = ["adzuna_service", "reed_service", "jsearch_service", "remotive_service",
                    "weworkremotely_service", "jobicy_service", "arbeitnow_service", "gradcracker_service",
                    "totaljobs_service", "cwjobs_service", "prospects_service"]
    patches = [patch.object(getattr(job_search, name), "search_jobs", AsyncMock(return_value=[]))
               for name in source_names]
    for p in patches:
        p.start()
    try:
        job_search.adzuna_service.search_jobs.side_effect = RuntimeError("adzuna down")
        job_search.reed_service.search_jobs.return_value = [make_job(1, source="reed")]
        push = AsyncMock()
        with patch("services.alert_service.score_job_match", AsyncMock(side_effect=scores_by_id({"1": 88}))), \
             patch("services.alert_service.ntfy_service.send_push", push):
            async with TestSession() as session:
                result = await alert_service.scan_user(session, settings_for())
    finally:
        for p in patches:
            p.stop()

    assert result.fetched == 1
    assert [c.kwargs["click_url"] for c in push.await_args_list] == ["https://example.com/job/1"]
    assert await seen_keys() == {("1", "reed")}
