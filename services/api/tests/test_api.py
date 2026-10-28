from fastapi.testclient import TestClient
from scos.app import app


def test_workspace_loads_every_schema_table():
    with TestClient(app) as client:
        response = client.post("/api/v1/auth/local", headers={"Origin": "http://127.0.0.1:3100"})
        assert response.status_code == 200
        response = client.get("/api/v1/workspace")
        assert response.status_code == 200
        assert response.json()["publishing_disabled"] is True
