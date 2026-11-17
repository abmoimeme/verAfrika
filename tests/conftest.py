import os

os.environ.setdefault("VERAFRIKA_DATABASE_URL", "postgresql://postgres@/verafrika_test?host=/tmp/pg&port=5433")
os.environ["VERAFRIKA_ENV"] = "development"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import connect  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import reset  # noqa: E402


@pytest.fixture()
def client():
    with connect() as conn:
        reset(conn)
    return TestClient(app)


@pytest.fixture()
def login(client):
    def _login(user_id: str) -> dict:
        r = client.post("/v1/dev/sessions", json={"user_id": user_id})
        assert r.status_code == 200, r.text
        client.cookies.clear()
        return {"Authorization": f"Bearer {r.json()['token']}"}
    return _login


@pytest.fixture()
def published(client, login):
    """Run the initial snapshot and have the analyst approve it. Returns (opportunity_id, analyst headers)."""
    analyst = login("usr_fatou")
    r = client.post("/v1/admin/sources/sn-synthetic-procurement/runs", json={"snapshot": "initial"}, headers=analyst)
    assert r.status_code == 200, r.text
    task = client.get("/v1/admin/review-tasks", headers=analyst).json()["tasks"][0]
    r = client.post(f"/v1/admin/review-tasks/{task['id']}/approve", json={}, headers=analyst)
    assert r.status_code == 200, r.text
    return r.json()["opportunity_id"], analyst
