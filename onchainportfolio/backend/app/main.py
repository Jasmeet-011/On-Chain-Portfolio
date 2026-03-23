# app/main.py
import os
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .routers import health, balances, prices, portfolio, chat, transactions, history, alerts, nfts, insights, chains
from .routers.auth import router as auth_router
from .routers.wallets import router as wallets_router
from .routers.telegram import router as telegram_router
from .services.db import setup_indexes
from .services.migrations.runner import run_migrations
from .limiter import limiter

app = FastAPI(
    title="On-Chain Portfolio API",
    version="0.4.0",
    description="Multi-chain portfolio tracker with price alerts"
)

# ============================================================
# Rate Limiting
# ============================================================

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ============================================================
# Startup Event - Database, Migration & Alert System
# ============================================================

@app.on_event("startup")
async def startup_event():
    """Run database setup, migrations, and initialize alert system on app startup."""
    print("\n" + "=" * 60)
    print("STARTING CHAINLENS BACKEND")
    print("=" * 60)

    # Initialize Cache (Redis or in-memory fallback)
    print("\n[STARTUP] Initializing cache...")
    try:
        from app.services.cache import initialize_cache, cache
        initialize_cache()
        print(f"[STARTUP] Cache initialized ({cache.backend_name} backend)")
    except Exception as e:
        print(f"[STARTUP] Cache initialization failed: {e}")
        print("[STARTUP] Using in-memory cache fallback")

    # Database connection and indexes (auto-created in db.py)
    print("\n[STARTUP] Database connected")
    print("[STARTUP] Indexes created")

    # Run one-shot database migrations (each runs only once, tracked in DB)
    print("\n[STARTUP] Running migrations...")
    try:
        run_migrations()
        print("[STARTUP] Migrations complete")
    except Exception as e:
        print(f"[STARTUP] Migration runner failed: {e}")
        print("[STARTUP] App will continue — check logs for migration details")

    # Initialize Alert System
    print("\n[STARTUP] Initializing alert system...")
    try:
        from app.deps import get_alert_service
        from app.services.scheduler import AlertScheduler

        alert_service = get_alert_service()
        scheduler = AlertScheduler(alert_service)
        scheduler.start()

        # Store in app state for access in endpoints
        app.state.alert_service = alert_service
        app.state.scheduler = scheduler

        print("[STARTUP] Alert system initialized")
        print("[STARTUP] Scheduler started (checks every 5 minutes)")
    except Exception as e:
        print(f"[STARTUP] Alert system failed to start: {e}")
        print("[STARTUP] App will continue but alerts will not work")

    # Start Telegram Bot (optional — requires TELEGRAM_BOT_TOKEN)
    print("\n[STARTUP] Checking Telegram bot...")
    try:
        from app.config import settings as cfg
        from app.services.telegram_bot import init_bot

        if cfg.telegram_enabled and cfg.telegram_bot_token:
            bot = init_bot(cfg.telegram_bot_token)
            await bot.start()
            app.state.telegram_bot = bot
            print("[STARTUP] Telegram bot started (polling mode)")
        else:
            print("[STARTUP] Telegram bot disabled (TELEGRAM_BOT_TOKEN not set)")
    except Exception as e:
        print(f"[STARTUP] Telegram bot failed to start: {e}")
        print("[STARTUP] App will continue without Telegram support")

    print("\n" + "=" * 60)
    print("APPLICATION READY")
    print("=" * 60)
    print("API Docs: http://localhost:8000/docs")
    print("Health:   http://localhost:8000/health")
    print("=" * 60 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if hasattr(app.state, "scheduler"):
        app.state.scheduler.stop()
    print("[SHUTDOWN] Alert system stopped")
    if hasattr(app.state, "telegram_bot"):
        await app.state.telegram_bot.stop()
    print("[SHUTDOWN] Telegram bot stopped")

# ============================================================
# CORS Middleware
# ============================================================
# Set CORS_ORIGINS in your environment as a comma-separated list.
# Example: CORS_ORIGINS=https://my-app.vercel.app,http://localhost:5173
# Defaults to localhost dev origins only.

_cors_env = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173"
)
_allowed_origins = [o.strip() for o in _cors_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With"],
)

# ============================================================
# Health Check
# ============================================================

app.include_router(health.router, tags=["health"])

# ============================================================
# V1 API Endpoints
# ============================================================

app.include_router(balances.router, prefix="/v1", tags=["wallets"])
app.include_router(prices.router, prefix="/v1", tags=["prices"])
app.include_router(portfolio.router, prefix="/v1", tags=["portfolio"])
app.include_router(chat.router, prefix="/v1", tags=["chat"])
app.include_router(transactions.router, prefix="/v1", tags=["transactions"])
app.include_router(history.router, prefix="/v1/history", tags=["history"])
app.include_router(alerts.router, prefix="/v1/alerts", tags=["alerts"])
app.include_router(nfts.router, prefix="/v1/nfts", tags=["nfts"])
app.include_router(insights.router, prefix="/v1/insights", tags=["insights"])
app.include_router(chains.router, prefix="/v1", tags=["chains"])

# ============================================================
# Authentication & Wallet Management
# ============================================================

app.include_router(auth_router)
app.include_router(wallets_router, prefix="/v1")

# ============================================================
# Telegram Bot Integration
# ============================================================

app.include_router(telegram_router, prefix="/v1/telegram", tags=["telegram"])

# ============================================================
# Root
# ============================================================

@app.get("/", include_in_schema=False)
def root():
    """Redirect root to API documentation"""
    return RedirectResponse(url="/docs")
