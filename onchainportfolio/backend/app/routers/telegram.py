# backend/app/routers/telegram.py
"""
Telegram Bot API Endpoints
- Generate link codes so users can connect their Telegram account
- Check link status / unlink
"""
from fastapi import APIRouter, Depends, HTTPException, status
import logging

from app.deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/generate-link", status_code=status.HTTP_200_OK)
async def generate_telegram_link(
    current_user: dict = Depends(get_current_user),
):
    """
    Generate a short-lived 6-char link code.
    The user sends /link <code> to the Telegram bot to connect their account.

    Returns:
        code: 6-char alphanumeric code (valid 15 min)
        bot_username: The bot's Telegram username (for the deep-link)
        expires_in_minutes: 15
    """
    try:
        from app.services.telegram_bot import generate_link_token
        from app.config import settings

        user_id = str(current_user["_id"])
        code = generate_link_token(user_id)

        return {
            "code": code,
            "expires_in_minutes": 15,
            "instructions": f"Open Telegram and send this message to the ChainLens bot:\n/link {code}",
        }

    except Exception as e:
        logger.error(f"[TG] Error generating link token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate link code",
        )


@router.get("/status", status_code=status.HTTP_200_OK)
async def get_telegram_status(
    current_user: dict = Depends(get_current_user),
):
    """
    Check whether the current user has linked their Telegram account.

    Returns:
        linked: bool
        chat_id: Telegram chat ID if linked, null otherwise
    """
    chat_id = current_user.get("telegram_chat_id")
    return {
        "linked": chat_id is not None,
        "chat_id": chat_id,
    }


@router.delete("/unlink", status_code=status.HTTP_200_OK)
async def unlink_telegram(
    current_user: dict = Depends(get_current_user),
):
    """
    Remove the Telegram link for the current user.
    """
    try:
        from app.services.db import users_collection
        import bson

        result = users_collection.update_one(
            {"_id": bson.ObjectId(str(current_user["_id"]))},
            {"$unset": {"telegram_chat_id": ""}},
        )

        if result.modified_count:
            return {"message": "Telegram account unlinked successfully"}
        else:
            return {"message": "No Telegram account was linked"}

    except Exception as e:
        logger.error(f"[TG] Error unlinking: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unlink Telegram account",
        )
