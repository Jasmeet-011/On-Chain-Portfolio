# app/main.py
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from .routers import health, balances, prices, portfolio, chat, transactions, history, alerts ,nfts, insights
from .routers.auth import router as auth_router
from .routers.wallets import router as wallets_router
from .services.db import setup_indexes
from .services.wallet_service import migrate_all_users

app = FastAPI(
    title="On-Chain Portfolio API",
    version="0.4.0",
    description="Multi-chain portfolio tracker with price alerts"
)

# ============================================================
# Startup Event - Database, Migration & Alert System
# ============================================================

@app.on_event("startup")
async def startup_event():
    """Run database setup, migrations, and initialize alert system on app startup."""
    print("\n" + "=" * 60)
    print("🚀 STARTING CHAINIQ BACKEND")
    print("=" * 60)
    
    # Database connection and indexes (auto-created in db.py)
    print("\n[STARTUP] ✅ Database connected")
    print("[STARTUP] ✅ Indexes created")
    
    # Migrate existing users' wallets
    print("\n[STARTUP] 🔄 Migrating embedded wallets to collection...")
    try:
        migration_stats = migrate_all_users()
        
        if "error" in migration_stats:
            print(f"[STARTUP] ⚠️  Migration had errors: {migration_stats['error']}")
        else:
            print(f"[STARTUP] ✅ Migration complete!")
            print(f"[STARTUP]    - Total users: {migration_stats.get('total_users', 0)}")
            print(f"[STARTUP]    - Users with embedded wallets: {migration_stats.get('users_with_wallets', 0)}")
            print(f"[STARTUP]    - Wallets migrated: {migration_stats.get('total_wallets_migrated', 0)}")
    except Exception as e:
        print(f"[STARTUP] ⚠️  Migration failed: {e}")
        print("[STARTUP] App will continue but embedded wallets may not work correctly")
    
    # Initialize Alert System
    print("\n[STARTUP] 🔔 Initializing alert system...")
    try:
        from app.deps import get_alert_service
        from app.services.scheduler import AlertScheduler
        
        alert_service = get_alert_service()
        scheduler = AlertScheduler(alert_service)
        scheduler.start()
        
        # Store in app state for access in endpoints
        app.state.alert_service = alert_service
        app.state.scheduler = scheduler
        
        print("[STARTUP] ✅ Alert system initialized")
        print("[STARTUP] ✅ Scheduler started (checks every 5 minutes)")
    except Exception as e:
        print(f"[STARTUP] ⚠️  Alert system failed to start: {e}")
        print("[STARTUP] App will continue but alerts will not work")
    
    print("\n" + "=" * 60)
    print("✅ APPLICATION READY!")
    print("=" * 60)
    print("📚 API Docs: http://localhost:8000/docs")
    print("💚 Health Check: http://localhost:8000/health")
    print("🔔 Alerts: http://localhost:8000/v1/alerts")
    print("=" * 60 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if hasattr(app.state, "scheduler"):
        app.state.scheduler.stop()
    print("[SHUTDOWN] ✅ Alert system stopped")

# ============================================================
# CORS Middleware
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
# ============================================================
# Authentication & Wallet Management
# ============================================================

app.include_router(auth_router)
app.include_router(wallets_router, prefix="/v1")

# ============================================================
# Root & Info
# ============================================================

@app.get("/", include_in_schema=False)
def root():
    """Redirect root to API documentation"""
    return RedirectResponse(url="/docs")


@app.get("/info", tags=["info"])
def get_info():
    """Get API information and endpoints"""
    return {
        "name": "On-Chain Portfolio API",
        "version": "0.4.0",
        "description": "Multi-chain portfolio tracker with price alerts",
        "features": [
            "JWT Authentication",
            "Multi-chain support (Aptos, Solana)",
            "Multiple wallet management",
            "Portfolio aggregation across wallets",
            "AI-powered portfolio chat",
            "Transaction history with filters",
            "Real-time token prices",
            "Historical charts",
            "Price alerts with email notifications"
        ],
        "endpoints": {
            "auth": "/auth",
            "wallets": "/v1/wallets",
            "chat": "/v1/chat",
            "portfolio": "/v1/portfolio",
            "transactions": "/v1/wallets/{address}/transactions",
            "history": "/v1/history",
            "alerts": "/v1/alerts",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }