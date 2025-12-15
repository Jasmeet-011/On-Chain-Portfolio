#!/usr/bin/env python3
"""
Migration script to move embedded wallets from users collection to wallets collection.
Run this ONCE after deploying the new wallet service.

Usage:
    python migrate_wallets.py
"""

import sys
import os

# Add parent directory to path so we can import from app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.db import users_collection, setup_indexes
from app.services.wallet_service import migrate_user_wallets

def main():
    print("=" * 60)
    print("Wallet Migration Script")
    print("=" * 60)
    
    # Setup indexes first
    print("\n[1/3] Setting up database indexes...")
    setup_indexes()
    
    # Get all users
    print("\n[2/3] Fetching users...")
    users = list(users_collection.find({}))
    print(f"Found {len(users)} users")
    
    if len(users) == 0:
        print("\nNo users found. Nothing to migrate.")
        return
    
    # Migrate each user's wallets
    print("\n[3/3] Migrating wallets...")
    total_migrated = 0
    users_with_wallets = 0
    
    for user in users:
        user_id = str(user["_id"])
        embedded_wallets = user.get("wallets", [])
        
        if embedded_wallets:
            print(f"\nUser: {user.get('email', 'unknown')} ({user_id})")
            print(f"  Found {len(embedded_wallets)} embedded wallets")
            
            migrated = migrate_user_wallets(user_id)
            total_migrated += migrated
            
            if migrated > 0:
                users_with_wallets += 1
                print(f"  ✓ Migrated {migrated} wallets")
            else:
                print(f"  ⚠ No wallets migrated (may already exist)")
    
    # Summary
    print("\n" + "=" * 60)
    print("Migration Complete!")
    print("=" * 60)
    print(f"Total users processed: {len(users)}")
    print(f"Users with wallets: {users_with_wallets}")
    print(f"Total wallets migrated: {total_migrated}")
    print("\n✓ Migration successful!")
    print("\nNote: Old embedded wallets are kept in users collection for safety.")
    print("You can manually remove the 'wallets' field from users after verifying.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nMigration cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)