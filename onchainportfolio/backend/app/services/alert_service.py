# backend/app/services/alert_service.py - COMPLETE 3-TIER ALERT SYSTEM
"""
Alert Service - Complete 3-Tier Alert System
Manages portfolio, token, and wallet alerts with trigger notifications
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from pymongo.collection import Collection
from bson import ObjectId
import logging

from app.services.price_service import PriceService
from app.services.email_service import EmailService
from app.models.alert_models import (
    AlertResponse,
    PriceAlertEmailData,
    DailyDigestEmailData,
    WeeklySummaryEmailData,
)

logger = logging.getLogger(__name__)


class AlertService:
    """Service for managing all 3 tiers of alerts and notifications"""

    def __init__(
        self,
        alerts_collection: Collection,
        preferences_collection: Collection,
        wallets_collection: Collection,
        price_service: PriceService,
        email_service: EmailService
    ):
        self.alerts = alerts_collection
        self.preferences = preferences_collection
        self.wallets = wallets_collection
        self.price_service = price_service
        self.email_service = email_service

    # ============================================================
    # CRUD OPERATIONS
    # ============================================================

    def create_alert(self, user_id: str, user_email: str, alert_data: dict) -> AlertResponse:
        """Create a new alert (any tier)"""

        condition = alert_data.get("condition", "above")
        alert_type = alert_data.get("alert_type", "token")

        # Create alert document
        alert_doc = {
            "user_id": user_id,
            "user_email": user_email,
            "alert_type": alert_type,
            "condition": condition,
            "is_active": True,
            "is_recurring": alert_data.get("is_recurring", False),
            "status": "active",
            "last_triggered": None,
            "trigger_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        # Add tier-specific fields
        if alert_type == "portfolio":
            alert_doc.update({
                "portfolio_metric": alert_data["portfolio_metric"],
                "target_value": float(alert_data["target_value"])
            })
        elif alert_type == "token":
            # Fetch current price at creation time for accurate change% in future emails
            token_symbol = alert_data["token_symbol"].upper()
            token_chain = alert_data.get("chain", "solana")
            price_at_creation = None
            try:
                price_at_creation = self.price_service.get_price(token_symbol, chain=token_chain)
            except Exception as e:
                logger.warning(f"[ALERTS] Could not fetch price at creation for {token_symbol}: {e}")

            alert_doc.update({
                "token_symbol": token_symbol,
                "target_price": float(alert_data["target_price"]),
                "chain": token_chain,
                "wallet_address": alert_data.get("wallet_address"),
                "price_at_creation": price_at_creation,
                "current_price": price_at_creation,
            })
        elif alert_type == "wallet":
            alert_doc.update({
                "wallet_address": alert_data["wallet_address"],
                "target_value": float(alert_data["target_value"])
            })

        # Insert into MongoDB
        result = self.alerts.insert_one(alert_doc)

        logger.info(f"[ALERTS] Created {alert_type} alert {result.inserted_id} for {user_email}")

        # Fetch and return created alert
        return self.get_alert(str(result.inserted_id), user_id)

    def get_user_alerts(self, user_id: str) -> List[AlertResponse]:
        """Get all alerts for a user"""

        alerts = list(self.alerts.find({"user_id": user_id}).sort("created_at", -1))

        result = []
        for a in alerts:
            try:
                alert_response = self._doc_to_response(a)
                result.append(alert_response)
            except Exception as e:
                logger.error(f"[ALERTS] Error converting alert {a.get('_id')}: {e}")
                continue

        return result

    def get_alert(self, alert_id: str, user_id: str) -> Optional[AlertResponse]:
        """Get a specific alert"""

        try:
            alert = self.alerts.find_one({
                "_id": ObjectId(alert_id),
                "user_id": user_id
            })

            if not alert:
                return None

            return self._doc_to_response(alert)

        except Exception as e:
            logger.error(f"[ALERTS] Error getting alert {alert_id}: {e}")
            return None

    def update_alert(self, alert_id: str, user_id: str, update_data: dict) -> Optional[AlertResponse]:
        """Update an alert"""

        # Clean update data
        allowed_fields = ["is_active", "target_price", "target_value", "condition", "is_recurring"]
        clean_data = {k: v for k, v in update_data.items() if k in allowed_fields and v is not None}
        clean_data["updated_at"] = datetime.utcnow()

        # If reactivating, reset status
        if clean_data.get("is_active") == True:
            clean_data["status"] = "active"

        result = self.alerts.update_one(
            {"_id": ObjectId(alert_id), "user_id": user_id},
            {"$set": clean_data}
        )

        if result.matched_count == 0:
            return None

        logger.info(f"[ALERTS] Updated alert {alert_id}: {clean_data}")
        return self.get_alert(alert_id, user_id)

    def delete_alert(self, alert_id: str, user_id: str) -> bool:
        """Delete an alert"""

        result = self.alerts.delete_one({
            "_id": ObjectId(alert_id),
            "user_id": user_id
        })

        if result.deleted_count > 0:
            logger.info(f"[ALERTS] Deleted alert {alert_id}")
            return True
        return False

    def get_alert_stats(self, user_id: str) -> dict:
        """Get user's alert statistics"""

        total = self.alerts.count_documents({"user_id": user_id})
        active = self.alerts.count_documents({"user_id": user_id, "is_active": True})

        # Triggered today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        triggered_today = self.alerts.count_documents({
            "user_id": user_id,
            "last_triggered": {"$gte": today_start}
        })

        # Triggered this week
        week_start = today_start - timedelta(days=today_start.weekday())
        triggered_week = self.alerts.count_documents({
            "user_id": user_id,
            "last_triggered": {"$gte": week_start}
        })

        # Total triggered (ever)
        triggered_total = self.alerts.count_documents({
            "user_id": user_id,
            "trigger_count": {"$gt": 0}
        })

        return {
            "total_alerts": total,
            "active_alerts": active,
            "triggered_today": triggered_today,
            "triggered_this_week": triggered_week,
            "triggered_total": triggered_total
        }

    # ============================================================
    # HELPER METHODS
    # ============================================================

    def _doc_to_response(self, doc: dict) -> AlertResponse:
        """Convert MongoDB document to AlertResponse"""

        return AlertResponse(
            id=str(doc["_id"]),
            user_id=doc["user_id"],
            alert_type=doc.get("alert_type", "token"),
            portfolio_metric=doc.get("portfolio_metric"),
            token_symbol=doc.get("token_symbol"),
            chain=doc.get("chain", "aptos"),
            condition=doc.get("condition", "above"),
            target_price=doc.get("target_price"),
            wallet_address=doc.get("wallet_address"),
            target_value=doc.get("target_value"),
            current_price=doc.get("current_price"),
            is_active=doc.get("is_active", True),
            is_recurring=doc.get("is_recurring", False),
            status=doc.get("status", "active"),
            last_triggered=doc.get("last_triggered"),
            trigger_count=doc.get("trigger_count", 0),
            last_checked=doc.get("last_checked"),
            created_at=doc.get("created_at", datetime.utcnow()),
            updated_at=doc.get("updated_at")
        )

    # ============================================================
    # TIER 1: PORTFOLIO ALERTS CHECKING
    # ============================================================

    async def check_portfolio_alerts(self, user_id: str) -> List[Dict]:
        """Check all portfolio-level alerts for a user"""

        alerts = list(self.alerts.find({
            "user_id": user_id,
            "alert_type": "portfolio",
            "is_active": True
        }))

        if not alerts:
            return []

        triggered = []

        # Get user's complete portfolio data
        portfolio_data = await self._get_user_portfolio(user_id)

        for alert in alerts:
            try:
                metric = alert.get("portfolio_metric")

                if metric == "value":
                    current_value = portfolio_data["total_value"]
                    if self._check_condition(
                        current_value,
                        alert["condition"],
                        alert["target_value"]
                    ):
                        triggered.append(await self._trigger_portfolio_alert(
                            alert,
                            current_value,
                            portfolio_data
                        ))

                elif metric == "change_percent":
                    change = await self._calculate_portfolio_change(user_id, "24h")
                    if abs(change) >= alert["target_value"]:
                        triggered.append(await self._trigger_portfolio_alert(
                            alert,
                            change,
                            portfolio_data
                        ))

                elif metric == "risk_level":
                    risk_level = await self._calculate_risk_level(user_id)
                    risk_map = {"low": 1, "moderate": 2, "high": 3}
                    current_risk = risk_map.get(risk_level, 0)
                    target_risk = risk_map.get(alert["target_value"], 0)

                    if current_risk >= target_risk:
                        triggered.append(await self._trigger_portfolio_alert(
                            alert,
                            risk_level,
                            portfolio_data
                        ))

                elif metric == "concentration":
                    concentration = await self._calculate_max_concentration(user_id)
                    if concentration >= alert["target_value"]:
                        triggered.append(await self._trigger_portfolio_alert(
                            alert,
                            concentration,
                            portfolio_data
                        ))

            except Exception as e:
                logger.error(f"Error checking portfolio alert {alert['_id']}: {e}")

        return triggered

    # ============================================================
    # TIER 2: TOKEN ALERTS CHECKING
    # ============================================================

    async def check_token_alerts(self, user_id: Optional[str] = None) -> int:
        """
        Check all active token price alerts.
        If user_id provided, check only that user's alerts.
        Returns number of triggered alerts.
        """
        logger.info("[ALERTS] Starting token alert check...")

        # Build query
        query = {
            "alert_type": "token",
            "is_active": True,
            "status": {"$in": ["active", None]}
        }
        if user_id:
            query["user_id"] = user_id

        # Get all active token alerts
        active_alerts = list(self.alerts.find(query))

        logger.info(f"[ALERTS] Found {len(active_alerts)} active token alerts to check")

        triggered_count = 0

        for alert_doc in active_alerts:
            try:
                was_triggered = await self._check_single_token_alert(alert_doc)
                if was_triggered:
                    triggered_count += 1
            except Exception as e:
                logger.error(f"[ALERTS] Error checking alert {alert_doc['_id']}: {e}")

        logger.info(f"[ALERTS] Token check complete. {triggered_count} alerts triggered.")
        return triggered_count

    async def _check_single_token_alert(self, alert_doc: dict) -> bool:
        """Check a single token alert and trigger if conditions met"""

        alert_id = str(alert_doc["_id"])
        token = alert_doc["token_symbol"]
        chain = alert_doc.get("chain", "aptos")
        condition = alert_doc["condition"]
        target_price = alert_doc["target_price"]
        is_recurring = alert_doc.get("is_recurring", False)
        last_triggered = alert_doc.get("last_triggered")

        # Get current price
        try:
            current_price = self.price_service.get_price(token, chain=chain)
        except Exception as e:
            logger.warning(f"[ALERTS] Could not fetch price for {token}: {e}")
            return False

        if current_price is None:
            return False

        # Update current price and last_checked
        self.alerts.update_one(
            {"_id": ObjectId(alert_id)},
            {"$set": {
                "current_price": current_price,
                "last_checked": datetime.utcnow()
            }}
        )

        # Check if alert should trigger
        should_trigger = False

        if condition == "above" and current_price >= target_price:
            should_trigger = True
        elif condition == "below" and current_price <= target_price:
            should_trigger = True

        if not should_trigger:
            return False

        # For recurring alerts, don't trigger if recently triggered (within 1 hour)
        if is_recurring and last_triggered:
            time_since_last = datetime.utcnow() - last_triggered
            if time_since_last < timedelta(hours=1):
                logger.debug(f"[ALERTS] Alert {alert_id} recently triggered, skipping")
                return False

        # TRIGGER!
        logger.info(f"[ALERTS] 🚨 Alert {alert_id} triggered! {token} is ${current_price:.4f}, target was {condition} ${target_price:.4f}")

        # Send email notification
        await self._send_token_alert_email(alert_doc, current_price)

        # Update alert status
        update_data = {
            "last_triggered": datetime.utcnow(),
            "trigger_count": alert_doc.get("trigger_count", 0) + 1,
            "current_price": current_price,
            "updated_at": datetime.utcnow()
        }

        if not is_recurring:
            # One-time alert - disable it
            update_data["is_active"] = False
            update_data["status"] = "triggered"
        else:
            update_data["status"] = "triggered"

        self.alerts.update_one(
            {"_id": ObjectId(alert_id)},
            {"$set": update_data}
        )

        return True

    # ============================================================
    # TIER 3: WALLET ALERTS CHECKING
    # ============================================================

    async def check_wallet_alerts(self, user_id: str) -> List[Dict]:
        """Check all wallet-specific alerts for a user"""

        alerts = list(self.alerts.find({
            "user_id": user_id,
            "alert_type": "wallet",
            "is_active": True
        }))

        if not alerts:
            return []

        triggered = []

        for alert in alerts:
            try:
                wallet_address = alert["wallet_address"]

                # Get current wallet value
                wallet_data = await self._get_wallet_value(user_id, wallet_address)
                current_value = wallet_data["total_value"]

                # Check if condition is met
                if self._check_condition(
                    current_value,
                    alert["condition"],
                    alert["target_value"]
                ):
                    triggered.append(await self._trigger_wallet_alert(
                        alert,
                        current_value,
                        wallet_data
                    ))

            except Exception as e:
                logger.error(f"Error checking wallet alert {alert['_id']}: {e}")

        return triggered

    # ============================================================
    # CHECK ALL ALERTS (Called by Scheduler)
    # ============================================================

    async def check_all_alerts(self) -> Dict[str, int]:
        """
        Check all active alerts across all 3 tiers.
        Called by scheduler every 5 minutes.
        Returns dict with counts per tier.
        """
        logger.info("[ALERTS] Starting comprehensive alert check...")

        results = {
            "portfolio": 0,
            "token": 0,
            "wallet": 0,
            "total": 0
        }

        # Check token alerts (most common)
        token_count = await self.check_token_alerts()
        results["token"] = token_count

        # Check portfolio and wallet alerts for each user with active alerts
        users_with_alerts = self.alerts.distinct("user_id", {
            "is_active": True,
            "alert_type": {"$in": ["portfolio", "wallet"]}
        })

        for user_id in users_with_alerts:
            try:
                # Check portfolio alerts
                portfolio_triggered = await self.check_portfolio_alerts(user_id)
                results["portfolio"] += len(portfolio_triggered)

                # Check wallet alerts
                wallet_triggered = await self.check_wallet_alerts(user_id)
                results["wallet"] += len(wallet_triggered)

            except Exception as e:
                logger.error(f"[ALERTS] Error checking alerts for user {user_id}: {e}")

        results["total"] = results["portfolio"] + results["token"] + results["wallet"]

        logger.info(f"[ALERTS] Check complete. Triggered: {results}")
        return results

    # ============================================================
    # HELPER FUNCTIONS - CONDITION CHECKING
    # ============================================================

    def _check_condition(self, current: float, condition: str, target: float) -> bool:
        """Check if alert condition is met"""
        if condition == "above":
            return current >= target
        elif condition == "below":
            return current <= target
        elif condition == "equals":
            # Allow 1% tolerance for equals
            return abs(current - target) / target < 0.01
        return False

    # ============================================================
    # HELPER FUNCTIONS - PORTFOLIO CALCULATIONS
    # ============================================================

    async def _get_user_portfolio(self, user_id: str) -> Dict:
        """Get complete portfolio data for user"""

        wallets = list(self.wallets.find({"user_id": user_id}))

        total_value = 0
        all_balances = []
        token_totals = {}

        for wallet in wallets:
            try:
                # Get wallet's portfolio
                from app.services.adapters import get_adapter_for_chain
                adapter = get_adapter_for_chain(wallet["chain"])
                portfolio = adapter.get_portfolio(wallet["address"])

                wallet_value = 0
                for balance in portfolio.get("balances", []):
                    symbol = balance.get("symbol", "")
                    amount = balance.get("amount", 0)

                    # Get price
                    price = self.price_service.get_price(symbol, chain=wallet["chain"])
                    if price:
                        usd_value = amount * price
                        balance["usd_value"] = usd_value
                        wallet_value += usd_value

                        # Track token totals
                        if symbol not in token_totals:
                            token_totals[symbol] = {"amount": 0, "value": 0}
                        token_totals[symbol]["amount"] += amount
                        token_totals[symbol]["value"] += usd_value

                    all_balances.append(balance)

                total_value += wallet_value

            except Exception as e:
                logger.error(f"Error getting portfolio for wallet {wallet['address']}: {e}")

        return {
            "total_value": total_value,
            "wallet_count": len(wallets),
            "balances": all_balances,
            "token_totals": token_totals
        }

    async def _calculate_portfolio_change(self, user_id: str, period: str) -> float:
        """Calculate portfolio change percentage over period"""

        # Get current value
        portfolio = await self._get_user_portfolio(user_id)
        current_value = portfolio["total_value"]

        # Get historical value from snapshots
        if period == "24h":
            cutoff = datetime.utcnow() - timedelta(hours=24)
        elif period == "7d":
            cutoff = datetime.utcnow() - timedelta(days=7)
        else:
            cutoff = datetime.utcnow() - timedelta(hours=24)

        # Try to find snapshot near cutoff time
        from app.services.db import snapshots_collection
        snapshot = snapshots_collection.find_one(
            {
                "user_id": user_id,
                "snapshot_date": {"$lte": cutoff}
            },
            sort=[("snapshot_date", -1)]
        )

        if not snapshot:
            return 0.0

        old_value = snapshot.get("total_value", current_value)

        if old_value == 0:
            return 0.0

        change_percent = ((current_value - old_value) / old_value) * 100
        return change_percent

    async def _calculate_risk_level(self, user_id: str) -> str:
        """Calculate portfolio risk level based on concentration"""

        concentration = await self._calculate_max_concentration(user_id)

        if concentration >= 50:
            return "high"
        elif concentration >= 30:
            return "moderate"
        else:
            return "low"

    async def _calculate_max_concentration(self, user_id: str) -> float:
        """Calculate maximum token concentration percentage"""

        portfolio = await self._get_user_portfolio(user_id)

        if portfolio["total_value"] == 0:
            return 0.0

        # Find token with highest value
        max_value = 0
        for token_data in portfolio["token_totals"].values():
            if token_data["value"] > max_value:
                max_value = token_data["value"]

        concentration = (max_value / portfolio["total_value"]) * 100
        return concentration

    # ============================================================
    # HELPER FUNCTIONS - WALLET CALCULATIONS
    # ============================================================

    async def _get_wallet_value(self, user_id: str, wallet_address: str) -> Dict:
        """Get current value of a specific wallet"""

        wallet = self.wallets.find_one({
            "user_id": user_id,
            "address": wallet_address
        })

        if not wallet:
            return {"total_value": 0, "balances": []}

        try:
            from app.services.adapters import get_adapter_for_chain
            adapter = get_adapter_for_chain(wallet["chain"])
            portfolio = adapter.get_portfolio(wallet_address)

            total_value = 0
            balances = []

            for balance in portfolio.get("balances", []):
                symbol = balance.get("symbol", "")
                amount = balance.get("amount", 0)

                price = self.price_service.get_price(symbol, chain=wallet["chain"])
                if price:
                    usd_value = amount * price
                    balance["usd_value"] = usd_value
                    total_value += usd_value

                balances.append(balance)

            return {
                "total_value": total_value,
                "balances": balances,
                "wallet_address": wallet_address,
                "chain": wallet["chain"]
            }

        except Exception as e:
            logger.error(f"Error getting wallet value for {wallet_address}: {e}")
            return {"total_value": 0, "balances": []}

    # ============================================================
    # TRIGGER & NOTIFICATION FUNCTIONS
    # ============================================================

    async def _trigger_portfolio_alert(
        self,
        alert: Dict,
        current_value: float,
        portfolio_data: Dict
    ) -> Dict:
        """Trigger a portfolio alert and send notification"""

        alert_id = str(alert["_id"])

        # Update alert in database
        self.alerts.update_one(
            {"_id": alert["_id"]},
            {
                "$set": {
                    "last_triggered": datetime.utcnow(),
                    "trigger_count": alert.get("trigger_count", 0) + 1,
                    "is_active": False if not alert.get("is_recurring") else True,
                    "status": "triggered",
                    "last_checked": datetime.utcnow()
                }
            }
        )

        # Send notification (implement as needed)
        logger.info(f"[ALERTS] Portfolio alert {alert_id} triggered: {current_value}")

        return {
            "alert_id": alert_id,
            "alert_type": "portfolio",
            "triggered_at": datetime.utcnow(),
            "current_value": current_value
        }

    async def _trigger_wallet_alert(
        self,
        alert: Dict,
        current_value: float,
        wallet_data: Dict
    ) -> Dict:
        """Trigger a wallet alert and send notification"""

        alert_id = str(alert["_id"])

        # Update alert
        self.alerts.update_one(
            {"_id": alert["_id"]},
            {
                "$set": {
                    "last_triggered": datetime.utcnow(),
                    "trigger_count": alert.get("trigger_count", 0) + 1,
                    "is_active": False if not alert.get("is_recurring") else True,
                    "status": "triggered",
                    "last_checked": datetime.utcnow()
                }
            }
        )

        logger.info(f"[ALERTS] Wallet alert {alert_id} triggered: ${current_value:.2f}")

        return {
            "alert_id": alert_id,
            "alert_type": "wallet",
            "triggered_at": datetime.utcnow(),
            "current_value": current_value
        }

    async def _send_token_alert_email(self, alert_doc: dict, current_price: float):
        """Send token price alert notification email"""

        user_email = alert_doc["user_email"]
        user_id = alert_doc["user_id"]

        # Check if user's email is verified before sending any alert email
        try:
            from app.services.auth_service import get_user_by_id
            user = get_user_by_id(user_id)
            if user and not user.get("is_email_verified", True):
                # Legacy accounts (created before verification) are treated as verified
                # New accounts must verify first
                if "is_email_verified" in user:
                    logger.info(f"[ALERTS] User {user_email} email not verified, skipping alert email")
                    return
        except Exception:
            pass  # Don't block alert sending if user lookup fails

        # Check if user has price alerts enabled
        prefs = self.preferences.find_one({"user_id": user_id})
        if prefs and not prefs.get("price_alerts_enabled", True):
            logger.info(f"[ALERTS] User {user_email} has price alerts disabled, skipping email")
            return

        token = alert_doc["token_symbol"]
        chain = alert_doc.get("chain", "aptos")
        target_price = alert_doc["target_price"]
        condition = alert_doc["condition"]

        # Calculate real change from price when alert was created
        price_at_creation = alert_doc.get("price_at_creation")
        if price_at_creation and price_at_creation > 0:
            change_24h = current_price - price_at_creation
            change_percent = ((current_price - price_at_creation) / price_at_creation) * 100
        else:
            # No baseline recorded – show 0 rather than fake data
            change_24h = 0.0
            change_percent = 0.0

        email_data = PriceAlertEmailData(
            user_email=user_email,
            user_name=user_email.split("@")[0].title(),
            token_symbol=token,
            chain=chain,
            alert_type=condition,
            target_price=target_price,
            current_price=current_price,
            change_24h=change_24h,
            change_percent=change_percent,
            is_recurring=alert_doc.get("is_recurring", False),
            wallet_address=alert_doc.get("wallet_address"),
            alert_id=str(alert_doc["_id"])
        )

        try:
            self.email_service.send_price_alert(email_data)
            logger.info(f"[ALERTS] ✅ Email sent to {user_email}")
        except Exception as e:
            logger.error(f"[ALERTS] ❌ Failed to send email to {user_email}: {e}")

    # ============================================================
    # DAILY DIGEST (Called by Scheduler)
    # ============================================================

    async def send_daily_digests(self) -> int:
        """Send daily portfolio digest to users who have it enabled"""

        logger.info("[ALERTS] Sending daily digests...")

        users_with_digest = list(self.preferences.find({
            "daily_digest_enabled": True
        }))

        logger.info(f"[ALERTS] Found {len(users_with_digest)} users with daily digest enabled")

        sent_count = 0

        for prefs in users_with_digest:
            try:
                await self._send_daily_digest(prefs)
                sent_count += 1
            except Exception as e:
                logger.error(f"[ALERTS] Error sending digest to {prefs.get('user_email')}: {e}")

        logger.info(f"[ALERTS] Sent {sent_count} daily digests")
        return sent_count

    async def _send_daily_digest(self, prefs: dict):
        """Send daily digest to a single user"""

        user_email = prefs.get("user_email", "")
        user_id = prefs["user_id"]

        if not user_email:
            logger.warning(f"[ALERTS] No email for user {user_id}, skipping digest")
            return

        # Get user's portfolio
        portfolio = await self._get_user_portfolio(user_id)

        if portfolio["total_value"] == 0:
            logger.info(f"[ALERTS] User {user_email} has empty portfolio, skipping digest")
            return

        # Calculate 24h change
        change_percent = await self._calculate_portfolio_change(user_id, "24h")
        change_24h = portfolio["total_value"] * (change_percent / 100)

        # Find real top gainer/loser by fetching 24h price changes from CoinGecko
        top_gainer = None
        top_loser = None
        try:
            token_symbols = list(portfolio["token_totals"].keys())
            if token_symbols:
                price_changes = self.price_service.get_prices_with_changes(token_symbols)
                if price_changes:
                    best = max(price_changes.items(), key=lambda x: x[1].get("change_24h", 0), default=None)
                    worst = min(price_changes.items(), key=lambda x: x[1].get("change_24h", 0), default=None)
                    if best and best[1].get("change_24h") is not None:
                        top_gainer = {"symbol": best[0], "change_percent": round(best[1]["change_24h"], 2)}
                    if worst and worst[1].get("change_24h") is not None:
                        top_loser = {"symbol": worst[0], "change_percent": round(worst[1]["change_24h"], 2)}
        except Exception as e:
            logger.warning(f"[ALERTS] Could not fetch price changes for digest: {e}")

        email_data = DailyDigestEmailData(
            user_email=user_email,
            user_name=user_email.split("@")[0].title(),
            portfolio_value=portfolio["total_value"],
            change_24h=change_24h,
            change_percent=change_percent,
            top_gainer=top_gainer,
            top_loser=top_loser,
            total_tokens=len(portfolio["token_totals"])
        )

        self.email_service.send_daily_digest(email_data)

        # Update last sent timestamp
        self.preferences.update_one(
            {"user_id": user_id},
            {"$set": {"last_daily_digest": datetime.utcnow()}}
        )

    # ============================================================
    # WEEKLY SUMMARY (Called by Scheduler)
    # ============================================================

    async def send_weekly_summaries(self) -> int:
        """Send weekly summary to users who have it enabled"""

        logger.info("[ALERTS] Sending weekly summaries...")

        users_with_weekly = list(self.preferences.find({
            "weekly_summary_enabled": True
        }))

        sent_count = 0

        for prefs in users_with_weekly:
            try:
                await self._send_weekly_summary(prefs)
                sent_count += 1
            except Exception as e:
                logger.error(f"[ALERTS] Error sending summary: {e}")

        logger.info(f"[ALERTS] Sent {sent_count} weekly summaries")
        return sent_count

    async def _send_weekly_summary(self, prefs: dict):
        """Send weekly summary to a single user"""

        user_email = prefs.get("user_email", "")
        user_id = prefs["user_id"]

        if not user_email:
            return

        # Get current portfolio
        portfolio = await self._get_user_portfolio(user_id)

        # Calculate 7d change
        change_percent = await self._calculate_portfolio_change(user_id, "7d")
        change_week = portfolio["total_value"] * (change_percent / 100)
        portfolio_value_start = portfolio["total_value"] - change_week

        # Count alerts triggered this week
        week_start = datetime.utcnow() - timedelta(days=7)
        alerts_triggered = self.alerts.count_documents({
            "user_id": user_id,
            "last_triggered": {"$gte": week_start}
        })

        # Find real best/worst performer over the week using 24h changes as proxy
        best_performer = None
        worst_performer = None
        try:
            token_symbols = list(portfolio["token_totals"].keys())
            if token_symbols:
                price_changes = self.price_service.get_prices_with_changes(token_symbols)
                if price_changes:
                    best = max(price_changes.items(), key=lambda x: x[1].get("change_24h", 0), default=None)
                    worst = min(price_changes.items(), key=lambda x: x[1].get("change_24h", 0), default=None)
                    if best and best[1].get("change_24h") is not None:
                        best_performer = {"symbol": best[0], "change_percent": round(best[1]["change_24h"], 2)}
                    if worst and worst[1].get("change_24h") is not None:
                        worst_performer = {"symbol": worst[0], "change_percent": round(worst[1]["change_24h"], 2)}
        except Exception as e:
            logger.warning(f"[ALERTS] Could not fetch price changes for weekly summary: {e}")

        email_data = WeeklySummaryEmailData(
            user_email=user_email,
            user_name=user_email.split("@")[0].title(),
            portfolio_value_start=portfolio_value_start,
            portfolio_value_end=portfolio["total_value"],
            change_week=change_week,
            change_percent=change_percent,
            best_performer=best_performer,
            worst_performer=worst_performer,
            alerts_triggered=alerts_triggered,
            total_tokens=len(portfolio["token_totals"])
        )

        self.email_service.send_weekly_summary(email_data)

        self.preferences.update_one(
            {"user_id": user_id},
            {"$set": {"last_weekly_summary": datetime.utcnow()}}
        )

    # ============================================================
    # MILESTONE CHECKS (Called by Scheduler)
    # ============================================================

    async def check_milestones(self) -> int:
        """
        Check for price milestones (ATH, etc.) - Placeholder implementation.
        Called by scheduler every hour.
        Returns number of milestones detected.
        """
        logger.info("[ALERTS] Milestone check - no milestones configured yet")
        return 0

    # ============================================================
    # PORTFOLIO SUGGESTIONS (Rule-Based)
    # ============================================================

    async def get_portfolio_suggestions(self, user_id: str) -> List[Dict]:
        """
        Generate rule-based portfolio rebalancing suggestions.

        Rules:
        1. Concentration >50% in one token → suggest reducing
        2. No stablecoins (<5%) → suggest adding USDC
        3. Single chain (>95%) → suggest diversifying chains
        4. No blue-chip tokens → suggest adding ETH or SOL
        5. Large unrealised gain (>100% from creation price) → suggest taking profits
        """
        suggestions = []

        try:
            portfolio = await self._get_user_portfolio(user_id)
            total_value = portfolio["total_value"]
            token_totals = portfolio["token_totals"]

            if total_value == 0 or not token_totals:
                return []

            # ── Rule 1: Concentration risk ─────────────────────────────
            for symbol, data in token_totals.items():
                pct = (data["value"] / total_value) * 100
                if pct > 50:
                    suggestions.append({
                        "type": "reduce",
                        "priority": "high",
                        "token": symbol,
                        "title": f"High concentration in {symbol}",
                        "reason": (
                            f"{symbol} makes up {pct:.0f}% of your portfolio. "
                            f"Consider rebalancing to reduce single-asset risk."
                        ),
                        "action": f"Consider selling some {symbol} and diversifying",
                    })

            # ── Rule 2: No stablecoins ─────────────────────────────────
            stablecoins = {"USDC", "USDT", "DAI", "FRAX", "BUSD", "LUSD"}
            stable_value = sum(
                d["value"] for s, d in token_totals.items() if s.upper() in stablecoins
            )
            stable_pct = (stable_value / total_value) * 100 if total_value > 0 else 0
            if stable_pct < 5:
                suggestions.append({
                    "type": "buy",
                    "priority": "medium",
                    "token": "USDC",
                    "title": "No stable reserves",
                    "reason": (
                        f"Only {stable_pct:.1f}% of your portfolio is in stablecoins. "
                        f"Holding some USDC provides a buffer during market downturns."
                    ),
                    "action": "Consider adding USDC as a stable reserve (10–20% allocation)",
                })

            # ── Rule 3: Single-chain concentration ────────────────────
            wallets = list(self.wallets.find({"user_id": user_id}))
            chains_used = set(w.get("chain", "") for w in wallets)
            # Normalise testnets
            normalised_chains = set()
            for c in chains_used:
                if "ethereum" in c or "evm" in c:
                    normalised_chains.add("ethereum")
                elif "polygon" in c:
                    normalised_chains.add("polygon")
                elif "base" in c:
                    normalised_chains.add("base")
                else:
                    normalised_chains.add(c)

            if len(normalised_chains) == 1:
                only_chain = next(iter(normalised_chains))
                suggestions.append({
                    "type": "diversify",
                    "priority": "medium",
                    "token": None,
                    "title": "Single-chain exposure",
                    "reason": (
                        f"All your assets are on {only_chain}. "
                        f"Diversifying across chains reduces protocol-specific risk."
                    ),
                    "action": "Consider adding wallets on Solana, Ethereum, or Aptos",
                })

            # ── Rule 4: No blue-chip tokens ───────────────────────────
            blue_chips = {"ETH", "BTC", "WBTC", "WETH", "SOL"}
            has_blue_chip = any(s.upper() in blue_chips for s in token_totals)
            if not has_blue_chip and total_value > 100:
                suggestions.append({
                    "type": "buy",
                    "priority": "low",
                    "token": "ETH",
                    "title": "No blue-chip assets",
                    "reason": (
                        "Your portfolio has no ETH, BTC, or SOL. "
                        "Blue-chip crypto assets typically offer better liquidity and lower long-term risk."
                    ),
                    "action": "Consider allocating a small portion to ETH or SOL",
                })

            # ── Rule 5: Large unrealised gain from alert creation ──────
            # Check alerts with price_at_creation that doubled
            triggered_alerts = list(self.alerts.find({
                "user_id": user_id,
                "alert_type": "token",
                "is_active": True,
                "price_at_creation": {"$gt": 0},
            }))
            for alert in triggered_alerts:
                symbol = alert.get("token_symbol", "")
                pac = alert.get("price_at_creation", 0)
                current = alert.get("current_price")
                if current and pac and current >= pac * 2:
                    gain_pct = ((current - pac) / pac) * 100
                    suggestions.append({
                        "type": "take_profit",
                        "priority": "medium",
                        "token": symbol,
                        "title": f"{symbol} up {gain_pct:.0f}% since your alert",
                        "reason": (
                            f"{symbol} has doubled from ${pac:.4f} to ${current:.4f} "
                            f"since you set your alert. Consider taking some profits."
                        ),
                        "action": f"Consider selling a portion of your {symbol} position",
                    })

        except Exception as e:
            logger.error(f"[ALERTS] Error generating suggestions for {user_id}: {e}", exc_info=True)

        return suggestions
