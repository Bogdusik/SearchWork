import pytest
from models import SavedJob, Application


async def create_test_job(db):
    job = SavedJob(
        external_id="test-1", source="adzuna", title="Test Job", company="Corp",
        location="London", url="https://example.com", description="Test", match_score=80
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


@pytest.mark.asyncio
async def test_list_applications_empty(client):
    resp = await client.get("/applications")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_create_application(client):
    from tests.conftest import TestSession
    async with TestSession() as db:
        job = await create_test_job(db)

    resp = await client.post("/applications", json={"job_id": job.id, "status": "applied"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "applied"
    assert data["job"]["id"] == job.id


@pytest.mark.asyncio
async def test_update_application_status(client):
    from tests.conftest import TestSession
    async with TestSession() as db:
        job = await create_test_job(db)
        app = Application(job_id=job.id, status="applied")
        db.add(app)
        await db.commit()
        await db.refresh(app)

    resp = await client.patch(f"/applications/{app.id}", json={"status": "interview"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "interview"
