import pytest
from fastapi.testclient import TestClient
from scos.app import app
from scos.config import RUNTIME
from scos import storage


def test_unauthenticated_workspace_denied():
    with TestClient(app) as client:
        assert client.get("/api/v1/workspace").status_code == 401


def test_login_requires_local_origin():
    with TestClient(app) as client:
        assert client.post("/api/v1/auth/local", headers={"Origin": "https://evil.example"}).status_code == 403


def test_mutation_requires_csrf_and_correct_origin():
    with TestClient(app) as client:
        auth = client.post("/api/v1/auth/local", headers={"Origin": "http://127.0.0.1:3100"}).json()
        body = {"payload": {"title": "Should never be created"}}
        assert (
            client.post(
                "/api/v1/actions/opportunity.create", json=body, headers={"Origin": "http://127.0.0.1:3100"}
            ).status_code
            == 403
        )
        headers = {
            "Origin": "https://evil.example",
            "X-CSRF-Token": auth["csrf_token"],
            "Idempotency-Key": "test-key-123",
        }
        assert client.post("/api/v1/actions/opportunity.create", json=body, headers=headers).status_code == 403


def test_valid_mutation_requires_idempotency_key():
    with TestClient(app) as client:
        auth = client.post("/api/v1/auth/local", headers={"Origin": "http://127.0.0.1:3100"}).json()
        headers = {"Origin": "http://127.0.0.1:3100", "X-CSRF-Token": auth["csrf_token"]}
        response = client.post(
            "/api/v1/actions/opportunity.create", json={"payload": {"title": "A fresh idea"}}, headers=headers
        )
        assert response.status_code == 422


def test_logout_revokes_session():
    with TestClient(app) as client:
        auth = client.post("/api/v1/auth/local", headers={"Origin": "http://127.0.0.1:3100"}).json()
        assert (
            client.post(
                "/api/v1/auth/logout", headers={"Origin": "http://127.0.0.1:3100", "X-CSRF-Token": auth["csrf_token"]}
            ).status_code
            == 200
        )
        assert client.get("/api/v1/workspace").status_code == 401


def test_storage_path_cannot_escape_objects():
    with pytest.raises(ValueError):
        storage.read("../backup.sql")


def test_storage_detects_replaced_bytes():
    p = RUNTIME / "test-corruption.dat"
    p.write_bytes(b"original immutable data")
    key, digest, _ = storage.put(p)
    (RUNTIME / key).write_bytes(b"corrupted")
    with pytest.raises(ValueError):
        storage.read(key, digest)


def test_backup_path_not_available_as_export():
    with TestClient(app) as client:
        client.post("/api/v1/auth/local", headers={"Origin": "http://127.0.0.1:3100"})
        assert client.get("/api/v1/exports/backup.sql/preview").status_code == 422


def test_production_and_cross_project_resources_fail_closed(monkeypatch):
    import scos.config as config

    monkeypatch.setattr(config, "ENV", "production")
    with pytest.raises(RuntimeError):
        config.validate()
    monkeypatch.setattr(config, "ENV", "local")
    monkeypatch.setattr(config, "DATABASE_URL", "postgresql://user:pass@localhost/scrapper")
    with pytest.raises(RuntimeError):
        config.validate()


def test_corrupt_image_upload_is_rejected():
    with TestClient(app) as client:
        auth = client.post("/api/v1/auth/local", headers={"Origin": "http://127.0.0.1:3100"}).json()
        headers = {
            "Origin": "http://127.0.0.1:3100",
            "X-CSRF-Token": auth["csrf_token"],
            "Idempotency-Key": "upload-test-123",
        }
        response = client.post(
            "/api/v1/assets/upload", files={"file": ("../../escape.png", b"not a PNG", "image/png")}, headers=headers
        )
        assert response.status_code == 422


def test_owned_image_upload_quarantines_and_sanitizes_filename():
    import io
    from PIL import Image
    from scos.db import connect, one

    b = io.BytesIO()
    Image.new("RGB", (100, 100), "coral").save(b, format="PNG")
    with TestClient(app) as client:
        auth = client.post("/api/v1/auth/local", headers={"Origin": "http://127.0.0.1:3100"}).json()
        headers = {
            "Origin": "http://127.0.0.1:3100",
            "X-CSRF-Token": auth["csrf_token"],
            "Idempotency-Key": "upload-test-123",
        }
        response = client.post(
            "/api/v1/assets/upload", files={"file": ("../../escape.png", b.getvalue(), "image/png")}, headers=headers
        )
        assert response.status_code == 200
        row = response.json()
        assert row["filename"] == "escape.png"
        assert row["status"] == "quarantine"
        with connect() as c:
            assert one(c, "SELECT count(*) AS n FROM asset_rights WHERE asset_id=%s", (row["id"],))["n"] == 0
