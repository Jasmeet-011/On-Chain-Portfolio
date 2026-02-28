# backend/tests/test_aptos_adapter.py
"""
Unit tests for Aptos Adapter

Tests address validation, normalization, and balance fetching.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import httpx

from app.services.adapters.aptos_adapter import AptosAdapter


class TestAptosAddressValidation:
    """Tests for Aptos address validation."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with mocked client."""
        with patch.object(AptosAdapter, '__init__', lambda x, y: None):
            adapter = AptosAdapter.__new__(AptosAdapter)
            adapter.rpc_url = "https://fullnode.testnet.aptoslabs.com/v1"
            adapter.chain_name = "aptos"
            adapter._client = Mock()
            return adapter

    def test_valid_address_full_length(self, adapter):
        """Test valid 64-character hex address."""
        address = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        is_valid, error = adapter.validate_address(address)
        assert is_valid is True
        assert error is None

    def test_valid_address_short(self, adapter):
        """Test valid short address (e.g., 0x1)."""
        address = "0x1"
        is_valid, error = adapter.validate_address(address)
        assert is_valid is True
        assert error is None

    def test_valid_address_uppercase(self, adapter):
        """Test valid address with uppercase hex."""
        address = "0xABCDEF1234567890ABCDEF1234567890ABCDEF1234567890ABCDEF1234567890"
        is_valid, error = adapter.validate_address(address)
        assert is_valid is True
        assert error is None

    def test_invalid_address_empty(self, adapter):
        """Test empty address."""
        is_valid, error = adapter.validate_address("")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_invalid_address_no_prefix(self, adapter):
        """Test address without 0x prefix."""
        address = "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        is_valid, error = adapter.validate_address(address)
        assert is_valid is False
        assert "0x" in error

    def test_invalid_address_too_long(self, adapter):
        """Test address longer than 64 hex characters."""
        address = "0x" + "a" * 65
        is_valid, error = adapter.validate_address(address)
        assert is_valid is False
        assert "64" in error

    def test_invalid_address_non_hex(self, adapter):
        """Test address with non-hex characters."""
        address = "0x1234567890ghijkl"
        is_valid, error = adapter.validate_address(address)
        assert is_valid is False
        assert "hexadecimal" in error.lower()

    def test_invalid_address_only_prefix(self, adapter):
        """Test address with only 0x prefix."""
        address = "0x"
        is_valid, error = adapter.validate_address(address)
        assert is_valid is False
        assert "at least one character" in error.lower()


class TestAptosAddressNormalization:
    """Tests for Aptos address normalization."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with mocked client."""
        with patch.object(AptosAdapter, '__init__', lambda x, y: None):
            adapter = AptosAdapter.__new__(AptosAdapter)
            adapter.rpc_url = "https://fullnode.testnet.aptoslabs.com/v1"
            adapter.chain_name = "aptos"
            return adapter

    def test_normalize_lowercase(self, adapter):
        """Test normalization to lowercase."""
        address = "0xABCDEF"
        normalized = adapter.normalize_address(address)
        assert normalized == "0xabcdef"

    def test_normalize_add_prefix(self, adapter):
        """Test adding 0x prefix."""
        address = "abcdef"
        normalized = adapter.normalize_address(address)
        assert normalized == "0xabcdef"

    def test_normalize_trim_whitespace(self, adapter):
        """Test trimming whitespace."""
        address = "  0xabcdef  "
        normalized = adapter.normalize_address(address)
        assert normalized == "0xabcdef"


class TestAptosBalanceFetching:
    """Tests for Aptos balance fetching."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with mocked HTTP client."""
        with patch.object(AptosAdapter, '__init__', lambda x, y: None):
            adapter = AptosAdapter.__new__(AptosAdapter)
            adapter.rpc_url = "https://fullnode.testnet.aptoslabs.com/v1"
            adapter.chain_name = "aptos"
            adapter._client = Mock()
            adapter.TOKEN_REGISTRY = {
                "0x1::aptos_coin::AptosCoin": ("APT", 8),
            }
            return adapter

    def test_get_balance_success(self, adapter):
        """Test successful balance fetch."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"balance": "100000000"}
        mock_response.raise_for_status = Mock()
        adapter._client.get.return_value = mock_response

        balance = adapter.get_balance("0x1")
        assert balance == 100000000

    def test_get_balance_not_found(self, adapter):
        """Test balance fetch for non-existent account."""
        mock_response = Mock()
        mock_response.status_code = 404
        adapter._client.get.return_value = mock_response

        balance = adapter.get_balance("0x1")
        assert balance is None

    def test_get_balance_http_error(self, adapter):
        """Test balance fetch with HTTP error."""
        adapter._client.get.side_effect = httpx.HTTPError("Connection failed")

        balance = adapter.get_balance("0x1")
        assert balance is None

    def test_get_native_balance_success(self, adapter):
        """Test successful native balance fetch."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"balance": "100000000"}
        mock_response.raise_for_status = Mock()
        adapter._client.get.return_value = mock_response

        result = adapter.get_native_balance("0x1")

        assert result is not None
        assert result["symbol"] == "APT"
        assert result["amount"] == 1.0
        assert result["decimals"] == 8
        assert result["chain"] == "aptos"

    def test_get_native_balance_none(self, adapter):
        """Test native balance when account doesn't exist."""
        mock_response = Mock()
        mock_response.status_code = 404
        adapter._client.get.return_value = mock_response

        result = adapter.get_native_balance("0x1")
        assert result is None


class TestAptosTokenBalances:
    """Tests for Aptos token balance fetching."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with mocked HTTP client."""
        with patch.object(AptosAdapter, '__init__', lambda x, y: None):
            adapter = AptosAdapter.__new__(AptosAdapter)
            adapter.rpc_url = "https://fullnode.testnet.aptoslabs.com/v1"
            adapter.chain_name = "aptos"
            adapter._client = Mock()
            adapter.TOKEN_REGISTRY = {
                "0x1::aptos_coin::AptosCoin": ("APT", 8),
            }
            return adapter

    def test_get_token_balances_with_balance(self, adapter):
        """Test getting token balances when tokens exist."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"balance": "500000000"}
        mock_response.raise_for_status = Mock()
        adapter._client.get.return_value = mock_response

        balances = adapter.get_token_balances("0x1")

        assert len(balances) == 1
        assert balances[0]["symbol"] == "APT"
        assert balances[0]["amount"] == 5.0

    def test_get_token_balances_zero_balance(self, adapter):
        """Test getting token balances when balance is zero."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"balance": "0"}
        mock_response.raise_for_status = Mock()
        adapter._client.get.return_value = mock_response

        balances = adapter.get_token_balances("0x1")
        assert len(balances) == 0

    def test_get_token_balances_error_continues(self, adapter):
        """Test that errors for one token don't stop others."""
        adapter._client.get.side_effect = httpx.HTTPError("Failed")

        balances = adapter.get_token_balances("0x1")
        assert balances == []


class TestAptosTransactions:
    """Tests for Aptos transaction fetching."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with mocked HTTP client."""
        with patch.object(AptosAdapter, '__init__', lambda x, y: None):
            adapter = AptosAdapter.__new__(AptosAdapter)
            adapter.rpc_url = "https://fullnode.testnet.aptoslabs.com/v1"
            adapter.chain_name = "aptos"
            adapter._client = Mock()
            return adapter

    def test_get_transactions_success(self, adapter):
        """Test successful transaction fetch."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"type": "user_transaction", "hash": "0x123"},
            {"type": "block_metadata_transaction", "hash": "0x456"},
            {"type": "user_transaction", "hash": "0x789"},
        ]
        mock_response.raise_for_status = Mock()
        adapter._client.get.return_value = mock_response

        transactions = adapter.get_transactions("0x1", limit=10)

        # Should only return user transactions
        assert len(transactions) == 2
        assert transactions[0]["hash"] == "0x123"
        assert transactions[1]["hash"] == "0x789"

    def test_get_transactions_not_found(self, adapter):
        """Test transaction fetch for non-existent account."""
        mock_response = Mock()
        mock_response.status_code = 404
        adapter._client.get.return_value = mock_response

        transactions = adapter.get_transactions("0x1")
        assert transactions == []

    def test_get_transactions_error(self, adapter):
        """Test transaction fetch with error."""
        adapter._client.get.side_effect = httpx.HTTPError("Failed")

        transactions = adapter.get_transactions("0x1")
        assert transactions == []


class TestAptosPortfolio:
    """Tests for Aptos portfolio fetching."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with mocked HTTP client."""
        with patch.object(AptosAdapter, '__init__', lambda x, y: None):
            adapter = AptosAdapter.__new__(AptosAdapter)
            adapter.rpc_url = "https://fullnode.testnet.aptoslabs.com/v1"
            adapter.chain_name = "aptos"
            adapter._client = Mock()
            adapter.TOKEN_REGISTRY = {
                "0x1::aptos_coin::AptosCoin": ("APT", 8),
            }
            return adapter

    def test_get_portfolio_success(self, adapter):
        """Test successful portfolio fetch."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"balance": "100000000"}
        mock_response.raise_for_status = Mock()
        adapter._client.get.return_value = mock_response

        portfolio = adapter.get_portfolio("0x1")

        assert portfolio["chain"] == "aptos"
        assert portfolio["address"] == "0x1"
        assert "balances" in portfolio
        assert portfolio["native_balance"] is not None
        assert portfolio["native_balance"]["symbol"] == "APT"
