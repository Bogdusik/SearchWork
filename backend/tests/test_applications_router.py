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


JOB_PAYLOAD = {
    "external_id": "test-1",
    "source": "adzuna",
    "title": "Test Job",
    "company": "Corp",
    "location": "London",
    "url": "https://example.com",
    "description": "Test",
    "match_score": 80,
}


@pytest.mark.asyncio
async def test_create_application(client):
    resp = await client.post("/applications", json={"job": JOB_PAYLOAD, "status": "applied"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "applied"
    assert data["job"]["external_id"] == "test-1"


@pytest.mark.asyncio
async def test_update_application_status(client):
    create_resp = await client.post("/applications", json={"job": JOB_PAYLOAD, "status": "applied"})
    app_id = create_resp.json()["id"]

    resp = await client.patch(f"/applications/{app_id}", json={"status": "interview"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "interview"


@pytest.mark.asyncio
async def test_create_duplicate_application_returns_409(client):
    await client.post("/applications", json={"job": JOB_PAYLOAD, "status": "applied"})
    resp = await client.post("/applications", json={"job": JOB_PAYLOAD, "status": "applied"})
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_invalid_status_returns_422(client):
    payload = dict(JOB_PAYLOAD, external_id="test-invalid")
    resp = await client.post("/applications", json={"job": payload, "status": "banana"})
    assert resp.status_code == 422
