# app/services/migrations/add_chain_field.py
"""
Migration: Add 'chain' field to existing wallets

This script adds the 'chain' field to all existing wallets in the database.
All existing wallets are assumed to be Aptos wallets since that was the only
supported chain before this migration.

Run this ONCE after deploying multi-chain code.

Usage:
    cd backend
    python -m app.services.migrations.add_chain_field
"""

import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "chainiq")


def add_chain_field_to_wallets():
    """
    Add 'chain' field to all existing wallets.
    Sets chain='aptos' for all existing wallets.
    """
    
    print("=" * 60)
    print("🔄 MIGRATION: Add 'chain' field to wallets")
    print("=" * 60)
    
    try:
        # Connect to MongoDB
        print(f"\n📡 Connecting to MongoDB...")
        print(f"   URI: {MONGODB_URI[:30]}...")
        print(f"   Database: {MONGO_DB_NAME}")
        
        client = MongoClient(MONGODB_URI)
        db = client[MONGO_DB_NAME]
        wallets_collection = db["wallets"]
        
        # Test connection
        client.admin.command('ping')
        print("✅ Connected successfully!")
        
        # Count existing wallets
        total_wallets = wallets_collection.count_documents({})
        wallets_without_chain = wallets_collection.count_documents({"chain": {"$exists": False}})
        
        print(f"\n📊 Database Status:")
        print(f"   Total wallets: {total_wallets}")
        print(f"   Wallets without 'chain' field: {wallets_without_chain}")
        
        if wallets_without_chain == 0:
            print("\n✅ All wallets already have 'chain' field!")
            print("   No migration needed.")
            return
        
        # Ask for confirmation
        print(f"\n⚠️  This will add chain='aptos' to {wallets_without_chain} wallet(s).")
        response = input("   Continue? (yes/no): ").strip().lower()
        
        if response not in ['yes', 'y']:
            print("\n❌ Migration cancelled.")
            return
        
        # Perform migration
        print(f"\n🔄 Updating wallets...")
        
        result = wallets_collection.update_many(
            {"chain": {"$exists": False}},  # Only update wallets without chain field
            {"$set": {"chain": "aptos"}}     # Set chain to "aptos"
        )
        
        print(f"✅ Migration complete!")
        print(f"   Modified: {result.modified_count} wallet(s)")
        print(f"   Matched: {result.matched_count} wallet(s)")
        
        # Verify migration
        print(f"\n🔍 Verifying migration...")
        wallets_still_without_chain = wallets_collection.count_documents({"chain": {"$exists": False}})
        wallets_with_aptos = wallets_collection.count_documents({"chain": "aptos"})
        wallets_with_solana = wallets_collection.count_documents({"chain": "solana"})
        
        print(f"   Wallets without 'chain': {wallets_still_without_chain}")
        print(f"   Wallets with chain='aptos': {wallets_with_aptos}")
        print(f"   Wallets with chain='solana': {wallets_with_solana}")
        
        if wallets_still_without_chain == 0:
            print(f"\n✅ SUCCESS! All wallets now have 'chain' field.")
        else:
            print(f"\n⚠️  WARNING: {wallets_still_without_chain} wallet(s) still missing 'chain' field.")
        
        # Show sample wallets
        print(f"\n📋 Sample migrated wallets:")
        sample_wallets = wallets_collection.find({"chain": "aptos"}).limit(3)
        
        for i, wallet in enumerate(sample_wallets, 1):
            print(f"\n   {i}. Wallet:")
            print(f"      Address: {wallet.get('address', 'N/A')}")
            print(f"      Chain: {wallet.get('chain', 'N/A')}")
            print(f"      Type: {wallet.get('type', 'N/A')}")
            print(f"      Label: {wallet.get('label', 'N/A')}")
        
        print("\n" + "=" * 60)
        print("🎉 MIGRATION COMPLETE!")
        print("=" * 60)
        print("\n✅ You can now use multi-chain features!")
        print("✅ All existing wallets are set to chain='aptos'")
        print("✅ New wallets can be added with chain='solana'")
        
        client.close()
        
    except Exception as e:
        print(f"\n❌ MIGRATION FAILED!")
        print(f"   Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def rollback_migration():
    """
    Rollback migration by removing 'chain' field from all wallets.
    
    WARNING: This will remove the chain field from ALL wallets,
    including newly created Solana wallets!
    """
    
    print("=" * 60)
    print("⚠️  ROLLBACK: Remove 'chain' field from wallets")
    print("=" * 60)
    
    print("\n⚠️  WARNING: This will remove 'chain' field from ALL wallets!")
    print("   This includes any Solana wallets that were added.")
    print("   Only use this if you need to undo the migration.")
    
    response = input("\n   Are you SURE you want to rollback? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("\n❌ Rollback cancelled.")
        return
    
    try:
        client = MongoClient(MONGODB_URI)
        db = client[MONGO_DB_NAME]
        wallets_collection = db["wallets"]
        
        result = wallets_collection.update_many(
            {},  # All wallets
            {"$unset": {"chain": ""}}  # Remove chain field
        )
        
        print(f"\n✅ Rollback complete!")
        print(f"   Modified: {result.modified_count} wallet(s)")
        
        client.close()
        
    except Exception as e:
        print(f"\n❌ ROLLBACK FAILED!")
        print(f"   Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Add chain field to wallets")
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Rollback migration (remove chain field)"
    )
    
    args = parser.parse_args()
    
    if args.rollback:
        rollback_migration()
    else:
        add_chain_field_to_wallets()