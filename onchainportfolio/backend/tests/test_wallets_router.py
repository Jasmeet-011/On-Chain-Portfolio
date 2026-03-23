# backend/tests/test_wallets_router.py
"""
Integration tests for the /v1/wallets router.

All external dependencies (MongoDB, blockchain adapters) are mocked.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from bson import ObjectId

import pytest

backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_FAKE_USER_ID = str(ObjectId())

_FAKE_USER = {
    "_id": ObjectId(_FAKE_USER_ID),
    "name": "Wallet Tester",
    "email": "wallet@example.com",
    "hashed_password": "hashed_pw",
    "is_email_verified": True,
}

_FAKE_WALLET = {
    "id": str(ObjectId()),
    "user_id": _FAKE_USER_ID,
    "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f7CDEF",
    "chain": "ethereum",
    "type": "manual",
    "label": "My ETH Wallet",
    "is_primary": True,
    "created_at": "2026-01-01T00:00:00",
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    with (
        patch("pymongo.MongoClient"),
        patch("app.services.cache.initialize_cache"),
        patch("app.services.wallet_service.migrate_all_users", return_value={}),
        patch("app.services.scheduler.AlertScheduler.start"),
        patch("app.services.scheduler.AlertScheduler.stop"),
    ):
        from fastapi.testclient import TestClient
        from app.main import app

        # Override auth so every request is treated as _FAKE_USER
        from app.deps import get_current_user
        app.dependency_overrides[get_current_user] = lambda: _FAKE_USER

        with TestClient(app, raise_server_exceptions=True) as c:
            yield c

        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /v1/wallets
# ---------------------------------------------------------------------------

class TestCreateWallet:
    def test_create_wallet_success(self, client):
        with patch("app.routers.wallets.create_wallet", return_value=_FAKE_WALLET):
            resp = client.post("/v1/wallets", json={
                "address": _FAKE_WALLET["address"],
                "chain": "ethereum",
                "label": "My ETH Wallet",
            })

        assert resp.status_code in (200, 201)
        body = resp.json()
        assert body["address"] == _FAKE_WALLET["address"]
        assert body["chain"] == "ethereum"

    def test_create_wallet_duplicate(self, client):
        with patch("app.routers.wallets.create_wallet", return_value=None):
            resp = client.post("/v1/wallets", json={
                "address": _FAKE_WALLET["address"],
                "chain": "ethereum",
            })

        assert resp.status_code == 400

    def test_create_wallet_missing_address(self, client):
        resp = client.post("/v1/wallets", json={"chain": "ethereum"})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /v1/wallets
# ---------------------------------------------------------------------------

class TestListWallets:
    def test_list_wallets_returns_list(self, client):
        with patch("app.routers.wallets.list_user_wallets", return_value=[_FAKE_WALLET]):
            resp = client.get("/v1/wallets")

        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) == 1
        assert body[0]["chain"] == "ethereum"

    def test_list_wallets_empty(self, client):
        with patch("app.routers.wallets.list_user_wallets", return_value=[]):
            resp = client.get("/v1/wallets")

        assert resp.status_code == 200
        assert resp.json() == []


# ---------------------------------------------------------------------------
# DELETE /v1/wallets/{address}
# ---------------------------------------------------------------------------

class TestDeleteWallet:
    def test_delete_wallet_success(self, client):
        with patch("app.routers.wallets.delete_wallet", return_value=True):
            resp = client.delete(f"/v1/wallets/{_FAKE_WALLET['address']}")

        assert resp.status_code == 200
        assert "removed" in resp.json().get("message", "").lower()

    def test_delete_wallet_not_found(self, client):
        with patch("app.routers.wallets.delete_wallet", return_value=False):
            resp = client.delete("/v1/wallets/nonexistent_address")

        assert resp.status_code == 400
