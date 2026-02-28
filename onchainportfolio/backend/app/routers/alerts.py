# backend/app/routers/alerts.py - IMPROVED ERROR HANDLING
"""
Alert API Endpoints - Token Price Alerts with improved error handling
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from pydantic import ValidationError
import logging

from app.models.alert_models import (
    CreateAlertRequest,
    UpdateAlertRequest,
    AlertResponse,
    AlertStatsResponse,
    EmailPreferencesRequest,
    EmailPreferencesResponse,
    PriceAlertEmailData
)
from app.deps import get_current_user, get_alert_service, get_email_preferences_service
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# CUSTOM EXCEPTIONS
# ============================================================

class AlertNotFoundException(HTTPException):
    def __init__(self, alert_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID '{alert_id}' not found"
        )


class AlertCreationException(HTTPException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create alert: {message}"
        )


class AlertUpdateException(HTTPException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update alert: {message}"
        )


# ============================================================
# PRICE ALERTS
# ============================================================

@router.post("/", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    request: CreateAlertRequest,
    current_user: dict = Depends(get_current_user),
    alert_service = Depends(get_alert_service)
):
    """
    Create a new price alert.

    - **token_symbol**: Token symbol (SOL, APT, etc.)
    - **target_price**: Target price in USD
    - **condition**: "above" or "below"
    - **wallet_address**: Optional specific wallet (null = all wallets)

    Raises:
        - 400: Invalid request data
        - 401: Unauthorized
        - 500: Server error
    """
    try:
        # Validate token symbol
        if not request.token_symbol or len(request.token_symbol.strip()) == 0:
            raise AlertCreationException("Token symbol cannot be empty")

        # Validate target price
        if request.target_price <= 0:
            raise AlertCreationException("Target price must be greater than 0")

        # Build alert data from request
        alert_data = {
            "token_symbol": request.token_symbol.strip().upper(),
            "target_price": request.target_price,
            "condition": request.condition,
            "wallet_address": request.wallet_address,
            "chain": request.chain or "solana",
            "is_recurring": request.is_recurring or False,
            "alert_type": "token",
        }

        alert = alert_service.create_alert(
            user_id=str(current_user["_id"]),
            user_email=current_user["email"],
            alert_data=alert_data
        )

        logger.info(f"[ALERTS] Created alert for user {current_user['email']}: {request.token_symbol}")
        return alert

    except AlertCreationException:
        raise
    except ValidationError as e:
        logger.error(f"[ALERTS] Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}"
        )
    except ValueError as e:
        logger.error(f"[ALERTS] Value error: {e}")
        raise AlertCreationException(str(e))
    except Exception as e:
        logger.error(f"[ALERTS] Unexpected error creating alert: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the alert"
        )


@router.get("/", response_model=List[AlertResponse])
async def get_alerts(
    current_user: dict = Depends(get_current_user),
    alert_service = Depends(get_alert_service)
):
    """
    Get all alerts for the current user.

    Returns:
        List of alerts sorted by creation date (newest first)

    Raises:
        - 401: Unauthorized
        - 500: Server error
    """
    try:
        alerts = alert_service.get_user_alerts(str(current_user["_id"]))
        return alerts

    except Exception as e:
        logger.error(f"[ALERTS] Error fetching alerts for user {current_user['email']}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch alerts"
        )


@router.get("/stats", response_model=AlertStatsResponse)
async def get_alert_stats(
    current_user: dict = Depends(get_current_user),
    alert_service = Depends(get_alert_service)
):
    """
    Get user's alert statistics.

    Returns:
        Statistics including total alerts, active alerts, and trigger counts

    Raises:
        - 401: Unauthorized
        - 500: Server error
    """
    try:
        stats = alert_service.get_alert_stats(str(current_user["_id"]))
        return AlertStatsResponse(**stats)

    except ValidationError as e:
        logger.error(f"[ALERTS] Stats validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error formatting alert statistics"
        )
    except Exception as e:
        logger.error(f"[ALERTS] Error fetching stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch alert statistics"
        )


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user),
    alert_service = Depends(get_alert_service)
):
    """
    Get a specific alert by ID.

    Args:
        alert_id: The alert ID to retrieve

    Returns:
        Alert details

    Raises:
        - 401: Unauthorized
        - 404: Alert not found
        - 500: Server error
    """
    try:
        alert = alert_service.get_alert(alert_id, str(current_user["_id"]))

        if not alert:
            raise AlertNotFoundException(alert_id)

        return alert

    except AlertNotFoundException:
        raise
    except Exception as e:
        logger.error(f"[ALERTS] Error fetching alert {alert_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch alert"
        )


@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: str,
    request: UpdateAlertRequest,
    current_user: dict = Depends(get_current_user),
    alert_service = Depends(get_alert_service)
):
    """
    Update an alert.

    Can update:
    - target_price: New target price
    - is_active: Enable/disable alert
    - condition: Change condition (above/below)

    Args:
        alert_id: The alert ID to update
        request: Fields to update

    Returns:
        Updated alert details

    Raises:
        - 400: Invalid update data
        - 401: Unauthorized
        - 404: Alert not found
        - 500: Server error
    """
    try:
        # Validate update data
        update_data = request.model_dump(exclude_unset=True)

        if not update_data:
            raise AlertUpdateException("No fields provided to update")

        # Validate target_price if provided
        if "target_price" in update_data and update_data["target_price"] <= 0:
            raise AlertUpdateException("Target price must be greater than 0")

        alert = alert_service.update_alert(
            alert_id=alert_id,
            user_id=str(current_user["_id"]),
            update_data=update_data
        )

        if not alert:
            raise AlertNotFoundException(alert_id)

        logger.info(f"[ALERTS] Updated alert {alert_id} for user {current_user['email']}")
        return alert

    except (AlertNotFoundException, AlertUpdateException):
        raise
    except ValidationError as e:
        logger.error(f"[ALERTS] Update validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"[ALERTS] Error updating alert {alert_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update alert"
        )


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user),
    alert_service = Depends(get_alert_service)
):
    """
    Delete an alert.

    Args:
        alert_id: The alert ID to delete

    Raises:
        - 401: Unauthorized
        - 404: Alert not found
        - 500: Server error
    """
    try:
        success = alert_service.delete_alert(alert_id, str(current_user["_id"]))

        if not success:
            raise AlertNotFoundException(alert_id)

        logger.info(f"[ALERTS] Deleted alert {alert_id} for user {current_user['email']}")

    except AlertNotFoundException:
        raise
    except Exception as e:
        logger.error(f"[ALERTS] Error deleting alert {alert_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete alert"
        )


@router.post("/{alert_id}/test", status_code=status.HTTP_200_OK)
async def test_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user),
    alert_service = Depends(get_alert_service)
):
    """
    Send a test email for this alert.
    Useful for testing notification settings.

    Args:
        alert_id: The alert ID to test

    Returns:
        Success message with email address

    Raises:
        - 401: Unauthorized
        - 404: Alert not found
        - 500: Server error
    """
    try:
        alert = alert_service.get_alert(alert_id, str(current_user["_id"]))

        if not alert:
            raise AlertNotFoundException(alert_id)

        # Validate alert has required fields
        if not alert.token_symbol or not alert.target_price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Alert is missing required fields for test email"
            )

        # Create email service and send test
        email_service = EmailService()

        test_data = PriceAlertEmailData(
            user_email=current_user["email"],
            user_name=current_user.get("name", current_user["email"].split("@")[0]),
            token_symbol=alert.token_symbol,
            chain=alert.chain or "aptos",
            alert_type=alert.condition,
            target_price=alert.target_price,
            current_price=alert.target_price,  # Use target as current for test
            change_24h=5.0,
            change_percent=2.5,
            is_recurring=alert.is_recurring or False,
            alert_id=alert.id
        )

        success = email_service.send_price_alert(test_data)

        message = "Test email sent successfully" if success else "Test email logged (SMTP not configured)"
        logger.info(f"[ALERTS] Test email for alert {alert_id}: {message}")

        return {
            "message": message,
            "email": current_user["email"],
            "alert_id": alert_id
        }

    except AlertNotFoundException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ALERTS] Error sending test email for alert {alert_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test email"
        )


# ============================================================
# MANUAL ALERT CHECK (for testing)
# ============================================================

@router.post("/check-now", status_code=status.HTTP_200_OK)
async def check_alerts_now(
    current_user: dict = Depends(get_current_user),
    alert_service = Depends(get_alert_service)
):
    """
    Manually trigger alert checking for the current user.
    Useful for testing alerts without waiting for the scheduler.

    Returns:
        Number of alerts triggered

    Raises:
        - 401: Unauthorized
        - 500: Server error
    """
    try:
        user_id = str(current_user["_id"])

        # Check token alerts for this user
        triggered_count = await alert_service.check_token_alerts(user_id=user_id)

        logger.info(f"[ALERTS] Manual check for user {current_user['email']}: {triggered_count} alerts triggered")

        return {
            "message": f"Alert check complete. {triggered_count} alerts triggered.",
            "triggered_count": triggered_count,
            "user_email": current_user["email"]
        }

    except Exception as e:
        logger.error(f"[ALERTS] Error during manual alert check: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check alerts"
        )


# ============================================================
# EMAIL PREFERENCES
# ============================================================

@router.get("/preferences/email", response_model=EmailPreferencesResponse)
async def get_email_preferences(
    current_user: dict = Depends(get_current_user),
    prefs_service = Depends(get_email_preferences_service)
):
    """
    Get user's email notification preferences.

    Returns:
        Email preference settings

    Raises:
        - 401: Unauthorized
        - 500: Server error
    """
    try:
        prefs = prefs_service.get_preferences(str(current_user["_id"]))
        return prefs

    except Exception as e:
        logger.error(f"[ALERTS] Error fetching preferences for user {current_user['email']}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch email preferences"
        )


@router.put("/preferences/email", response_model=EmailPreferencesResponse)
async def update_email_preferences(
    request: EmailPreferencesRequest,
    current_user: dict = Depends(get_current_user),
    prefs_service = Depends(get_email_preferences_service)
):
    """
    Update email notification preferences.

    - **price_alerts_enabled**: Enable/disable price alert emails
    - **daily_digest_enabled**: Enable/disable daily portfolio digest
    - **weekly_summary_enabled**: Enable/disable weekly summary

    Args:
        request: Preference settings to update

    Returns:
        Updated preference settings

    Raises:
        - 401: Unauthorized
        - 422: Validation error
        - 500: Server error
    """
    try:
        preferences = request.model_dump(exclude_unset=True)

        if not preferences:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No preferences provided to update"
            )

        prefs = prefs_service.update_preferences(
            user_id=str(current_user["_id"]),
            user_email=current_user["email"],
            preferences=preferences
        )

        logger.info(f"[ALERTS] Updated email preferences for user {current_user['email']}")
        return prefs

    except HTTPException:
        raise
    except ValidationError as e:
        logger.error(f"[ALERTS] Preferences validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"[ALERTS] Error updating preferences: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update email preferences"
        )


# ============================================================
# PORTFOLIO SUGGESTIONS
# ============================================================

@router.get("/suggestions", status_code=status.HTTP_200_OK)
async def get_portfolio_suggestions(
    current_user: dict = Depends(get_current_user),
    alert_service = Depends(get_alert_service)
):
    """
    Get rule-based portfolio rebalancing suggestions.
    Analyzes the user's portfolio and suggests actions to improve stability.

    Returns:
        List of suggestion objects with action, reason, and priority
    """
    try:
        suggestions = await alert_service.get_portfolio_suggestions(
            user_id=str(current_user["_id"])
        )
        return {"suggestions": suggestions}

    except Exception as e:
        logger.error(f"[ALERTS] Error generating suggestions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate portfolio suggestions"
        )
