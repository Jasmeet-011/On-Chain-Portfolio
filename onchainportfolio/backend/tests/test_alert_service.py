# backend/tests/test_alert_service.py
"""
Unit tests for Alert Service

Tests the 3-tier alert system: portfolio, token, and wallet alerts.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
from bson import ObjectId

from app.services.alert_service import AlertService
from app.models.alert_models import AlertResponse


class TestAlertServiceInitialization:
    """Tests for alert service initialization."""

    def test_init_with_collections(self):
        """Test initialization with MongoDB collections."""
        alerts_col = Mock()
        prefs_col = Mock()
        wallets_col = Mock()
        price_svc = Mock()
        email_svc = Mock()

        service = AlertService(
            alerts_col, prefs_col, wallets_col, price_svc, email_svc
        )

        assert service.alerts is alerts_col
        assert service.preferences is prefs_col
        assert service.wallets is wallets_col
        assert service.price_service is price_svc
        assert service.email_service is email_svc


class TestAlertCRUDOperations:
    """Tests for alert CRUD operations."""

    @pytest.fixture
    def service(self):
        """Create alert service with mocked dependencies."""
        alerts_col = Mock()
        prefs_col = Mock()
        wallets_col = Mock()
        price_svc = Mock()
        email_svc = Mock()

        return AlertService(
            alerts_col, prefs_col, wallets_col, price_svc, email_svc
        )

    def test_create_token_alert(self, service):
        """Test creating a token alert."""
        mock_id = ObjectId()
        service.alerts.insert_one.return_value = Mock(inserted_id=mock_id)
        service.alerts.find_one.return_value = {
            "_id": mock_id,
            "user_id": "user123",
            "alert_type": "token",
            "token_symbol": "ETH",
            "target_price": 3000.0,
            "condition": "above",
            "chain": "ethereum",
            "is_active": True,
            "is_recurring": False,
            "status": "active",
            "trigger_count": 0,
            "created_at": datetime.utcnow(),
        }

        alert_data = {
            "alert_type": "token",
            "token_symbol": "ETH",
            "target_price": 3000.0,
            "condition": "above",
            "chain": "ethereum"
        }

        result = service.create_alert("user123", "user@test.com", alert_data)

        assert result is not None
        assert result.token_symbol == "ETH"
        assert result.target_price == 3000.0
        service.alerts.insert_one.assert_called_once()

    def test_create_portfolio_alert(self, service):
        """Test creating a portfolio alert."""
        mock_id = ObjectId()
        service.alerts.insert_one.return_value = Mock(inserted_id=mock_id)
        service.alerts.find_one.return_value = {
            "_id": mock_id,
            "user_id": "user123",
            "alert_type": "portfolio",
            "portfolio_metric": "value",
            "target_value": 10000.0,
            "condition": "above",
            "is_active": True,
            "is_recurring": False,
            "status": "active",
            "trigger_count": 0,
            "created_at": datetime.utcnow(),
        }

        alert_data = {
            "alert_type": "portfolio",
            "portfolio_metric": "value",
            "target_value": 10000.0,
            "condition": "above"
        }

        result = service.create_alert("user123", "user@test.com", alert_data)

        assert result is not None
        assert result.alert_type == "portfolio"
        assert result.portfolio_metric == "value"

    def test_create_wallet_alert(self, service):
        """Test creating a wallet alert."""
        mock_id = ObjectId()
        service.alerts.insert_one.return_value = Mock(inserted_id=mock_id)
        service.alerts.find_one.return_value = {
            "_id": mock_id,
            "user_id": "user123",
            "alert_type": "wallet",
            "wallet_address": "0x123abc",
            "target_value": 5000.0,
            "condition": "below",
            "is_active": True,
            "is_recurring": False,
            "status": "active",
            "trigger_count": 0,
            "created_at": datetime.utcnow(),
        }

        alert_data = {
            "alert_type": "wallet",
            "wallet_address": "0x123abc",
            "target_value": 5000.0,
            "condition": "below"
        }

        result = service.create_alert("user123", "user@test.com", alert_data)

        assert result is not None
        assert result.alert_type == "wallet"
        assert result.wallet_address == "0x123abc"

    def test_get_user_alerts(self, service):
        """Test getting all alerts for a user."""
        mock_id_1 = ObjectId()
        mock_id_2 = ObjectId()
        service.alerts.find.return_value.sort.return_value = [
            {
                "_id": mock_id_1,
                "user_id": "user123",
                "alert_type": "token",
                "token_symbol": "ETH",
                "target_price": 3000.0,
                "condition": "above",
                "chain": "ethereum",
                "is_active": True,
                "status": "active",
                "trigger_count": 0,
                "created_at": datetime.utcnow(),
            },
            {
                "_id": mock_id_2,
                "user_id": "user123",
                "alert_type": "token",
                "token_symbol": "SOL",
                "target_price": 100.0,
                "condition": "below",
                "chain": "solana",
                "is_active": True,
                "status": "active",
                "trigger_count": 0,
                "created_at": datetime.utcnow(),
            }
        ]

        alerts = service.get_user_alerts("user123")

        assert len(alerts) == 2
        assert alerts[0].token_symbol == "ETH"
        assert alerts[1].token_symbol == "SOL"

    def test_get_alert_found(self, service):
        """Test getting a specific alert."""
        mock_id = ObjectId()
        service.alerts.find_one.return_value = {
            "_id": mock_id,
            "user_id": "user123",
            "alert_type": "token",
            "token_symbol": "ETH",
            "target_price": 3000.0,
            "condition": "above",
            "chain": "ethereum",
            "is_active": True,
            "status": "active",
            "trigger_count": 0,
            "created_at": datetime.utcnow(),
        }

        result = service.get_alert(str(mock_id), "user123")

        assert result is not None
        assert result.token_symbol == "ETH"

    def test_get_alert_not_found(self, service):
        """Test getting a non-existent alert."""
        service.alerts.find_one.return_value = None

        result = service.get_alert(str(ObjectId()), "user123")

        assert result is None

    def test_update_alert(self, service):
        """Test updating an alert."""
        mock_id = ObjectId()
        service.alerts.update_one.return_value = Mock(matched_count=1)
        service.alerts.find_one.return_value = {
            "_id": mock_id,
            "user_id": "user123",
            "alert_type": "token",
            "token_symbol": "ETH",
            "target_price": 3500.0,
            "condition": "above",
            "chain": "ethereum",
            "is_active": True,
            "status": "active",
            "trigger_count": 0,
            "created_at": datetime.utcnow(),
        }

        result = service.update_alert(str(mock_id), "user123", {"target_price": 3500.0})

        assert result is not None
        assert result.target_price == 3500.0
        service.alerts.update_one.assert_called_once()

    def test_update_alert_not_found(self, service):
        """Test updating a non-existent alert."""
        service.alerts.update_one.return_value = Mock(matched_count=0)

        result = service.update_alert(str(ObjectId()), "user123", {"target_price": 3500.0})

        assert result is None

    def test_delete_alert_success(self, service):
        """Test deleting an alert successfully."""
        service.alerts.delete_one.return_value = Mock(deleted_count=1)

        result = service.delete_alert(str(ObjectId()), "user123")

        assert result is True

    def test_delete_alert_not_found(self, service):
        """Test deleting a non-existent alert."""
        service.alerts.delete_one.return_value = Mock(deleted_count=0)

        result = service.delete_alert(str(ObjectId()), "user123")

        assert result is False


class TestAlertStats:
    """Tests for alert statistics."""

    @pytest.fixture
    def service(self):
        """Create alert service with mocked dependencies."""
        alerts_col = Mock()
        prefs_col = Mock()
        wallets_col = Mock()
        price_svc = Mock()
        email_svc = Mock()

        return AlertService(
            alerts_col, prefs_col, wallets_col, price_svc, email_svc
        )

    def test_get_alert_stats(self, service):
        """Test getting alert statistics."""
        service.alerts.count_documents.side_effect = [
            10,  # total
            7,   # active
            2,   # triggered_today
            5,   # triggered_week
            8    # triggered_total (ever)
        ]

        stats = service.get_alert_stats("user123")

        assert stats["total_alerts"] == 10
        assert stats["active_alerts"] == 7
        assert stats["triggered_today"] == 2
        assert stats["triggered_this_week"] == 5
        assert stats["triggered_total"] == 8


class TestConditionChecking:
    """Tests for alert condition checking."""

    @pytest.fixture
    def service(self):
        """Create alert service with mocked dependencies."""
        alerts_col = Mock()
        prefs_col = Mock()
        wallets_col = Mock()
        price_svc = Mock()
        email_svc = Mock()

        return AlertService(
            alerts_col, prefs_col, wallets_col, price_svc, email_svc
        )

    def test_check_condition_above_met(self, service):
        """Test 'above' condition when met."""
        assert service._check_condition(3100.0, "above", 3000.0) is True

    def test_check_condition_above_not_met(self, service):
        """Test 'above' condition when not met."""
        assert service._check_condition(2900.0, "above", 3000.0) is False

    def test_check_condition_below_met(self, service):
        """Test 'below' condition when met."""
        assert service._check_condition(2900.0, "below", 3000.0) is True

    def test_check_condition_below_not_met(self, service):
        """Test 'below' condition when not met."""
        assert service._check_condition(3100.0, "below", 3000.0) is False

    def test_check_condition_equals_met(self, service):
        """Test 'equals' condition when met (within 1%)."""
        assert service._check_condition(3005.0, "equals", 3000.0) is True

    def test_check_condition_equals_not_met(self, service):
        """Test 'equals' condition when not met (outside 1%)."""
        assert service._check_condition(3100.0, "equals", 3000.0) is False


class TestTokenAlertChecking:
    """Tests for token alert checking."""

    @pytest.fixture
    def service(self):
        """Create alert service with mocked dependencies."""
        alerts_col = Mock()
        prefs_col = Mock()
        wallets_col = Mock()
        price_svc = Mock()
        email_svc = Mock()

        return AlertService(
            alerts_col, prefs_col, wallets_col, price_svc, email_svc
        )

    @pytest.mark.asyncio
    async def test_check_token_alerts_no_alerts(self, service):
        """Test checking when no active alerts."""
        service.alerts.find.return_value = []

        count = await service.check_token_alerts("user123")

        assert count == 0

    @pytest.mark.asyncio
    async def test_check_single_token_alert_triggered(self, service):
        """Test single token alert that should trigger."""
        mock_id = ObjectId()
        alert_doc = {
            "_id": mock_id,
            "user_id": "user123",
            "user_email": "user@test.com",
            "alert_type": "token",
            "token_symbol": "ETH",
            "target_price": 3000.0,
            "condition": "above",
            "chain": "ethereum",
            "is_active": True,
            "is_recurring": False,
            "trigger_count": 0,
        }

        service.price_service.get_price.return_value = 3100.0
        service.preferences.find_one.return_value = {"price_alerts_enabled": True}

        was_triggered = await service._check_single_token_alert(alert_doc)

        assert was_triggered is True
        service.alerts.update_one.assert_called()

    @pytest.mark.asyncio
    async def test_check_single_token_alert_not_triggered(self, service):
        """Test single token alert that should not trigger."""
        mock_id = ObjectId()
        alert_doc = {
            "_id": mock_id,
            "user_id": "user123",
            "user_email": "user@test.com",
            "alert_type": "token",
            "token_symbol": "ETH",
            "target_price": 3000.0,
            "condition": "above",
            "chain": "ethereum",
            "is_active": True,
            "is_recurring": False,
            "trigger_count": 0,
        }

        service.price_service.get_price.return_value = 2900.0

        was_triggered = await service._check_single_token_alert(alert_doc)

        assert was_triggered is False

    @pytest.mark.asyncio
    async def test_check_single_token_alert_price_unavailable(self, service):
        """Test token alert when price is unavailable."""
        mock_id = ObjectId()
        alert_doc = {
            "_id": mock_id,
            "user_id": "user123",
            "user_email": "user@test.com",
            "alert_type": "token",
            "token_symbol": "UNKNOWN",
            "target_price": 1.0,
            "condition": "above",
            "chain": "ethereum",
            "is_active": True,
            "is_recurring": False,
            "trigger_count": 0,
        }

        service.price_service.get_price.return_value = None

        was_triggered = await service._check_single_token_alert(alert_doc)

        assert was_triggered is False

    @pytest.mark.asyncio
    async def test_recurring_alert_cooldown(self, service):
        """Test recurring alert respects cooldown period."""
        mock_id = ObjectId()
        alert_doc = {
            "_id": mock_id,
            "user_id": "user123",
            "user_email": "user@test.com",
            "alert_type": "token",
            "token_symbol": "ETH",
            "target_price": 3000.0,
            "condition": "above",
            "chain": "ethereum",
            "is_active": True,
            "is_recurring": True,
            "trigger_count": 1,
            "last_triggered": datetime.utcnow() - timedelta(minutes=30),  # 30 min ago
        }

        service.price_service.get_price.return_value = 3100.0

        was_triggered = await service._check_single_token_alert(alert_doc)

        # Should not trigger because of cooldown (1 hour)
        assert was_triggered is False


class TestEmailNotifications:
    """Tests for email notification sending."""

    @pytest.fixture
    def service(self):
        """Create alert service with mocked dependencies."""
        alerts_col = Mock()
        prefs_col = Mock()
        wallets_col = Mock()
        price_svc = Mock()
        email_svc = Mock()

        return AlertService(
            alerts_col, prefs_col, wallets_col, price_svc, email_svc
        )

    @pytest.mark.asyncio
    async def test_send_token_alert_email(self, service):
        """Test sending token alert email."""
        alert_doc = {
            "_id": ObjectId(),
            "user_id": "user123",
            "user_email": "user@test.com",
            "token_symbol": "ETH",
            "chain": "ethereum",
            "target_price": 3000.0,
            "condition": "above",
            "is_recurring": False,
        }

        service.preferences.find_one.return_value = {"price_alerts_enabled": True}

        await service._send_token_alert_email(alert_doc, 3100.0)

        service.email_service.send_price_alert.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_token_alert_email_disabled(self, service):
        """Test email not sent when alerts disabled."""
        alert_doc = {
            "_id": ObjectId(),
            "user_id": "user123",
            "user_email": "user@test.com",
            "token_symbol": "ETH",
            "chain": "ethereum",
            "target_price": 3000.0,
            "condition": "above",
            "is_recurring": False,
        }

        service.preferences.find_one.return_value = {"price_alerts_enabled": False}

        await service._send_token_alert_email(alert_doc, 3100.0)

        service.email_service.send_price_alert.assert_not_called()


class TestDailyDigest:
    """Tests for daily digest functionality."""

    @pytest.fixture
    def service(self):
        """Create alert service with mocked dependencies."""
        alerts_col = Mock()
        prefs_col = Mock()
        wallets_col = Mock()
        price_svc = Mock()
        email_svc = Mock()

        return AlertService(
            alerts_col, prefs_col, wallets_col, price_svc, email_svc
        )

    @pytest.mark.asyncio
    async def test_send_daily_digests_no_users(self, service):
        """Test daily digest when no users have it enabled."""
        service.preferences.find.return_value = []

        count = await service.send_daily_digests()

        assert count == 0

    @pytest.mark.asyncio
    async def test_send_daily_digests_empty_portfolio(self, service):
        """Test daily digest skipped for empty portfolio."""
        service.preferences.find.return_value = [
            {"user_id": "user123", "user_email": "user@test.com", "daily_digest_enabled": True}
        ]
        service.wallets.find.return_value = []

        count = await service.send_daily_digests()

        # Should not send because portfolio is empty
        service.email_service.send_daily_digest.assert_not_called()


class TestWeeklySummary:
    """Tests for weekly summary functionality."""

    @pytest.fixture
    def service(self):
        """Create alert service with mocked dependencies."""
        alerts_col = Mock()
        prefs_col = Mock()
        wallets_col = Mock()
        price_svc = Mock()
        email_svc = Mock()

        return AlertService(
            alerts_col, prefs_col, wallets_col, price_svc, email_svc
        )

    @pytest.mark.asyncio
    async def test_send_weekly_summaries_no_users(self, service):
        """Test weekly summary when no users have it enabled."""
        service.preferences.find.return_value = []

        count = await service.send_weekly_summaries()

        assert count == 0


class TestDocumentConversion:
    """Tests for MongoDB document conversion."""

    @pytest.fixture
    def service(self):
        """Create alert service with mocked dependencies."""
        alerts_col = Mock()
        prefs_col = Mock()
        wallets_col = Mock()
        price_svc = Mock()
        email_svc = Mock()

        return AlertService(
            alerts_col, prefs_col, wallets_col, price_svc, email_svc
        )

    def test_doc_to_response_token_alert(self, service):
        """Test converting token alert document to response."""
        mock_id = ObjectId()
        doc = {
            "_id": mock_id,
            "user_id": "user123",
            "alert_type": "token",
            "token_symbol": "ETH",
            "target_price": 3000.0,
            "condition": "above",
            "chain": "ethereum",
            "is_active": True,
            "is_recurring": False,
            "status": "active",
            "trigger_count": 0,
            "current_price": 2950.0,
            "created_at": datetime.utcnow(),
        }

        result = service._doc_to_response(doc)

        assert isinstance(result, AlertResponse)
        assert result.id == str(mock_id)
        assert result.alert_type == "token"
        assert result.token_symbol == "ETH"
        assert result.target_price == 3000.0
        assert result.current_price == 2950.0

    def test_doc_to_response_portfolio_alert(self, service):
        """Test converting portfolio alert document to response."""
        mock_id = ObjectId()
        doc = {
            "_id": mock_id,
            "user_id": "user123",
            "alert_type": "portfolio",
            "portfolio_metric": "value",
            "target_value": 10000.0,
            "condition": "above",
            "is_active": True,
            "is_recurring": True,
            "status": "active",
            "trigger_count": 3,
            "created_at": datetime.utcnow(),
        }

        result = service._doc_to_response(doc)

        assert result.alert_type == "portfolio"
        assert result.portfolio_metric == "value"
        assert result.target_value == 10000.0
        assert result.is_recurring is True
        assert result.trigger_count == 3

    def test_doc_to_response_wallet_alert(self, service):
        """Test converting wallet alert document to response."""
        mock_id = ObjectId()
        doc = {
            "_id": mock_id,
            "user_id": "user123",
            "alert_type": "wallet",
            "wallet_address": "0x123abc",
            "target_value": 5000.0,
            "condition": "below",
            "is_active": True,
            "is_recurring": False,
            "status": "triggered",
            "trigger_count": 1,
            "last_triggered": datetime.utcnow() - timedelta(hours=2),
            "created_at": datetime.utcnow(),
        }

        result = service._doc_to_response(doc)

        assert result.alert_type == "wallet"
        assert result.wallet_address == "0x123abc"
        assert result.status == "triggered"
        assert result.last_triggered is not None


class TestCheckAllAlerts:
    """Tests for checking all alerts."""

    @pytest.fixture
    def service(self):
        """Create alert service with mocked dependencies."""
        alerts_col = Mock()
        prefs_col = Mock()
        wallets_col = Mock()
        price_svc = Mock()
        email_svc = Mock()

        return AlertService(
            alerts_col, prefs_col, wallets_col, price_svc, email_svc
        )

    @pytest.mark.asyncio
    async def test_check_all_alerts(self, service):
        """Test checking all alert types."""
        service.alerts.find.return_value = []
        service.alerts.distinct.return_value = []

        results = await service.check_all_alerts()

        assert "portfolio" in results
        assert "token" in results
        assert "wallet" in results
        assert "total" in results
        assert results["total"] == 0
