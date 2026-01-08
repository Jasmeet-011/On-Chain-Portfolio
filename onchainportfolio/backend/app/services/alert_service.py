# backend/app/services/alert_service.py - FIXED VERSION
"""
Alert Service - Manage price alerts and trigger notifications
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
    """Service for managing price alerts and notifications"""
    
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
        """Create a new price alert"""
        
        # ✅ FIXED: Map 'condition' to 'alert_type' for storage
        # Frontend sends: condition = "above" or "below"
        # We store it as: condition (for the check) and alert_type (for display)
        condition = alert_data.get("condition", "above")
        
        # Create alert document
        alert_doc = {
            "user_id": user_id,
            "user_email": user_email,
            "alert_type": "token",  # Always "token" for price alerts
            "token_symbol": alert_data["token_symbol"].upper(),
            "chain": alert_data.get("chain", "aptos"),
            "condition": condition,  # "above" or "below"
            "target_price": float(alert_data["target_price"]),
            "wallet_address": alert_data.get("wallet_address"),
            "current_price": None,
            "is_active": True,
            "is_recurring": alert_data.get("is_recurring", False),
            "status": "active",
            "last_triggered": None,
            "trigger_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Insert into MongoDB
        result = self.alerts.insert_one(alert_doc)
        
        logger.info(f"[ALERTS] Created alert {result.inserted_id} for {user_email}: {alert_doc['token_symbol']} {condition} ${alert_doc['target_price']}")
        
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
        allowed_fields = ["is_active", "target_price", "condition", "is_recurring"]
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
            token_symbol=doc.get("token_symbol"),
            chain=doc.get("chain", "aptos"),
            condition=doc.get("condition", "above"),
            target_price=doc.get("target_price"),
            wallet_address=doc.get("wallet_address"),
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
    # PRICE CHECKING (Called by Cron/Scheduler)
    # ============================================================
    
    async def check_all_alerts(self) -> int:
        """
        Check all active alerts against current prices.
        Called by scheduler every 5 minutes.
        Returns number of triggered alerts.
        """
        logger.info("[ALERTS] Starting alert check...")
        
        # Get all active alerts
        active_alerts = list(self.alerts.find({
            "is_active": True,
            "status": {"$in": ["active", None]}
        }))
        
        logger.info(f"[ALERTS] Found {len(active_alerts)} active alerts to check")
        
        triggered_count = 0
        
        for alert_doc in active_alerts:
            try:
                was_triggered = await self._check_single_alert(alert_doc)
                if was_triggered:
                    triggered_count += 1
            except Exception as e:
                logger.error(f"[ALERTS] Error checking alert {alert_doc['_id']}: {e}")
        
        logger.info(f"[ALERTS] Check complete. {triggered_count} alerts triggered.")
        return triggered_count
    
    async def _check_single_alert(self, alert_doc: dict) -> bool:
        """Check a single alert and trigger if conditions met"""
        
        alert_id = str(alert_doc["_id"])
        token = alert_doc["token_symbol"]
        chain = alert_doc.get("chain", "aptos")
        condition = alert_doc["condition"]  # "above" or "below"
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
        await self._send_alert_email(alert_doc, current_price)
        
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
    
    async def _send_alert_email(self, alert_doc: dict, current_price: float):
        """Send price alert notification email"""
        
        user_email = alert_doc["user_email"]
        user_id = alert_doc["user_id"]
        
        # Check if user has price alerts enabled
        prefs = self.preferences.find_one({"user_id": user_id})
        if prefs and not prefs.get("price_alerts_enabled", True):
            logger.info(f"[ALERTS] User {user_email} has price alerts disabled, skipping email")
            return
        
        token = alert_doc["token_symbol"]
        chain = alert_doc.get("chain", "aptos")
        target_price = alert_doc["target_price"]
        condition = alert_doc["condition"]
        
        # Calculate approximate 24h change
        # In production, you'd fetch this from price history
        change_24h = current_price * 0.025  # Placeholder 2.5%
        change_percent = 2.5
        
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
        
        # Get user's wallets
        user_wallets = list(self.wallets.find({"user_id": user_id}))
        
        if not user_wallets:
            logger.info(f"[ALERTS] User {user_email} has no wallets, skipping digest")
            return
        
        # Calculate portfolio value (placeholder - implement actual calculation)
        portfolio_value = 1000.0
        change_24h = 25.0
        change_percent = 2.5
        
        email_data = DailyDigestEmailData(
            user_email=user_email,
            user_name=user_email.split("@")[0].title(),
            portfolio_value=portfolio_value,
            change_24h=change_24h,
            change_percent=change_percent,
            top_gainer={"symbol": "SOL", "change_percent": 5.2},
            top_loser={"symbol": "APT", "change_percent": -2.1},
            total_tokens=len(user_wallets)
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
        
        # Count alerts triggered this week
        week_start = datetime.utcnow() - timedelta(days=7)
        alerts_triggered = self.alerts.count_documents({
            "user_id": user_id,
            "last_triggered": {"$gte": week_start}
        })
        
        email_data = WeeklySummaryEmailData(
            user_email=user_email,
            user_name=user_email.split("@")[0].title(),
            portfolio_value_start=950.0,
            portfolio_value_end=1000.0,
            change_week=50.0,
            change_percent=5.26,
            best_performer={"symbol": "SOL", "change_percent": 15.0},
            worst_performer={"symbol": "APT", "change_percent": -5.0},
            alerts_triggered=alerts_triggered,
            total_tokens=2
        )
        
        self.email_service.send_weekly_summary(email_data)
        
        self.preferences.update_one(
            {"user_id": user_id},
            {"$set": {"last_weekly_summary": datetime.utcnow()}}
        )