# backend/app/services/telegram_bot.py
"""
ChainLens Telegram Bot
- Polling mode (works locally and on Railway without a public URL)
- Commands: /start, /help, /link <code>, /portfolio, /balance, /price <sym>, /alerts, /unlink
- Link flow: user generates a 6-char code in the web app → sends /link <code> to bot
"""
import asyncio
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from app.services.db import users_collection
from app.services.wallet_service import list_user_wallets
from app.services.adapters import get_adapter_for_chain, SUPPORTED_CHAINS

logger = logging.getLogger(__name__)


# ============================================================
# LINK TOKEN STORE
# Short-lived tokens linking the web-app user → Telegram chat.
# Format: { "ABC123": {"user_id": "...", "expires_at": datetime} }
# ============================================================
_link_tokens: dict[str, dict] = {}


def generate_link_token(user_id: str) -> str:
    """
    Generate a 6-char alphanumeric link token for a user.
    Valid for 15 minutes.  Replaces any existing token for this user.
    """
    # Remove any existing token belonging to this user
    _link_tokens.update(
        {k: v for k, v in _link_tokens.items() if v["user_id"] != user_id}
    )

    token = secrets.token_hex(3).upper()  # 6 uppercase hex chars
    _link_tokens[token] = {
        "user_id": user_id,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=15),
    }
    return token


def consume_link_token(token: str) -> Optional[str]:
    """
    Validate and consume a link token.  Returns the user_id on success, None otherwise.
    """
    entry = _link_tokens.get(token.upper())
    if not entry:
        return None
    if datetime.now(timezone.utc) > entry["expires_at"]:
        del _link_tokens[token.upper()]
        return None
    del _link_tokens[token.upper()]
    return entry["user_id"]


# ============================================================
# PORTFOLIO HELPER
# ============================================================

def _fetch_portfolio_text(user_id: str, max_wallets: int = 6) -> str:
    """
    Fetch wallet balances and format as a Telegram-friendly text block.
    Runs synchronously — called inside asyncio.to_thread() from bot handlers.
    """
    try:
        wallets = list_user_wallets(user_id)
    except Exception as e:
        logger.error(f"[TG] Failed to list wallets: {e}")
        return "⚠️ Could not fetch your wallets."

    if not wallets:
        return "You have no wallets connected. Add them at chainlens.app."

    lines = ["📊 *Portfolio Summary*\n"]
    grand_total = 0.0

    for wallet in wallets[:max_wallets]:
        address = wallet.get("address", "")
        chain = wallet.get("chain", "aptos")
        label = wallet.get("label", "Wallet")

        if chain not in SUPPORTED_CHAINS:
            lines.append(f"• {label} ({chain.upper()}) — unsupported chain")
            continue

        try:
            adapter = get_adapter_for_chain(chain)
            balances = adapter.get_token_balances(address)
        except Exception as e:
            lines.append(f"• {label} ({chain.upper()}) — fetch error")
            logger.warning(f"[TG] balance fetch error for {address}: {e}")
            continue

        wallet_total = 0.0
        token_lines = []
        for b in balances:
            amt = b.get("amount", 0)
            sym = b.get("symbol", "?")
            usd = b.get("usd_value", 0) or 0
            wallet_total += usd
            if amt > 0:
                usd_str = f"  (${usd:,.2f})" if usd else ""
                token_lines.append(f"    {sym}: {amt:,.4f}{usd_str}")

        grand_total += wallet_total
        short_addr = address[:6] + "…" + address[-4:] if len(address) > 12 else address
        lines.append(
            f"• *{label}* ({chain.upper()}) — `{short_addr}`\n"
            f"  Total: ${wallet_total:,.2f}"
        )
        lines.extend(token_lines)
        lines.append("")

    if len(wallets) > max_wallets:
        lines.append(f"_…and {len(wallets) - max_wallets} more wallet(s). See app for full view._")

    lines.append(f"\n💰 *Grand Total: ${grand_total:,.2f}*")
    return "\n".join(lines)


# ============================================================
# BOT CLASS
# ============================================================

class TelegramBot:
    """Thin wrapper around python-telegram-bot Application for lifecycle management."""

    def __init__(self, token: str):
        self.token = token
        self.application: Optional[Application] = None

    async def start(self):
        """Build the application, register handlers, and begin polling."""
        self.application = Application.builder().token(self.token).build()

        app = self.application
        app.add_handler(CommandHandler("start", self._cmd_start))
        app.add_handler(CommandHandler("help", self._cmd_help))
        app.add_handler(CommandHandler("link", self._cmd_link))
        app.add_handler(CommandHandler("unlink", self._cmd_unlink))
        app.add_handler(CommandHandler("portfolio", self._cmd_portfolio))
        app.add_handler(CommandHandler("balance", self._cmd_portfolio))  # alias
        app.add_handler(CommandHandler("price", self._cmd_price))
        app.add_handler(CommandHandler("alerts", self._cmd_alerts))

        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        logger.info("[TG] Bot started (polling mode)")

    async def stop(self):
        """Gracefully stop polling and shut down."""
        if self.application:
            try:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                logger.info("[TG] Bot stopped")
            except Exception as e:
                logger.error(f"[TG] Error stopping bot: {e}")

    # ----------------------------------------------------------------
    # Auth helper
    # ----------------------------------------------------------------

    def _get_user(self, chat_id: int) -> Optional[dict]:
        """Return the ChainLens user linked to this Telegram chat, or None."""
        return users_collection.find_one({"telegram_chat_id": chat_id})

    # ----------------------------------------------------------------
    # Handlers
    # ----------------------------------------------------------------

    async def _cmd_start(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        user = self._get_user(update.effective_chat.id)
        if user:
            name = user.get("name", "there")
            await update.message.reply_text(
                f"👋 Hey {name}! You're already linked.\n\n"
                "Try /portfolio to see your holdings or /help for all commands."
            )
        else:
            await update.message.reply_text(
                "👋 Welcome to *ChainLens Bot*!\n\n"
                "I can show your multi-chain portfolio right here in Telegram.\n\n"
                "*To get started:*\n"
                "1. Open ChainLens → Settings → Connect Telegram\n"
                "2. Copy your 6-digit link code\n"
                "3. Send me: `/link YOURCODE`\n\n"
                "Type /help to see all commands.",
                parse_mode="Markdown",
            )

    async def _cmd_help(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "📋 *ChainLens Bot Commands*\n\n"
            "/portfolio — View your full portfolio\n"
            "/balance — Alias for /portfolio\n"
            "/price `<symbol>` — Token price (e.g. `/price SOL`)\n"
            "/alerts — List your active alerts\n"
            "/link `<code>` — Link your ChainLens account\n"
            "/unlink — Disconnect your account\n"
            "/help — Show this message",
            parse_mode="Markdown",
        )

    async def _cmd_link(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id

        if not ctx.args:
            await update.message.reply_text(
                "Usage: /link `<6-digit code>`\n\n"
                "Get your code from ChainLens → Settings → Connect Telegram.",
                parse_mode="Markdown",
            )
            return

        token = ctx.args[0].strip()
        user_id = consume_link_token(token)

        if not user_id:
            await update.message.reply_text(
                "❌ Invalid or expired code. Please generate a new one in ChainLens Settings."
            )
            return

        # Store telegram_chat_id on the user document
        users_collection.update_one(
            {"_id": __import__("bson").ObjectId(user_id)},
            {"$set": {"telegram_chat_id": chat_id}},
        )

        user = users_collection.find_one({"telegram_chat_id": chat_id})
        name = user.get("name", "there") if user else "there"
        await update.message.reply_text(
            f"✅ Linked successfully! Hey {name} 👋\n\n"
            "Try /portfolio to see your holdings.",
        )

    async def _cmd_unlink(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        result = users_collection.update_one(
            {"telegram_chat_id": chat_id},
            {"$unset": {"telegram_chat_id": ""}},
        )
        if result.modified_count:
            await update.message.reply_text(
                "✅ Your Telegram account has been unlinked from ChainLens."
            )
        else:
            await update.message.reply_text(
                "ℹ️ No linked account found. Use /link to connect first."
            )

    async def _cmd_portfolio(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        user = self._get_user(update.effective_chat.id)
        if not user:
            await update.message.reply_text(
                "🔒 Please link your account first using /link `<code>`.",
                parse_mode="Markdown",
            )
            return

        await update.message.reply_text("⏳ Fetching your portfolio…")

        user_id = str(user["_id"])
        text = await asyncio.to_thread(_fetch_portfolio_text, user_id)
        await update.message.reply_text(text, parse_mode="Markdown")

    async def _cmd_price(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not ctx.args:
            await update.message.reply_text(
                "Usage: /price `<symbol>` — e.g. /price SOL",
                parse_mode="Markdown",
            )
            return

        symbol = ctx.args[0].upper()
        try:
            from app.deps import price_service
            price = await asyncio.to_thread(price_service.get_price, symbol)
            if price:
                await update.message.reply_text(
                    f"💵 *{symbol}* current price: *${price:,.4f}*",
                    parse_mode="Markdown",
                )
            else:
                await update.message.reply_text(
                    f"❓ Could not find price for *{symbol}*. Check the symbol and try again.",
                    parse_mode="Markdown",
                )
        except Exception as e:
            logger.error(f"[TG] price fetch error: {e}")
            await update.message.reply_text("⚠️ Failed to fetch price. Please try again.")

    async def _cmd_alerts(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        user = self._get_user(update.effective_chat.id)
        if not user:
            await update.message.reply_text(
                "🔒 Please link your account first using /link `<code>`.",
                parse_mode="Markdown",
            )
            return

        try:
            from app.services.db import alerts_collection
            user_id = str(user["_id"])
            cursor = alerts_collection.find(
                {"user_id": user_id, "is_active": True},
                {"token_symbol": 1, "condition": 1, "target_price": 1, "chain": 1},
            ).limit(10)
            alerts = list(cursor)
        except Exception as e:
            logger.error(f"[TG] alerts fetch error: {e}")
            await update.message.reply_text("⚠️ Failed to fetch alerts.")
            return

        if not alerts:
            await update.message.reply_text(
                "You have no active alerts. Set them up at chainlens.app."
            )
            return

        lines = ["🔔 *Your Active Alerts*\n"]
        for a in alerts:
            sym = a.get("token_symbol", "?")
            cond = a.get("condition", "above")
            price = a.get("target_price", 0)
            chain = a.get("chain", "")
            chain_str = f" ({chain.upper()})" if chain else ""
            arrow = "📈" if cond == "above" else "📉"
            lines.append(f"{arrow} {sym}{chain_str} {cond} ${price:,.4f}")

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ============================================================
# SINGLETON — imported by main.py and telegram router
# ============================================================
_bot_instance: Optional[TelegramBot] = None


def get_bot() -> Optional[TelegramBot]:
    return _bot_instance


def init_bot(token: str) -> TelegramBot:
    global _bot_instance
    _bot_instance = TelegramBot(token)
    return _bot_instance
