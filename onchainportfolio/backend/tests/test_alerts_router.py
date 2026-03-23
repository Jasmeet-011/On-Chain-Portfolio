# backend/tests/test_alerts_router.py
"""
Integration tests for the /v1/alerts router.

All external dependencies (MongoDB, email, price service) are mocked.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
from bson import ObjectId
from datetime import datetime

import pytest

backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_FAKE_USER_ID = str(ObjectId())
_FAKE_ALERT_ID = str(ObjectId())

_FAKE_USER = {
    "_id": ObjectId(_FAKE_USER_ID),
    "name": "Alert Tester",
    "email": "alerts@example.com",
    "hashed_password": "hashed_pw",
    "is_email_verified": True,
}

_FAKE_ALERT = {
    "id": _FAKE_ALERT_ID,
    "user_id": _FAKE_USER_ID,
    "alert_type": "token",
    "token_symbol": "BTC",
    "chain": "ethereum",
    "condition": "above",
    "target_price": 100000.0,
    "current_price": 95000.0,
    "is_active": True,
    "is_recurring": False,
    "status": "active",
    "last_triggered": None,
    "trigger_count": 0,
    "last_checked": None,
    "created_at": datetime.utcnow().isoformat(),
    "updated_at": None,
    "portfolio_metric": None,
    "wallet_address": None,
    "target_value": None,
}


# ---------------------------------------------------------------------------
# Mock AlertService
# ---------------------------------------------------------------------------

def _make_mock_alert_service():
    svc = MagicMock()
    svc.create_alert.return_value = MagicMock(**_FAKE_ALERT)
    svc.get_user_alerts.return_value = [MagicMock(**_FAKE_ALERT)]
    svc.get_alert.return_value = MagicMock(**_FAKE_ALERT)
    svc.delete_alert.return_value = True
    svc.get_alert_stats.return_value = {
        "total_alerts": 1, "active_alerts": 1,
        "triggered_today": 0, "triggered_this_week": 0, "triggered_total": 0,
    }
    svc.send_test_alert = AsyncMock(return_value=True)
    svc.check_all_alerts = AsyncMock(return_value={"portfolio": 0, "token": 0, "wallet": 0, "total": 0})
    return svc


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
        from app.deps import get_current_user, get_alert_service

        mock_svc = _make_mock_alert_service()

        app.dependency_overrides[get_current_user] = lambda: _FAKE_USER
        app.dependency_overrides[get_alert_service] = lambda: mock_svc

        with TestClient(app, raise_server_exceptions=True) as c:
            # Attach mock for per-test tweaks
            c.alert_service = mock_svc
            yield c

        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /v1/alerts
# ---------------------------------------------------------------------------

class TestCreateAlert:
    def test_create_token_alert_success(self, client):
        resp = client.post("/v1/alerts/", json={
            "alert_type": "token",
            "token_symbol": "BTC",
            "chain": "ethereum",
            "condition": "above",
            "target_price": 100000.0,
        })

        assert resp.status_code in (200, 201)
        body = resp.json()
        assert body["token_symbol"] == "BTC"
        assert body["condition"] == "above"

    def test_create_alert_missing_required_field(self, client):
        # token alert without target_price should fail validation
        resp = client.post("/v1/alerts/", json={
            "alert_type": "token",
            "token_symbol": "ETH",
            "condition": "above",
            # missing target_price
        })
        # Expect 422 (validation) or 400 (service-level)
        assert resp.status_code in (400, 422)


# ---------------------------------------------------------------------------
# GET /v1/alerts
# ---------------------------------------------------------------------------

class TestListAlerts:
    def test_list_alerts_returns_list(self, client):
        resp = client.get("/v1/alerts/")

        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) == 1
        assert body[0]["token_symbol"] == "BTC"

    def test_list_alerts_stats_endpoint(self, client):
        resp = client.get("/v1/alerts/stats")

        assert resp.status_code == 200
        body = resp.json()
        assert "total_alerts" in body


# ---------------------------------------------------------------------------
# DELETE /v1/alerts/{alert_id}
# ---------------------------------------------------------------------------

class TestDeleteAlert:
    def test_delete_alert_success(self, client):
        client.alert_service.delete_alert.return_value = True
        resp = client.delete(f"/v1/alerts/{_FAKE_ALERT_ID}")

        assert resp.status_code == 200

    def test_delete_alert_not_found(self, client):
        client.alert_service.delete_alert.return_value = False
        resp = client.delete(f"/v1/alerts/{_FAKE_ALERT_ID}")

        assert resp.status_code in (404, 400)


# ---------------------------------------------------------------------------
# POST /v1/alerts/{alert_id}/test
# ---------------------------------------------------------------------------

class TestSendTestAlert:
    def test_send_test_alert(self, client):
        client.alert_service.send_test_alert = AsyncMock(return_value=True)
        resp = client.post(f"/v1/alerts/{_FAKE_ALERT_ID}/test")

        assert resp.status_code == 200
