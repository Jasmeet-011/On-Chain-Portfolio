# backend/tests/test_nft_service.py
"""
Unit tests for NFT Service

Tests NFT fetching from Solana (Helius) and Aptos (Indexer).
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import httpx

from app.services.nft_service import NFTService, get_nft_service
from app.models.nft_models import NFT, NFTResponse


class TestNFTServiceInitialization:
    """Tests for NFT service initialization."""

    def test_init_with_helius_key(self):
        """Test initialization with Helius API key."""
        with patch.dict('os.environ', {'HELIUS_API_KEY': 'test-key', 'SIMPLEHASH_API_KEY': ''}):
            service = NFTService()
            assert service.helius_api_key == 'test-key'
            assert service.helius_rpc_url is not None

    def test_init_without_helius_key(self):
        """Test initialization without Helius API key."""
        with patch.dict('os.environ', {'HELIUS_API_KEY': '', 'SIMPLEHASH_API_KEY': ''}):
            service = NFTService()
            assert service.helius_api_key == ''
            assert service.helius_rpc_url is None

    def test_init_with_simplehash_key(self):
        """Test initialization with SimpleHash API key."""
        with patch.dict('os.environ', {'HELIUS_API_KEY': '', 'SIMPLEHASH_API_KEY': 'simple-key'}):
            service = NFTService()
            assert service.simplehash_api_key == 'simple-key'


class TestSolanaNFTFetching:
    """Tests for Solana NFT fetching via Helius."""

    @pytest.fixture
    def service(self):
        """Create NFT service with mocked environment."""
        with patch.dict('os.environ', {'HELIUS_API_KEY': 'test-key', 'SIMPLEHASH_API_KEY': ''}):
            return NFTService()

    def test_get_solana_nfts_helius_success(self, service):
        """Test successful NFT fetch from Helius."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {
                "total": 2,
                "items": [
                    {
                        "id": "nft1",
                        "interface": "ProgrammableNFT",
                        "content": {
                            "metadata": {"name": "Cool NFT #1"},
                            "links": {"image": "https://example.com/nft1.png"}
                        },
                        "grouping": [
                            {"group_key": "collection", "group_value": "cool-collection"}
                        ]
                    },
                    {
                        "id": "nft2",
                        "interface": "ProgrammableNFT",
                        "content": {
                            "metadata": {"name": "Cool NFT #2"},
                            "links": {"image": "https://example.com/nft2.png"}
                        },
                        "grouping": [
                            {"group_key": "collection", "group_value": "cool-collection"}
                        ]
                    }
                ]
            }
        }

        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.post.return_value = mock_response

            nfts = service.get_solana_nfts_helius("wallet123")

            assert len(nfts) == 2
            assert nfts[0].name == "Cool NFT #1"
            assert nfts[0].collection == "cool-collection"
            assert nfts[0].chain == "solana"

    def test_get_solana_nfts_helius_skips_fungible(self, service):
        """Test that fungible tokens are skipped."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {
                "total": 2,
                "items": [
                    {
                        "id": "token1",
                        "interface": "FungibleToken",  # Should be skipped
                        "content": {"metadata": {"name": "USDC"}}
                    },
                    {
                        "id": "nft1",
                        "interface": "ProgrammableNFT",
                        "content": {
                            "metadata": {"name": "Real NFT"},
                            "links": {"image": "https://example.com/nft.png"}
                        },
                        "grouping": []
                    }
                ]
            }
        }

        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.post.return_value = mock_response

            nfts = service.get_solana_nfts_helius("wallet123")

            assert len(nfts) == 1
            assert nfts[0].name == "Real NFT"

    def test_get_solana_nfts_helius_error_fallback(self, service):
        """Test fallback to SimpleHash on Helius error."""
        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.post.side_effect = httpx.HTTPError("Failed")

            with patch.object(service, 'get_solana_nfts_simplehash', return_value=[]) as mock_fallback:
                nfts = service.get_solana_nfts_helius("wallet123")
                mock_fallback.assert_called_once_with("wallet123")

    def test_get_solana_nfts_helius_timeout_fallback(self, service):
        """Test fallback to SimpleHash on timeout."""
        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.post.side_effect = httpx.TimeoutException("Timeout")

            with patch.object(service, 'get_solana_nfts_simplehash', return_value=[]) as mock_fallback:
                nfts = service.get_solana_nfts_helius("wallet123")
                mock_fallback.assert_called_once_with("wallet123")

    def test_get_solana_nfts_no_api_key(self):
        """Test fallback when no Helius key."""
        with patch.dict('os.environ', {'HELIUS_API_KEY': '', 'SIMPLEHASH_API_KEY': ''}):
            service = NFTService()

            with patch.object(service, 'get_solana_nfts_simplehash', return_value=[]) as mock_fallback:
                nfts = service.get_solana_nfts_helius("wallet123")
                mock_fallback.assert_called_once()


class TestSimpleHashNFTFetching:
    """Tests for SimpleHash fallback NFT fetching."""

    @pytest.fixture
    def service(self):
        """Create NFT service with SimpleHash key."""
        with patch.dict('os.environ', {'HELIUS_API_KEY': '', 'SIMPLEHASH_API_KEY': 'simple-key'}):
            return NFTService()

    def test_get_solana_nfts_simplehash_success(self, service):
        """Test successful NFT fetch from SimpleHash."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "nfts": [
                {
                    "name": "SimpleHash NFT",
                    "collection": {"name": "Simple Collection"},
                    "nft_id": "simple1",
                    "previews": {"image_medium_url": "https://example.com/simple.png"}
                }
            ]
        }

        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            nfts = service.get_solana_nfts_simplehash("wallet123")

            assert len(nfts) == 1
            assert nfts[0].name == "SimpleHash NFT"
            assert nfts[0].collection == "Simple Collection"

    def test_get_solana_nfts_simplehash_no_key(self):
        """Test returns empty when no SimpleHash key."""
        with patch.dict('os.environ', {'HELIUS_API_KEY': '', 'SIMPLEHASH_API_KEY': ''}):
            service = NFTService()
            nfts = service.get_solana_nfts_simplehash("wallet123")
            assert nfts == []

    def test_get_solana_nfts_simplehash_error(self, service):
        """Test returns empty on SimpleHash error."""
        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = httpx.HTTPError("Failed")

            nfts = service.get_solana_nfts_simplehash("wallet123")
            assert nfts == []


class TestAptosNFTFetching:
    """Tests for Aptos NFT fetching via Indexer."""

    @pytest.fixture
    def service(self):
        """Create NFT service."""
        with patch.dict('os.environ', {'HELIUS_API_KEY': '', 'SIMPLEHASH_API_KEY': ''}):
            return NFTService()

    def test_get_aptos_nfts_success(self, service):
        """Test successful Aptos NFT fetch."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "current_token_ownerships_v2": [
                    {
                        "token_data_id": "aptos-nft-1",
                        "current_token_data": {
                            "token_name": "Aptos NFT #1",
                            "token_uri": "https://example.com/aptos1.png",
                            "current_collection": {
                                "collection_name": "Aptos Collection"
                            }
                        }
                    }
                ]
            }
        }

        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.post.return_value = mock_response

            nfts = service.get_aptos_nfts("0x123")

            assert len(nfts) == 1
            assert nfts[0].name == "Aptos NFT #1"
            assert nfts[0].collection == "Aptos Collection"
            assert nfts[0].chain == "aptos"

    def test_get_aptos_nfts_graphql_error(self, service):
        """Test handling GraphQL errors."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "errors": [{"message": "Invalid query"}]
        }

        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.post.return_value = mock_response

            nfts = service.get_aptos_nfts("0x123")
            assert nfts == []

    def test_get_aptos_nfts_http_error(self, service):
        """Test handling HTTP errors."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.post.return_value = mock_response

            nfts = service.get_aptos_nfts("0x123")
            assert nfts == []

    def test_get_aptos_nfts_timeout(self, service):
        """Test handling timeout."""
        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.post.side_effect = httpx.TimeoutException("Timeout")

            nfts = service.get_aptos_nfts("0x123")
            assert nfts == []


class TestNFTServiceMainInterface:
    """Tests for main NFT service interface."""

    @pytest.fixture
    def service(self):
        """Create NFT service."""
        with patch.dict('os.environ', {'HELIUS_API_KEY': 'test', 'SIMPLEHASH_API_KEY': ''}):
            return NFTService()

    def test_get_nfts_for_wallet_solana(self, service):
        """Test getting NFTs for Solana wallet."""
        mock_nfts = [
            NFT(name="NFT1", collection="Col1", image_url="url1", token_id="1", chain="solana"),
            NFT(name="NFT2", collection="Col1", image_url="url2", token_id="2", chain="solana"),
            NFT(name="NFT3", collection="Col2", image_url="url3", token_id="3", chain="solana"),
        ]

        with patch.object(service, 'get_solana_nfts', return_value=mock_nfts):
            response = service.get_nfts_for_wallet("wallet123", "solana")

            assert response.total_nfts == 3
            assert len(response.collections) == 2
            assert response.chain == "solana"

    def test_get_nfts_for_wallet_aptos(self, service):
        """Test getting NFTs for Aptos wallet."""
        mock_nfts = [
            NFT(name="Aptos NFT", collection="Aptos Col", image_url="url", token_id="1", chain="aptos"),
        ]

        with patch.object(service, 'get_aptos_nfts', return_value=mock_nfts):
            response = service.get_nfts_for_wallet("0x123", "aptos")

            assert response.total_nfts == 1
            assert response.chain == "aptos"

    def test_get_nfts_for_wallet_unknown_chain(self, service):
        """Test getting NFTs for unknown chain."""
        response = service.get_nfts_for_wallet("wallet", "unknown")
        assert response.total_nfts == 0
        assert response.nfts == []


class TestNFTAggregation:
    """Tests for NFT aggregation across wallets."""

    @pytest.fixture
    def service(self):
        """Create NFT service."""
        with patch.dict('os.environ', {'HELIUS_API_KEY': '', 'SIMPLEHASH_API_KEY': ''}):
            return NFTService()

    def test_aggregate_nfts_multiple_wallets(self, service):
        """Test aggregating NFTs from multiple wallets."""
        wallet1_response = NFTResponse(
            wallet_address="wallet1",
            chain="solana",
            nfts=[
                NFT(name="NFT1", collection="Col1", image_url="url1", token_id="1", chain="solana"),
                NFT(name="NFT2", collection="Col1", image_url="url2", token_id="2", chain="solana"),
            ],
            total_nfts=2,
            collections=[]
        )

        wallet2_response = NFTResponse(
            wallet_address="wallet2",
            chain="aptos",
            nfts=[
                NFT(name="NFT3", collection="Col2", image_url="url3", token_id="3", chain="aptos"),
            ],
            total_nfts=1,
            collections=[]
        )

        aggregated = service.aggregate_nfts([wallet1_response, wallet2_response])

        assert aggregated["total_nfts"] == 3
        assert aggregated["total_collections"] == 2
        assert aggregated["by_chain"]["solana"] == 2
        assert aggregated["by_chain"]["aptos"] == 1

    def test_aggregate_nfts_empty(self, service):
        """Test aggregating empty NFT list."""
        aggregated = service.aggregate_nfts([])

        assert aggregated["total_nfts"] == 0
        assert aggregated["total_collections"] == 0
        assert aggregated["by_chain"] == {}


class TestNFTServiceSingleton:
    """Tests for NFT service singleton."""

    def test_get_nft_service_returns_same_instance(self):
        """Test that get_nft_service returns singleton."""
        with patch.dict('os.environ', {'HELIUS_API_KEY': '', 'SIMPLEHASH_API_KEY': ''}):
            # Reset singleton
            import app.services.nft_service as nft_module
            nft_module._nft_service = None

            service1 = get_nft_service()
            service2 = get_nft_service()

            assert service1 is service2
