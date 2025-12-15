# app/services/db.py
import os
from pymongo import MongoClient, ASCENDING
from pymongo.errors import CollectionInvalid

# ✅ FIXED: Changed MONGO_URI to MONGODB_URI to match your .env
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "chainiq")  # Changed default to "chainiq"

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

# Collections
users_collection = db["users"]
wallets_collection = db["wallets"]

# ============================================================
# Database Indexes (run on startup)
# ============================================================

def setup_indexes():
    """
    Create indexes for better query performance.
    Call this once on app startup or run manually.
    """
    try:
        print("[DB] Setting up indexes...")
        
        # Users: unique email index
        users_collection.create_index([("email", ASCENDING)], unique=True)
        print("[DB] ✅ Created index on users.email")
        
        # Users: created_at index for sorting
        users_collection.create_index([("created_at", ASCENDING)])
        print("[DB] ✅ Created index on users.created_at")
        
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
        
        print("[DB] 🎉 All indexes created successfully!")
        
    except Exception as e:
        print(f"[DB] ⚠️  Index creation note: {e}")

# Call setup_indexes() on import
setup_indexes()