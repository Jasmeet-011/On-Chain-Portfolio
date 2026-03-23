# backend/app/services/alert_checker.py
"""
Alert Checker - Thin wrapper used by the scheduler to run all alert tiers.

All logic lives in AlertService. This module exists so the scheduler has a
clean, importable entry-point that doesn't need to know about AlertService
internals.
"""
from datetime import datetime, timezone
import logging

from app.services.alert_service import AlertService

logger = logging.getLogger(__name__)


class AlertChecker:
    """
    Delegates all alert checking to AlertService.

    Tiers:
        1 - Portfolio alerts  (total value, % change, risk, concentration)
        2 - Token alerts      (price above / below target)
        3 - Wallet alerts     (per-wallet value thresholds)
    """

    def __init__(self, alert_service: AlertService):
        self.alert_service = alert_service

    async def check_all_alerts(self) -> dict:
        """
        Run all 3 alert tiers and return a summary dict.

        Returns:
            {"portfolio": int, "token": int, "wallet": int, "total": int}
        """
        logger.info(f"[CHECKER] Starting full alert check at {datetime.now(timezone.utc).isoformat()}")

        try:
            results = await self.alert_service.check_all_alerts()
            logger.info(f"[CHECKER] Done. Triggered: {results}")
            return results
        except Exception as e:
            logger.error(f"[CHECKER] Unexpected error during alert check: {e}")
            return {"portfolio": 0, "token": 0, "wallet": 0, "total": 0}
