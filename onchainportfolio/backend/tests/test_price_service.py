# backend/tests/test_price_service.py
"""
Unit tests for Price Service

Tests price fetching from CoinGecko, Jupiter, and DefiLlama APIs.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import httpx
import time

from app.services.price_service import PriceService, get_price_service


class TestPriceServiceInitialization:
    """Tests for price service initialization."""

    def test_init_default_ttl(self):
        """Test initialization with default TTL."""
        service = PriceService()
        assert service.ttl_seconds == 60

    def test_init_custom_ttl(self):
        """Test initialization with custom TTL."""
        service = PriceService(ttl_seconds=120)
        assert service.ttl_seconds == 120

    def test_init_api_urls(self):
        """Test API URLs are set correctly."""
        service = PriceService()
        assert "coingecko" in service.coingecko_base_url
        assert "jup.ag" in service.jupiter_base_url
        assert "llama.fi" in service.defillama_base_url

    def test_init_coingecko_mappings(self):
        """Test CoinGecko ID mappings are populated."""
        service = PriceService()
        assert service.coingecko_ids["ETH"] == "ethereum"
        assert service.coingecko_ids["SOL"] == "solana"
        assert service.coingecko_ids["APT"] == "aptos"
        assert service.coingecko_ids["USDC"] == "usd-coin"

    def test_init_solana_mints(self):
        """Test Solana mint addresses are populated."""
        service = PriceService()
        assert service.solana_mints["SOL"] == "So11111111111111111111111111111111111111112"
        assert service.solana_mints["USDC"] == "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


class TestCacheOperations:
    """Tests for cache operations."""

    def test_cache_set_and_get(self):
        """Test setting and getting from cache."""
        service = PriceService(ttl_seconds=60)
        service._set_cache("ETH", 3000.0)

        result = service._get_from_cache("ETH")
        assert result == 3000.0

    def test_cache_expired(self):
        """Test cache expiration."""
        service = PriceService(ttl_seconds=1)
        service._set_cache("ETH", 3000.0)

        # Wait for cache to expire
        time.sleep(1.1)

        result = service._get_from_cache("ETH")
        assert result is None

    def test_cache_clear(self):
        """Test clearing cache."""
        service = PriceService()
        service._set_cache("ETH", 3000.0)
        service._set_cache("SOL", 100.0)

        service.clear_cache()

        assert service._get_from_cache("ETH") is None
        assert service._get_from_cache("SOL") is None

    def test_cache_key_with_chain(self):
        """Test cache key includes chain when provided."""
        service = PriceService()
        service._set_cache("USDC:ethereum", 1.0)
        service._set_cache("USDC:solana", 1.0)

        assert service._get_from_cache("USDC:ethereum") == 1.0
        assert service._get_from_cache("USDC:solana") == 1.0
        assert service._get_from_cache("USDC") is None


class TestChainNormalization:
    """Tests for chain normalization."""

    def test_normalize_ethereum_sepolia(self):
        """Test testnet chain normalization."""
        service = PriceService()
        assert service._normalize_chain("ethereum_sepolia") == "ethereum"

    def test_normalize_polygon_amoy(self):
        """Test Polygon testnet normalization."""
        service = PriceService()
        assert service._normalize_chain("polygon_amoy") == "polygon"

    def test_normalize_base_sepolia(self):
        """Test Base testnet normalization."""
        service = PriceService()
        assert service._normalize_chain("base_sepolia") == "base"

    def test_normalize_mainnet_unchanged(self):
        """Test mainnet chains are unchanged."""
        service = PriceService()
        assert service._normalize_chain("ethereum") == "ethereum"
        assert service._normalize_chain("solana") == "solana"

    def test_normalize_uppercase(self):
        """Test uppercase chain names."""
        service = PriceService()
        assert service._normalize_chain("ETHEREUM") == "ethereum"


class TestCoinGeckoPriceFetching:
    """Tests for CoinGecko price fetching."""

    @pytest.fixture
    def service(self):
        """Create price service."""
        return PriceService()

    def test_get_price_coingecko_success(self, service):
        """Test successful price fetch from CoinGecko."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "ethereum": {"usd": 3000.0}
        }
        mock_response.raise_for_status = Mock()

        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            price = service._get_price_from_coingecko("ETH")

            assert price == 3000.0

    def test_get_price_coingecko_unknown_symbol(self, service):
        """Test price fetch for unknown symbol."""
        price = service._get_price_from_coingecko("UNKNOWNTOKEN123")
        assert price is None

    def test_get_price_coingecko_rate_limited(self, service):
        """Test handling rate limiting."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Rate limited",
            request=Mock(),
            response=mock_response
        )

        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            price = service._get_price_from_coingecko("ETH")
            assert price is None

    def test_get_prices_batch_coingecko_success(self, service):
        """Test batch price fetch from CoinGecko."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "ethereum": {"usd": 3000.0},
            "solana": {"usd": 100.0},
            "aptos": {"usd": 10.0}
        }
        mock_response.raise_for_status = Mock()

        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            prices = service._get_prices_batch_coingecko(["ETH", "SOL", "APT"])

            assert prices["ETH"] == 3000.0
            assert prices["SOL"] == 100.0
            assert prices["APT"] == 10.0

    def test_get_prices_batch_coingecko_partial(self, service):
        """Test batch price fetch with some missing."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "ethereum": {"usd": 3000.0}
            # solana is missing
        }
        mock_response.raise_for_status = Mock()

        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            prices = service._get_prices_batch_coingecko(["ETH", "SOL"])

            assert prices["ETH"] == 3000.0
            assert prices["SOL"] is None


class TestJupiterPriceFetching:
    """Tests for Jupiter (Solana) price fetching."""

    @pytest.fixture
    def service(self):
        """Create price service."""
        return PriceService()

    def test_get_price_jupiter_success(self, service):
        """Test successful price fetch from Jupiter."""
        sol_mint = "So11111111111111111111111111111111111111112"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                sol_mint: {"price": 100.0}
            }
        }
        mock_response.raise_for_status = Mock()

        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            price = service._get_price_from_jupiter("SOL")

            assert price == 100.0

    def test_get_price_jupiter_unknown_mint(self, service):
        """Test price fetch for unknown mint."""
        price = service._get_price_from_jupiter("UNKNOWNSOLTOKEN")
        assert price is None

    def test_get_price_jupiter_error(self, service):
        """Test handling Jupiter API error."""
        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = httpx.HTTPError("Failed")

            price = service._get_price_from_jupiter("SOL")
            assert price is None

    def test_get_prices_batch_jupiter_success(self, service):
        """Test batch price fetch from Jupiter."""
        sol_mint = "So11111111111111111111111111111111111111112"
        usdc_mint = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                sol_mint: {"price": 100.0},
                usdc_mint: {"price": 1.0}
            }
        }
        mock_response.raise_for_status = Mock()

        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            prices = service._get_prices_batch_jupiter(["SOL", "USDC"])

            assert prices["SOL"] == 100.0
            assert prices["USDC"] == 1.0


class TestDefiLlamaPriceFetching:
    """Tests for DefiLlama price fetching."""

    @pytest.fixture
    def service(self):
        """Create price service."""
        return PriceService()

    def test_get_price_defillama_success(self, service):
        """Test successful price fetch from DefiLlama."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "coins": {
                "ethereum:0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48": {"price": 1.0}
            }
        }
        mock_response.raise_for_status = Mock()

        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            price = service._get_price_from_defillama("USDC", "ethereum")

            assert price == 1.0

    def test_get_price_defillama_unknown_token(self, service):
        """Test price fetch for unknown token/chain combination."""
        price = service._get_price_from_defillama("UNKNOWN", "ethereum")
        assert price is None

    def test_get_price_defillama_unknown_chain(self, service):
        """Test price fetch for unknown chain."""
        price = service._get_price_from_defillama("USDC", "unknown_chain")
        assert price is None


class TestMainPriceInterface:
    """Tests for main get_price interface."""

    @pytest.fixture
    def service(self):
        """Create price service."""
        return PriceService()

    def test_get_price_from_cache(self, service):
        """Test that cached prices are returned."""
        service._set_cache("ETH", 3000.0)

        price = service.get_price("ETH")

        assert price == 3000.0

    def test_get_price_symbol_case_insensitive(self, service):
        """Test symbol is case insensitive."""
        service._set_cache("ETH", 3000.0)

        price = service.get_price("eth")

        assert price == 3000.0

    def test_get_price_solana_uses_jupiter(self, service):
        """Test Solana chain uses Jupiter API."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "So11111111111111111111111111111111111111112": {"price": 100.0}
            }
        }
        mock_response.raise_for_status = Mock()

        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            price = service.get_price("SOL", chain="solana")

            assert price == 100.0

    def test_get_price_with_testnet_chain(self, service):
        """Test that testnet chains are normalized to mainnet."""
        service._set_cache("ETH:ethereum", 3000.0)

        # Calling with testnet should find mainnet price
        price = service.get_price("ETH", chain="ethereum_sepolia")

        assert price == 3000.0

    def test_get_prices_multiple(self, service):
        """Test getting multiple prices at once."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "ethereum": {"usd": 3000.0},
            "aptos": {"usd": 10.0}
        }
        mock_response.raise_for_status = Mock()

        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            prices = service.get_prices(["ETH", "APT"])

            assert "ETH" in prices
            assert "APT" in prices

    def test_get_prices_with_cache(self, service):
        """Test batch prices uses cache."""
        service._set_cache("ETH", 3000.0)

        prices = service.get_prices(["ETH"])

        assert prices["ETH"] == 3000.0


class TestCustomMappings:
    """Tests for custom token mappings."""

    def test_add_coingecko_mapping(self):
        """Test adding custom CoinGecko mapping."""
        service = PriceService()
        service.add_coingecko_mapping("MYTOKEN", "my-token-id")

        assert service.coingecko_ids["MYTOKEN"] == "my-token-id"

    def test_add_solana_mint(self):
        """Test adding custom Solana mint."""
        service = PriceService()
        service.add_solana_mint("MYTOKEN", "MyMintAddress123")

        assert service.solana_mints["MYTOKEN"] == "MyMintAddress123"

    def test_add_mapping_uppercase(self):
        """Test mappings are stored uppercase."""
        service = PriceService()
        service.add_coingecko_mapping("mytoken", "my-token-id")

        assert service.coingecko_ids["MYTOKEN"] == "my-token-id"


class TestPriceServiceSingleton:
    """Tests for price service singleton."""

    def test_get_price_service_returns_same_instance(self):
        """Test that get_price_service returns singleton."""
        # Reset singleton
        import app.services.price_service as price_module
        price_module._price_service = None

        service1 = get_price_service()
        service2 = get_price_service()

        assert service1 is service2

    def test_backward_compatibility_instance(self):
        """Test backward compatibility price_service instance exists."""
        from app.services.price_service import price_service
        assert price_service is not None
        assert isinstance(price_service, PriceService)


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.fixture
    def service(self):
        """Create price service."""
        return PriceService()

    def test_coingecko_timeout(self, service):
        """Test handling CoinGecko timeout."""
        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = httpx.TimeoutException("Timeout")

            price = service._get_price_from_coingecko("ETH")
            assert price is None

    def test_jupiter_timeout(self, service):
        """Test handling Jupiter timeout."""
        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = httpx.TimeoutException("Timeout")

            price = service._get_price_from_jupiter("SOL")
            assert price is None

    def test_defillama_timeout(self, service):
        """Test handling DefiLlama timeout."""
        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = httpx.TimeoutException("Timeout")

            price = service._get_price_from_defillama("USDC", "ethereum")
            assert price is None

    def test_invalid_json_response(self, service):
        """Test handling invalid JSON response."""
        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = ValueError("Invalid JSON")

            price = service._get_price_from_coingecko("ETH")
            assert price is None
