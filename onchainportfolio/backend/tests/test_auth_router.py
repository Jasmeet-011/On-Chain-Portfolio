# backend/tests/test_auth_router.py
"""
Integration tests for the /auth router.

All external dependencies (MongoDB, email, scheduler) are mocked so tests
run without any live services.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from bson import ObjectId

import pytest

# Ensure backend/ is on the path
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# ---------------------------------------------------------------------------
# Patch every import that touches MongoDB / Redis / APScheduler BEFORE the
# app module is imported.  This prevents real connections during testing.
# ---------------------------------------------------------------------------

_FAKE_USER_ID = str(ObjectId())

_FAKE_USER = {
    "_id": ObjectId(_FAKE_USER_ID),
    "name": "Test User",
    "email": "test@example.com",
    "hashed_password": "hashed_pw",
    "wallet_address": None,
    "is_email_verified": True,
    "email_verification_token": "tok123",
}


@pytest.fixture(scope="module")
def client():
    """
    Create a TestClient with all side-effecting startup code mocked out.
    """
    with (
        patch("pymongo.MongoClient"),
        patch("app.services.cache.initialize_cache"),
        patch("app.services.wallet_service.migrate_all_users", return_value={}),
        patch("app.services.scheduler.AlertScheduler.start"),
        patch("app.services.scheduler.AlertScheduler.stop"),
        patch("app.services.snapshot_service.SnapshotService.save_all_user_snapshots"),
    ):
        from fastapi.testclient import TestClient
        from app.main import app

        with TestClient(app, raise_server_exceptions=True) as c:
            yield c


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _auth_header(user_id: str = _FAKE_USER_ID) -> dict:
    """Mint a real JWT so that get_current_user passes."""
    from app.services.auth_service import create_access_token
    token = create_access_token(user_id=user_id)
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# POST /auth/signup
# ---------------------------------------------------------------------------

class TestSignup:
    def test_signup_success(self, client):
        with (
            patch("app.routers.auth.get_user_by_email", return_value=None),
            patch("app.routers.auth.create_user", return_value=_FAKE_USER),
            patch("app.routers.auth.create_access_token", return_value="fake_token"),
            patch("app.routers.auth.list_user_wallets", return_value=[]),
            patch("app.services.email_service.EmailService.send_verification_email"),
        ):
            resp = client.post("/auth/signup", json={
                "name": "Test User",
                "email": "test@example.com",
                "password": "password123",
            })

        assert resp.status_code == 201
        body = resp.json()
        assert "access_token" in body
        assert body["user"]["email"] == "test@example.com"

    def test_signup_duplicate_email(self, client):
        with patch("app.routers.auth.get_user_by_email", return_value=_FAKE_USER):
            resp = client.post("/auth/signup", json={
                "name": "Test User",
                "email": "test@example.com",
                "password": "password123",
            })

        assert resp.status_code == 400
        assert "already registered" in resp.json()["detail"].lower()

    def test_signup_missing_fields(self, client):
        resp = client.post("/auth/signup", json={"email": "test@example.com"})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------

class TestLogin:
    def test_login_success(self, client):
        with (
            patch("app.routers.auth.authenticate_user", return_value=_FAKE_USER),
            patch("app.routers.auth.create_access_token", return_value="fake_token"),
            patch("app.routers.auth.list_user_wallets", return_value=[]),
        ):
            resp = client.post("/auth/login", json={
                "email": "test@example.com",
                "password": "password123",
            })

        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        with patch("app.routers.auth.authenticate_user", return_value=None):
            resp = client.post("/auth/login", json={
                "email": "test@example.com",
                "password": "wrong",
            })

        assert resp.status_code == 401

    def test_login_missing_fields(self, client):
        resp = client.post("/auth/login", json={"email": "test@example.com"})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------

class TestGetMe:
    def test_get_me_authenticated(self, client):
        with (
            patch("app.deps.get_user_by_id", return_value=_FAKE_USER),
            patch("app.routers.auth.list_user_wallets", return_value=[]),
        ):
            resp = client.get("/auth/me", headers=_auth_header())

        assert resp.status_code == 200
        assert resp.json()["email"] == "test@example.com"

    def test_get_me_no_token(self, client):
        resp = client.get("/auth/me")
        assert resp.status_code == 403

    def test_get_me_invalid_token(self, client):
        resp = client.get("/auth/me", headers={"Authorization": "Bearer bad_token"})
        assert resp.status_code == 401
