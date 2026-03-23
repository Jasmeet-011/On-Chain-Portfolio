# backend/tests/test_balances_router.py
"""
Integration tests for the /v1/wallets/{address}/balances and
/v1/wallets/{address}/multi-chain-balances endpoints.

All external dependencies (MongoDB, blockchain adapters, price service) are mocked.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_APTOS_ADDR = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
_SOLANA_ADDR = "So11111111111111111111111111111111111111112"
_EVM_ADDR = "0x742d35Cc6634C0532925a3b844Bc9e7595f7CDEF"

_FAKE_RAW_BALANCES = [
    {
        "symbol": "APT",
        "address": "0x1::aptos_coin::AptosCoin",
        "decimals": 8,
        "raw": "100000000",
        "amount": 1.0,
    }
]

_FAKE_PRICES = {"APT": 7.5}
_FAKE_CHANGES = {"APT": {"change_24h": 3.2}}


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

        with TestClient(app, raise_server_exceptions=True) as c:
            yield c


# ---------------------------------------------------------------------------
# GET /v1/wallets/{address}/balances
# ---------------------------------------------------------------------------

class TestGetBalances:
    def test_returns_balance_list(self, client):
        mock_adapter = MagicMock()
        mock_adapter.normalize_address.return_value = _APTOS_ADDR
        mock_adapter.get_token_balances.return_value = _FAKE_RAW_BALANCES

        with (
            patch("app.routers.balances.get_adapter_for_chain", return_value=mock_adapter),
            patch("app.routers.balances.cache.get", return_value=None),
            patch("app.routers.balances.cache.set"),
            patch(
                "app.routers.balances.price_service.get_prices_async",
                new=AsyncMock(return_value=_FAKE_PRICES),
            ),
            patch(
                "app.routers.balances.price_service.get_prices_with_changes_async",
                new=AsyncMock(return_value=_FAKE_CHANGES),
            ),
        ):
            resp = client.get(f"/v1/wallets/{_APTOS_ADDR}/balances?chain=aptos")

        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) == 1
        assert body[0]["symbol"] == "APT"
        assert body[0]["usd_price"] == 7.5
        assert body[0]["change_24h"] == 3.2

    def test_usd_value_calculated(self, client):
        mock_adapter = MagicMock()
        mock_adapter.normalize_address.return_value = _APTOS_ADDR
        mock_adapter.get_token_balances.return_value = _FAKE_RAW_BALANCES

        with (
            patch("app.routers.balances.get_adapter_for_chain", return_value=mock_adapter),
            patch("app.routers.balances.cache.get", return_value=None),
            patch("app.routers.balances.cache.set"),
            patch(
                "app.routers.balances.price_service.get_prices_async",
                new=AsyncMock(return_value={"APT": 10.0}),
            ),
            patch(
                "app.routers.balances.price_service.get_prices_with_changes_async",
                new=AsyncMock(return_value={}),
            ),
        ):
            resp = client.get(f"/v1/wallets/{_APTOS_ADDR}/balances?chain=aptos")

        assert resp.status_code == 200
        body = resp.json()
        # amount=1.0, price=10.0 → usd_value=10.0
        assert body[0]["usd_value"] == pytest.approx(10.0)

    def test_empty_wallet_returns_empty_list(self, client):
        mock_adapter = MagicMock()
        mock_adapter.normalize_address.return_value = _APTOS_ADDR
        mock_adapter.get_token_balances.return_value = []

        with (
            patch("app.routers.balances.get_adapter_for_chain", return_value=mock_adapter),
            patch("app.routers.balances.cache.get", return_value=None),
        ):
            resp = client.get(f"/v1/wallets/{_APTOS_ADDR}/balances?chain=aptos")

        assert resp.status_code == 200
        assert resp.json() == []

    def test_unsupported_chain_returns_400(self, client):
        with patch(
            "app.routers.balances.get_adapter_for_chain",
            side_effect=ValueError("Unsupported chain: fakechain"),
        ):
            resp = client.get(f"/v1/wallets/{_EVM_ADDR}/balances?chain=fakechain")

        assert resp.status_code == 400
        assert "fakechain" in resp.json()["detail"].lower() or "unsupported" in resp.json()["detail"].lower()

    def test_cached_response_returned(self, client):
        cached_data = [{"symbol": "APT", "address": "0x1", "decimals": 8, "raw": "100000000",
                        "amount": 1.0, "usd_price": 7.5, "usd_value": 7.5, "change_24h": 1.0}]

        with patch("app.routers.balances.cache.get", return_value=cached_data):
            resp = client.get(f"/v1/wallets/{_APTOS_ADDR}/balances?chain=aptos")

        assert resp.status_code == 200

    def test_testnet_param_false_uses_mainnet(self, client):
        """Ensure testnet=false passes network='mainnet' to adapter factory."""
        captured = {}

        def capture_adapter(chain, network=None, **kwargs):
            captured["network"] = network
            mock = MagicMock()
            mock.normalize_address.return_value = _APTOS_ADDR
            mock.get_token_balances.return_value = []
            return mock

        with (
            patch("app.routers.balances.get_adapter_for_chain", side_effect=capture_adapter),
            patch("app.routers.balances.cache.get", return_value=None),
        ):
            client.get(f"/v1/wallets/{_APTOS_ADDR}/balances?chain=aptos&testnet=false")

        assert captured.get("network") == "mainnet"

    def test_testnet_param_true_uses_testnet(self, client):
        captured = {}

        def capture_adapter(chain, network=None, **kwargs):
            captured["network"] = network
            mock = MagicMock()
            mock.normalize_address.return_value = _APTOS_ADDR
            mock.get_token_balances.return_value = []
            return mock

        with (
            patch("app.routers.balances.get_adapter_for_chain", side_effect=capture_adapter),
            patch("app.routers.balances.cache.get", return_value=None),
        ):
            client.get(f"/v1/wallets/{_APTOS_ADDR}/balances?chain=aptos&testnet=true")

        assert captured.get("network") == "testnet"


# ---------------------------------------------------------------------------
# GET /v1/wallets/{address}/multi-chain-balances
# ---------------------------------------------------------------------------

class TestGetMultiChainBalances:
    def test_evm_address_returns_multi_chain_result(self, client):
        mock_adapter = MagicMock()
        mock_adapter.normalize_address.return_value = _EVM_ADDR
        mock_adapter.get_token_balances.return_value = []

        with (
            patch("app.routers.balances.detect_address_type"),
            patch(
                "app.routers.balances.get_chains_for_address",
                return_value=["ethereum_sepolia"],
            ),
            patch("app.routers.balances.cache.get", return_value=None),
            patch("app.routers.balances.cache.set"),
            patch("app.routers.balances.get_adapter_for_chain", return_value=mock_adapter),
            patch(
                "app.routers.balances.price_service.get_prices_async",
                new=AsyncMock(return_value={}),
            ),
            patch(
                "app.routers.balances.price_service.get_prices_with_changes_async",
                new=AsyncMock(return_value={}),
            ),
        ):
            resp = client.get(f"/v1/wallets/{_EVM_ADDR}/multi-chain-balances")

        assert resp.status_code == 200
        body = resp.json()
        assert "balances_by_chain" in body
        assert "total_usd_value" in body

    def test_unsupported_address_returns_400(self, client):
        with patch(
            "app.routers.balances.detect_address_type",
            side_effect=ValueError("Unrecognized address format"),
        ):
            resp = client.get("/v1/wallets/not_a_real_address/multi-chain-balances")

        assert resp.status_code == 400
