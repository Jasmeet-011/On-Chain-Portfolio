# backend/tests/test_chat_router.py
"""
Integration tests for the /v1/chat endpoint.

MongoDB, blockchain adapters, price service, and AI service are all mocked.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
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
    "name": "Chat Tester",
    "email": "chat@example.com",
    "hashed_password": "hashed_pw",
    "is_email_verified": True,
}

_FAKE_WALLET_DOC = {
    "_id": ObjectId(),
    "user_id": _FAKE_USER_ID,
    "address": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
    "chain": "aptos",
    "label": "Test Wallet",
    "is_primary": True,
    "type": "manual",
}

_FAKE_BALANCES = [
    {"symbol": "APT", "address": "0x1::aptos_coin::AptosCoin",
     "decimals": 8, "raw": "100000000", "amount": 1.0}
]

_FAKE_PRICES = {"APT": 8.0}


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
        from app.deps import get_current_user

        app.dependency_overrides[get_current_user] = lambda: _FAKE_USER

        with TestClient(app, raise_server_exceptions=True) as c:
            yield c

        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /v1/chat
# ---------------------------------------------------------------------------

class TestChat:
    def _mock_wallets_cursor(self):
        """Return a mock cursor yielding the fake wallet."""
        cursor = MagicMock()
        cursor.__iter__ = MagicMock(return_value=iter([_FAKE_WALLET_DOC]))
        return cursor

    def test_chat_returns_answer(self, client):
        mock_adapter = MagicMock()
        mock_adapter.get_token_balances.return_value = _FAKE_BALANCES

        with (
            patch("app.routers.chat.wallets_collection.find",
                  return_value=[_FAKE_WALLET_DOC]),
            patch("app.routers.chat.get_adapter_for_chain", return_value=mock_adapter),
            patch(
                "app.routers.chat.price_service.get_prices_async",
                new=AsyncMock(return_value=_FAKE_PRICES),
            ),
            patch(
                "app.routers.chat.generate_portfolio_response",
                return_value="You hold 1.0 APT worth $8.00.",
            ),
        ):
            resp = client.post("/v1/chat", json={"question": "What do I hold?"})

        assert resp.status_code == 200
        body = resp.json()
        assert "answer" in body
        assert "APT" in body["answer"] or body["answer"]
        assert "portfolio" in body
        assert body["portfolio"]["total_wallets"] == 1

    def test_chat_with_history_passes_history(self, client):
        """Ensure conversation history is forwarded to the AI service."""
        captured = {}

        def capture_generate(query, portfolio, wallet_results, history=None):
            captured["history"] = history
            return "Test reply."

        mock_adapter = MagicMock()
        mock_adapter.get_token_balances.return_value = []

        history = [
            {"role": "user", "text": "Hi"},
            {"role": "assistant", "text": "Hello!"},
        ]

        with (
            patch("app.routers.chat.wallets_collection.find",
                  return_value=[_FAKE_WALLET_DOC]),
            patch("app.routers.chat.get_adapter_for_chain", return_value=mock_adapter),
            patch(
                "app.routers.chat.price_service.get_prices_async",
                new=AsyncMock(return_value={}),
            ),
            patch("app.routers.chat.generate_portfolio_response",
                  side_effect=capture_generate),
        ):
            resp = client.post("/v1/chat", json={
                "question": "What's my portfolio?",
                "history": history,
            })

        assert resp.status_code == 200
        assert captured.get("history") == history

    def test_chat_no_wallets_returns_404(self, client):
        with patch("app.routers.chat.wallets_collection.find", return_value=[]):
            resp = client.post("/v1/chat", json={"question": "What do I hold?"})

        assert resp.status_code == 404
        assert "no wallets" in resp.json()["detail"].lower()

    def test_chat_scope_primary(self, client):
        mock_adapter = MagicMock()
        mock_adapter.get_token_balances.return_value = []

        with (
            patch("app.routers.chat.wallets_collection.find",
                  return_value=[_FAKE_WALLET_DOC]) as mock_find,
            patch("app.routers.chat.get_adapter_for_chain", return_value=mock_adapter),
            patch(
                "app.routers.chat.price_service.get_prices_async",
                new=AsyncMock(return_value={}),
            ),
            patch("app.routers.chat.generate_portfolio_response",
                  return_value="Primary wallet data."),
        ):
            resp = client.post("/v1/chat", json={
                "question": "Show my primary wallet",
                "scope": "primary",
            })

        assert resp.status_code == 200
        assert resp.json()["scope_used"] == "primary"

    def test_chat_empty_question_rejected(self, client):
        resp = client.post("/v1/chat", json={"question": ""})
        assert resp.status_code == 422

    def test_chat_missing_question_rejected(self, client):
        resp = client.post("/v1/chat", json={"scope": "all"})
        assert resp.status_code == 422
