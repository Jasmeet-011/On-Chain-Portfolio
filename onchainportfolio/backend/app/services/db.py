# app/services/db.py - COMPLETE VERSION with Alert System
"""
MongoDB Database Connection and Collections
All collections are defined here for easy import across the app.
"""
import os
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import CollectionInvalid

# ============================================================
# DATABASE CONNECTION
# ============================================================

# ✅ Support both MONGODB_URI and MONGO_URI for flexibility
MONGODB_URI = os.getenv("MONGODB_URI", os.getenv("MONGO_URI", "mongodb://localhost:27017"))
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", os.getenv("DATABASE_NAME", "chainiq"))

print(f"[DB] Connecting to MongoDB...")
print(f"[DB] Database: {MONGO_DB_NAME}")

try:
    client = MongoClient(MONGODB_URI)
    # Test connection
    client.admin.command('ping')
    print(f"[DB] ✅ Successfully connected to MongoDB!")
except Exception as e:
    print(f"[DB] ❌ Failed to connect to MongoDB: {e}")
    raise

db = client[MONGO_DB_NAME]


# ============================================================
# USER & WALLET COLLECTIONS
# ============================================================

users_collection = db["users"]
wallets_collection = db["wallets"]


# ============================================================
# ALERT SYSTEM COLLECTIONS
# ============================================================

alerts_collection = db["alerts"]
email_preferences_collection = db["email_preferences"]
alert_history_collection = db["alert_history"]


# ============================================================
# PORTFOLIO & ANALYTICS COLLECTIONS
# ============================================================

snapshots_collection = db["snapshots"]
portfolio_snapshots_collection = db["portfolio_snapshots"]
price_history_collection = db["price_history"]


# ============================================================
# NFT COLLECTIONS
# ============================================================

nfts_collection = db["nfts"]


# ============================================================
# PORTFOLIO EVENT LOG
# ============================================================

portfolio_events_collection = db["portfolio_events"]


# ============================================================
# MIGRATION TRACKING
# ============================================================

migrations_collection = db["migrations"]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_db():
    """Get database instance."""
    return db


def health_check() -> dict:
    """Check database health"""
    try:
        client.admin.command('ping')
        return {
            "status": "healthy",
            "database": MONGO_DB_NAME,
            "collections": db.list_collection_names()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# ============================================================
# DATABASE INDEXES
# ============================================================

def setup_indexes():
    """
    Create indexes for better query performance.
    Called automatically on startup.
    """
    try:
        print("[DB] Setting up indexes...")
        
        # ============================================================
        # USER INDEXES
        # ============================================================
        
        # Users: unique email index
        users_collection.create_index([("email", ASCENDING)], unique=True)
        print("[DB] ✅ Created index on users.email")
        
        # Users: created_at index for sorting
        users_collection.create_index([("created_at", ASCENDING)])
        print("[DB] ✅ Created index on users.created_at")
        
        # ============================================================
        # WALLET INDEXES
        # ============================================================
        
        # Wallets: user_id index (for fetching user's wallets)
        wallets_collection.create_index([("user_id", ASCENDING)])
        print("[DB] ✅ Created index on wallets.user_id")
        
        # Wallets: address index (for checking duplicates, faster lookups)
        wallets_collection.create_index([("address", ASCENDING)])
        print("[DB] ✅ Created index on wallets.address")
        
        # Wallets: compound index for user_id + address (unique per user)
        wallets_collection.create_index(
            [("user_id", ASCENDING), ("address", ASCENDING)], 
            unique=True
        )
        print("[DB] ✅ Created unique compound index on wallets.user_id+address")
        
        # Wallets: index for finding primary wallet
        wallets_collection.create_index(
            [("user_id", ASCENDING), ("is_primary", ASCENDING)]
        )
        print("[DB] ✅ Created index on wallets.user_id+is_primary")
        
        # Wallets: index for wallet type
        wallets_collection.create_index([("type", ASCENDING)])
        print("[DB] ✅ Created index on wallets.type")
        
        # Wallets: index for chain
        wallets_collection.create_index([("chain", ASCENDING)])
        print("[DB] ✅ Created index on wallets.chain")
        
        # ============================================================
        # ALERT INDEXES
        # ============================================================
        
        # Alerts: user_id index (for fetching user's alerts)
        alerts_collection.create_index([("user_id", ASCENDING)])
        print("[DB] ✅ Created index on alerts.user_id")
        
        # Alerts: user_id + is_active (for fetching active alerts)
        alerts_collection.create_index([
            ("user_id", ASCENDING),
            ("is_active", ASCENDING)
        ])
        print("[DB] ✅ Created index on alerts.user_id+is_active")
        
        # Alerts: token_symbol index (for price checking)
        alerts_collection.create_index([("token_symbol", ASCENDING)])
        print("[DB] ✅ Created index on alerts.token_symbol")
        
        # Alerts: last_triggered index (for sorting/filtering)
        alerts_collection.create_index([("last_triggered", DESCENDING)])
        print("[DB] ✅ Created index on alerts.last_triggered")
        
        # Alerts: created_at index (for sorting newest first)
        alerts_collection.create_index([("created_at", DESCENDING)])
        print("[DB] ✅ Created index on alerts.created_at")
        
        # Alerts: compound index for active alerts by token (for cron job)
        alerts_collection.create_index([
            ("is_active", ASCENDING),
            ("token_symbol", ASCENDING),
            ("chain", ASCENDING)
        ])
        print("[DB] ✅ Created index on alerts.is_active+token_symbol+chain")
        
        # Alerts: status index for filtering
        alerts_collection.create_index([("status", ASCENDING)])
        print("[DB] ✅ Created index on alerts.status")
        
        # ============================================================
        # EMAIL PREFERENCES INDEXES
        # ============================================================
        
        # Email Preferences: unique user_id index
        email_preferences_collection.create_index([("user_id", ASCENDING)], unique=True)
        print("[DB] ✅ Created unique index on email_preferences.user_id")
        
        # ============================================================
        # SNAPSHOT INDEXES
        # ============================================================
        
        # Snapshots: user_id + snapshot_date (most common query)
        snapshots_collection.create_index([
            ("user_id", ASCENDING),
            ("snapshot_date", DESCENDING)
        ])
        print("[DB] ✅ Created index on snapshots.user_id+snapshot_date")
        
        # Snapshots: user_id + wallet_id + snapshot_date (for per-wallet history)
        snapshots_collection.create_index([
            ("user_id", ASCENDING),
            ("wallet_id", ASCENDING),
            ("snapshot_date", DESCENDING)
        ])
        print("[DB] ✅ Created index on snapshots.user_id+wallet_id+snapshot_date")
        
        # Snapshots: unique constraint (one snapshot per user/wallet/date)
        try:
            snapshots_collection.create_index([
                ("user_id", ASCENDING),
                ("wallet_id", ASCENDING),
                ("snapshot_date", ASCENDING)
            ], unique=True)
            print("[DB] ✅ Created unique index on snapshots.user_id+wallet_id+snapshot_date")
        except Exception as e:
            print(f"[DB] ⚠️  Snapshot unique index already exists or error: {e}")
        
        # Snapshots: snapshot_date for cleanup queries
        snapshots_collection.create_index([("snapshot_date", ASCENDING)])
        print("[DB] ✅ Created index on snapshots.snapshot_date")
        
        # ============================================================
        # PORTFOLIO SNAPSHOTS INDEXES
        # ============================================================
        
        portfolio_snapshots_collection.create_index([
            ("user_id", ASCENDING),
            ("timestamp", DESCENDING)
        ])
        print("[DB] ✅ Created index on portfolio_snapshots.user_id+timestamp")
        
        # ============================================================
        # PRICE HISTORY INDEXES
        # ============================================================
        
        price_history_collection.create_index([
            ("symbol", ASCENDING),
            ("chain", ASCENDING),
            ("timestamp", DESCENDING)
        ])
        print("[DB] ✅ Created index on price_history.symbol+chain+timestamp")
        
        # TTL index: auto-delete after 30 days
        try:
            price_history_collection.create_index(
                "timestamp", 
                expireAfterSeconds=60*60*24*30
            )
            print("[DB] ✅ Created TTL index on price_history.timestamp (30 days)")
        except Exception as e:
            print(f"[DB] ⚠️  Price history TTL index: {e}")
        
        # ============================================================
        # NFT INDEXES
        # ============================================================
        
        nfts_collection.create_index([("user_id", ASCENDING)])
        nfts_collection.create_index([("wallet_address", ASCENDING)])
        print("[DB] ✅ Created indexes on nfts collection")

        # ============================================================
        # PORTFOLIO EVENTS INDEXES
        # ============================================================

        # Fast lookup: all events for a user, sorted by time
        portfolio_events_collection.create_index([
            ("user_id", ASCENDING),
            ("timestamp", DESCENDING)
        ])
        print("[DB] ✅ Created index on portfolio_events.user_id+timestamp")

        # Filter by event type
        portfolio_events_collection.create_index([
            ("user_id", ASCENDING),
            ("event_type", ASCENDING),
            ("timestamp", DESCENDING)
        ])
        print("[DB] ✅ Created index on portfolio_events.user_id+event_type+timestamp")

        # ============================================================
        # MIGRATIONS INDEXES
        # ============================================================

        migrations_collection.create_index([("name", ASCENDING)], unique=True)
        print("[DB] ✅ Created unique index on migrations.name")

        print("[DB] 🎉 All indexes created successfully!")
        
    except Exception as e:
        print(f"[DB] ⚠️  Index creation note: {e}")


# ============================================================
# RUN SETUP ON IMPORT
# ============================================================

setup_indexes()

print(f"[DB] Collections initialized:")
print(f"  - users_collection")
print(f"  - wallets_collection")
print(f"  - alerts_collection")
print(f"  - email_preferences_collection")
print(f"  - alert_history_collection")
print(f"  - snapshots_collection")
print(f"  - portfolio_snapshots_collection")
print(f"  - price_history_collection")
print(f"  - nfts_collection")
print(f"  - portfolio_events_collection")
print(f"  - migrations_collection")