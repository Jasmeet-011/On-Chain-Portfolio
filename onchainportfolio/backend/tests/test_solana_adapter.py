# backend/tests/test_solana_adapter.py
"""
Unit tests for Solana Adapter

Tests address validation, normalization, and balance fetching.
"""
import pytest
from unittest.mock import Mock, patch
import httpx

from app.services.adapters.solana_adapter import SolanaAdapter


class TestSolanaAddressValidation:
    """Tests for Solana address validation."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with mocked client."""
        with patch.object(SolanaAdapter, '__init__', lambda x, y, **kwargs: None):
            adapter = SolanaAdapter.__new__(SolanaAdapter)
            adapter.rpc_url = "https://api.testnet.solana.com"
            adapter.backup_rpc_url = None
            adapter.chain_name = "solana"
            adapter._client = Mock()
            return adapter

    def test_valid_address_standard(self, adapter):
        """Test valid Solana address (base58, 44 chars)."""
        # Valid Solana address (System Program)
        address = "11111111111111111111111111111111"
        is_valid, error = adapter.validate_address(address)
        assert is_valid is True
        assert error is None

    def test_valid_address_wallet(self, adapter):
        """Test valid wallet address."""
        # Valid looking Solana address
        address = "So11111111111111111111111111111111111111112"
        is_valid, error = adapter.validate_address(address)
        assert is_valid is True
        assert error is None

    def test_invalid_address_empty(self, adapter):
        """Test empty address."""
        is_valid, error = adapter.validate_address("")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_invalid_address_too_short(self, adapter):
        """Test address shorter than 32 characters."""
        address = "abc123"
        is_valid, error = adapter.validate_address(address)
        assert is_valid is False
        assert "32-44" in error

    def test_invalid_address_too_long(self, adapter):
        """Test address longer than 44 characters."""
        address = "a" * 50
        is_valid, error = adapter.validate_address(address)
        assert is_valid is False
        assert "32-44" in error

    def test_invalid_address_bad_base58(self, adapter):
        """Test address with invalid base58 characters."""
        # 0, O, I, l are not valid in base58
        address = "0OIl" + "1" * 40
        is_valid, error = adapter.validate_address(address)
        assert is_valid is False
        assert "base58" in error.lower()


class TestSolanaAddressNormalization:
    """Tests for Solana address normalization."""

    @pytest.fixture
    def adapter(self):
        """Create adapter."""
        with patch.object(SolanaAdapter, '__init__', lambda x, y, **kwargs: None):
            adapter = SolanaAdapter.__new__(SolanaAdapter)
            adapter.rpc_url = "https://api.testnet.solana.com"
            return adapter

    def test_normalize_trim_whitespace(self, adapter):
        """Test trimming whitespace."""
        address = "  11111111111111111111111111111111  "
        normalized = adapter.normalize_address(address)
        assert normalized == "11111111111111111111111111111111"

    def test_normalize_preserves_case(self, adapter):
        """Test that case is preserved (base58 is case-sensitive)."""
        address = "So11111111111111111111111111111111111111112"
        normalized = adapter.normalize_address(address)
        assert normalized == address


class TestSolanaRPCCalls:
    """Tests for Solana RPC call handling."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with mocked HTTP client."""
        with patch.object(SolanaAdapter, '__init__', lambda x, y, **kwargs: None):
            adapter = SolanaAdapter.__new__(SolanaAdapter)
            adapter.rpc_url = "https://api.testnet.solana.com"
            adapter.backup_rpc_url = None
            adapter.chain_name = "solana"
            adapter._client = Mock()
            return adapter

    def test_rpc_call_success(self, adapter):
        """Test successful RPC call."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "result": {"value": 1000000000},
            "id": 1
        }
        mock_response.raise_for_status = Mock()
        adapter._client.post.return_value = mock_response

        result = adapter._rpc_call("getBalance", ["address"])
        assert result == {"value": 1000000000}

    def test_rpc_call_with_error_response(self, adapter):
        """Test RPC call that returns an error."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "error": {"code": -32600, "message": "Invalid Request"},
            "id": 1
        }
        mock_response.raise_for_status = Mock()
        adapter._client.post.return_value = mock_response

        with pytest.raises(Exception) as exc_info:
            adapter._rpc_call("getBalance", ["address"])
        assert "RPC error" in str(exc_info.value)

    def test_rpc_call_with_backup(self, adapter):
        """Test RPC call falls back to backup."""
        adapter.backup_rpc_url = "https://backup.solana.com"

        # Primary fails
        adapter._client.post.side_effect = [
            httpx.HTTPError("Primary failed"),
            Mock(
                status_code=200,
                json=Mock(return_value={"jsonrpc": "2.0", "result": {"value": 500}, "id": 1}),
                raise_for_status=Mock()
            )
        ]

        result = adapter._rpc_call("getBalance", ["address"])
        assert result == {"value": 500}


class TestSolanaBalanceFetching:
    """Tests for Solana balance fetching."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with mocked HTTP client."""
        with patch.object(SolanaAdapter, '__init__', lambda x, y, **kwargs: None):
            adapter = SolanaAdapter.__new__(SolanaAdapter)
            adapter.rpc_url = "https://api.testnet.solana.com"
            adapter.backup_rpc_url = None
            adapter.chain_name = "solana"
            adapter._client = Mock()
            adapter.KNOWN_TOKENS = {
                "So11111111111111111111111111111111111111112": {
                    "symbol": "SOL",
                    "decimals": 9,
                    "name": "Solana"
                }
            }
            return adapter

    def test_get_balance_success(self, adapter):
        """Test successful SOL balance fetch."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "result": {"value": 1000000000},
            "id": 1
        }
        mock_response.raise_for_status = Mock()
        adapter._client.post.return_value = mock_response

        balance = adapter.get_balance("11111111111111111111111111111111")
        assert balance == 1000000000

    def test_get_balance_error(self, adapter):
        """Test balance fetch with error."""
        adapter._client.post.side_effect = RuntimeError("RPC failed")

        balance = adapter.get_balance("11111111111111111111111111111111")
        assert balance is None

    def test_get_native_balance_success(self, adapter):
        """Test successful native balance fetch."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "result": {"value": 1000000000},
            "id": 1
        }
        mock_response.raise_for_status = Mock()
        adapter._client.post.return_value = mock_response

        result = adapter.get_native_balance("11111111111111111111111111111111")

        assert result is not None
        assert result["symbol"] == "SOL"
        assert result["amount"] == 1.0
        assert result["decimals"] == 9
        assert result["chain"] == "solana"


class TestSolanaTokenBalances:
    """Tests for Solana SPL token balance fetching."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with mocked HTTP client."""
        with patch.object(SolanaAdapter, '__init__', lambda x, y, **kwargs: None):
            adapter = SolanaAdapter.__new__(SolanaAdapter)
            adapter.rpc_url = "https://api.testnet.solana.com"
            adapter.backup_rpc_url = None
            adapter.chain_name = "solana"
            adapter._client = Mock()
            adapter.KNOWN_TOKENS = {
                "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": {
                    "symbol": "USDC",
                    "decimals": 6,
                    "name": "USD Coin"
                }
            }
            return adapter

    def test_get_token_balances_with_sol_and_spl(self, adapter):
        """Test getting both SOL and SPL token balances."""
        # Mock getBalance for SOL
        sol_response = Mock()
        sol_response.status_code = 200
        sol_response.json.return_value = {
            "jsonrpc": "2.0",
            "result": {"value": 2000000000},  # 2 SOL
            "id": 1
        }
        sol_response.raise_for_status = Mock()

        # Mock getTokenAccountsByOwner for SPL tokens
        token_response = Mock()
        token_response.status_code = 200
        token_response.json.return_value = {
            "jsonrpc": "2.0",
            "result": {
                "value": [
                    {
                        "account": {
                            "data": {
                                "parsed": {
                                    "info": {
                                        "mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                                        "tokenAmount": {
                                            "amount": "1000000",
                                            "decimals": 6,
                                            "uiAmount": 1.0
                                        }
                                    }
                                }
                            }
                        }
                    }
                ]
            },
            "id": 1
        }
        token_response.raise_for_status = Mock()

        adapter._client.post.side_effect = [sol_response, token_response]

        balances = adapter.get_token_balances("11111111111111111111111111111111")

        assert len(balances) == 2
        # First should be SOL (native)
        sol_balance = next((b for b in balances if b["symbol"] == "SOL"), None)
        assert sol_balance is not None
        assert sol_balance["amount"] == 2.0
        assert sol_balance["is_native"] is True

        # Second should be USDC
        usdc_balance = next((b for b in balances if b["symbol"] == "USDC"), None)
        assert usdc_balance is not None
        assert usdc_balance["amount"] == 1.0

    def test_get_token_balances_zero_sol(self, adapter):
        """Test when SOL balance is zero."""
        sol_response = Mock()
        sol_response.status_code = 200
        sol_response.json.return_value = {
            "jsonrpc": "2.0",
            "result": {"value": 0},
            "id": 1
        }
        sol_response.raise_for_status = Mock()

        token_response = Mock()
        token_response.status_code = 200
        token_response.json.return_value = {
            "jsonrpc": "2.0",
            "result": {"value": []},
            "id": 1
        }
        token_response.raise_for_status = Mock()

        adapter._client.post.side_effect = [sol_response, token_response]

        balances = adapter.get_token_balances("11111111111111111111111111111111")
        assert len(balances) == 0


class TestSolanaTransactions:
    """Tests for Solana transaction fetching."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with mocked HTTP client."""
        with patch.object(SolanaAdapter, '__init__', lambda x, y, **kwargs: None):
            adapter = SolanaAdapter.__new__(SolanaAdapter)
            adapter.rpc_url = "https://api.testnet.solana.com"
            adapter.backup_rpc_url = None
            adapter.chain_name = "solana"
            adapter._client = Mock()
            return adapter

    def test_get_transactions_success(self, adapter):
        """Test successful transaction fetch."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "result": [
                {"signature": "sig1", "slot": 100, "err": None, "blockTime": 1234567890},
                {"signature": "sig2", "slot": 101, "err": None, "blockTime": 1234567891},
            ],
            "id": 1
        }
        mock_response.raise_for_status = Mock()
        adapter._client.post.return_value = mock_response

        transactions = adapter.get_transactions("11111111111111111111111111111111", limit=10)

        assert len(transactions) == 2
        assert transactions[0]["signature"] == "sig1"
        assert transactions[1]["signature"] == "sig2"

    def test_get_transactions_error(self, adapter):
        """Test transaction fetch with error."""
        adapter._client.post.side_effect = RuntimeError("RPC failed")

        transactions = adapter.get_transactions("11111111111111111111111111111111")
        assert transactions == []


class TestSolanaPortfolio:
    """Tests for Solana portfolio fetching."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with mocked HTTP client."""
        with patch.object(SolanaAdapter, '__init__', lambda x, y, **kwargs: None):
            adapter = SolanaAdapter.__new__(SolanaAdapter)
            adapter.rpc_url = "https://api.testnet.solana.com"
            adapter.backup_rpc_url = None
            adapter.chain_name = "solana"
            adapter._client = Mock()
            adapter.KNOWN_TOKENS = {}
            return adapter

    def test_get_portfolio_success(self, adapter):
        """Test successful portfolio fetch."""
        sol_response = Mock()
        sol_response.status_code = 200
        sol_response.json.return_value = {
            "jsonrpc": "2.0",
            "result": {"value": 5000000000},  # 5 SOL
            "id": 1
        }
        sol_response.raise_for_status = Mock()

        token_response = Mock()
        token_response.status_code = 200
        token_response.json.return_value = {
            "jsonrpc": "2.0",
            "result": {"value": []},
            "id": 1
        }
        token_response.raise_for_status = Mock()

        adapter._client.post.side_effect = [sol_response, token_response]

        portfolio = adapter.get_portfolio("11111111111111111111111111111111")

        assert portfolio["chain"] == "solana"
        assert "balances" in portfolio
        assert portfolio["native_balance"] is not None
        assert portfolio["native_balance"]["symbol"] == "SOL"
        assert portfolio["native_balance"]["amount"] == 5.0
