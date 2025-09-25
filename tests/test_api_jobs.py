# tests/test_api_jobs.py
from fastapi.testclient import TestClient
from api.main import app
from db.models import Job

client = TestClient(app)

def test_jobs_endpoint_empty_then_with_one(db_session):
    # Initially empty
    resp = client.get("/api/jobs")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) == 0

    # Insert one
    db_session.add(Job(title="ML Engineer", company="Beta Inc"))
    db_session.commit()

    resp2 = client.get("/api/jobs")
    assert resp2.status_code == 200
    data = resp2.json()
    assert len(data) == 1
    assert data[0]["title"] == "ML Engineer"
    assert data[0]["company"] == "Beta Inc"
