# backend/app/routers/alerts.py - FIXED VERSION
"""
Alert API Endpoints - Token Price Alerts
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

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


router = APIRouter()


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
    """
    try:
        # Build alert data from request
        alert_data = {
            "token_symbol": request.token_symbol,
            "target_price": request.target_price,
            "condition": request.condition,
            "wallet_address": request.wallet_address,
            "chain": "aptos",  # Default chain
            "is_recurring": False  # One-time alert by default
        }
        
        alert = alert_service.create_alert(
            user_id=str(current_user["_id"]),
            user_email=current_user["email"],
            alert_data=alert_data
        )
        
        return alert
        
    except Exception as e:
        print(f"[ALERTS] Error creating alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create alert: {str(e)}"
        )


@router.get("/", response_model=List[AlertResponse])
async def get_alerts(
    current_user: dict = Depends(get_current_user),
    alert_service = Depends(get_alert_service)
):
    """Get all alerts for the current user"""
    try:
        alerts = alert_service.get_user_alerts(str(current_user["_id"]))
        return alerts
        
    except Exception as e:
        print(f"[ALERTS] Error fetching alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch alerts: {str(e)}"
        )


@router.get("/stats", response_model=AlertStatsResponse)
async def get_alert_stats(
    current_user: dict = Depends(get_current_user),
    alert_service = Depends(get_alert_service)
):
    """Get user's alert statistics"""
    try:
        stats = alert_service.get_alert_stats(str(current_user["_id"]))
        return AlertStatsResponse(**stats)
        
    except Exception as e:
        print(f"[ALERTS] Error fetching stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch stats: {str(e)}"
        )


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user),
    alert_service = Depends(get_alert_service)
):
    """Get a specific alert"""
    alert = alert_service.get_alert(alert_id, str(current_user["_id"]))
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    return alert


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
    - target_price
    - is_active (enable/disable)
    - condition
    """
    try:
        # Only update fields that are provided
        update_data = request.model_dump(exclude_unset=True)
        
        alert = alert_service.update_alert(
            alert_id=alert_id,
            user_id=str(current_user["_id"]),
            update_data=update_data
        )
        
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        return alert
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ALERTS] Error updating alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update alert: {str(e)}"
        )


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user),
    alert_service = Depends(get_alert_service)
):
    """Delete an alert"""
    success = alert_service.delete_alert(alert_id, str(current_user["_id"]))
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
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
    """
    alert = alert_service.get_alert(alert_id, str(current_user["_id"]))
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    try:
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
        
        if success:
            return {"message": "Test email sent successfully", "email": current_user["email"]}
        else:
            return {"message": "Test email logged (SMTP not configured)", "email": current_user["email"]}
        
    except Exception as e:
        print(f"[ALERTS] Error sending test email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test email: {str(e)}"
        )


# ============================================================
# EMAIL PREFERENCES
# ============================================================

@router.get("/preferences/email", response_model=EmailPreferencesResponse)
async def get_email_preferences(
    current_user: dict = Depends(get_current_user),
    prefs_service = Depends(get_email_preferences_service)
):
    """Get user's email notification preferences"""
    try:
        prefs = prefs_service.get_preferences(str(current_user["_id"]))
        return prefs
        
    except Exception as e:
        print(f"[ALERTS] Error fetching preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch preferences: {str(e)}"
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
    """
    try:
        prefs = prefs_service.update_preferences(
            user_id=str(current_user["_id"]),
            user_email=current_user["email"],
            preferences=request.model_dump(exclude_unset=True)
        )
        return prefs
        
    except Exception as e:
        print(f"[ALERTS] Error updating preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update preferences: {str(e)}"
        )