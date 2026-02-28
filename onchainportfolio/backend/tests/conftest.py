# backend/tests/conftest.py
"""
Pytest configuration and fixtures for backend tests.

This file ensures the app module is importable from tests.
"""
import sys
from pathlib import Path

# Add backend directory to Python path so 'app' module can be imported
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from unittest.mock import Mock, MagicMock


# ============================================================
# Common Fixtures
# ============================================================

@pytest.fixture
def mock_mongodb_collection():
    """Create a mock MongoDB collection."""
    collection = MagicMock()
    collection.find.return_value = []
    collection.find_one.return_value = None
    collection.insert_one.return_value = Mock(inserted_id="mock_id")
    collection.update_one.return_value = Mock(matched_count=1, modified_count=1)
    collection.delete_one.return_value = Mock(deleted_count=1)
    collection.count_documents.return_value = 0
    return collection


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client for API calls."""
    client = MagicMock()
    response = Mock()
    response.status_code = 200
    response.json.return_value = {}
    response.raise_for_status = Mock()
    client.get.return_value = response
    client.post.return_value = response
    return client


@pytest.fixture
def sample_wallet_address_aptos():
    """Sample Aptos wallet address."""
    return "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"


@pytest.fixture
def sample_wallet_address_solana():
    """Sample Solana wallet address."""
    return "11111111111111111111111111111111"


@pytest.fixture
def sample_wallet_address_ethereum():
    """Sample Ethereum wallet address."""
    return "0x742d35Cc6634C0532925a3b844Bc9e7595f7CDEF"
