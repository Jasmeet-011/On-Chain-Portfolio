# app/main.py
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from .routers import health, balances, prices, portfolio, chat, transactions
from .routers.auth import router as auth_router
from .routers.wallets import router as wallets_router
from .services.db import setup_indexes  # This will now work with fixed db.py
from .services.wallet_service import migrate_all_users

app = FastAPI(
    title="On-Chain Portfolio API",
    version="0.3.0",
    description="Multi-wallet portfolio tracker for Aptos blockchain"
)

# ============================================================
# Startup Event - Database Setup & Migration
# ============================================================

@app.on_event("startup")
async def startup_event():
    """Run database setup and migrations on app startup."""
    print("\n" + "=" * 60)
    print("🚀 STARTING CHAINIQ BACKEND")
    print("=" * 60)
    
    # Step 1: Database connection is already established in db.py
    # The indexes are created automatically when db.py imports
    print("\n[STARTUP] ✅ Database connected")
    print("[STARTUP] ✅ Indexes created")
    
    # Step 2: Migrate existing users' wallets
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
    
    print("\n" + "=" * 60)
    print("✅ APPLICATION READY!")
    print("=" * 60)
    print("📚 API Docs: http://localhost:8000/docs")
    print("💚 Health Check: http://localhost:8000/health")
    print("=" * 60 + "\n")

# ============================================================
# CORS Middleware
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://*.vercel.app",  # For deployment
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

# ============================================================
# Authentication Endpoints
# ============================================================

app.include_router(auth_router)

# ============================================================
# Wallet Management Endpoints
# ============================================================

app.include_router(wallets_router, prefix="/v1")

# ============================================================
# Root Redirect
# ============================================================

@app.get("/", include_in_schema=False)
def root():
    """Redirect root to API documentation"""
    return RedirectResponse(url="/docs")

# ============================================================
# Additional Info Endpoint
# ============================================================

@app.get("/info", tags=["info"])
def get_info():
    """Get API information and endpoints"""
    return {
        "name": "On-Chain Portfolio API",
        "version": "0.3.0",
        "description": "Multi-wallet portfolio tracker for Aptos blockchain",
        "features": [
            "JWT Authentication",
            "Multiple wallet management",
            "Portfolio aggregation across wallets",
            "AI-powered portfolio chat",
            "Transaction history with filters",
            "Real-time token prices"
        ],
        "endpoints": {
            "auth": "/auth",
            "wallets": "/v1/wallets",
            "chat": "/v1/chat",
            "transactions": "/v1/wallets/{address}/transactions",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }