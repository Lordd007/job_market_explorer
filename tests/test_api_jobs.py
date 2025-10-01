# tests/test_api_jobs.py
from fastapi.testclient import TestClient
from api.main import app
from db.models import Job

client = TestClient(app)

def test_jobs_endpoint_empty_then_with_one(db_session):
    # Initially empty
    resp = client.get("/api/jobs")
    assert resp.status_code == 200

    data = resp.json()
    assert isinstance(data, dict)
    assert data["total"] == 0
    assert isinstance(data["items"], list)
    assert data["items"] == []

    # Insert one job
    db_session.add(Job(title="ML Engineer", company="Beta Inc"))
    db_session.commit()

    # Check again
    resp2 = client.get("/api/jobs")
    assert resp2.status_code == 200

    data2 = resp2.json()
    assert data2["total"] == 1
    assert isinstance(data2["items"], list)
    assert len(data2["items"]) == 1

    job = data2["items"][0]
    assert job["title"] == "ML Engineer"
    assert job["company"] == "Beta Inc"

