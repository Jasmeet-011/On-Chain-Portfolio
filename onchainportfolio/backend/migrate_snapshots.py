# backend/migrate_snapshots.py
"""
Migration Script: Create Initial Snapshots

Run this once to create the first snapshot for all existing users.
This gives them immediate historical data instead of waiting for daily cron.

Usage:
    cd backend
    python migrate_snapshots.py
    
    # Or for specific user:
    python migrate_snapshots.py --user-id USER_ID_HERE
"""
import asyncio
import sys

from app.services.db import snapshots_collection, wallets_collection
from app.services.snapshot_service import SnapshotService
from app.deps import price_service


async def migrate_all_users():
    """Create initial snapshot for all users."""
    
    print("\n" + "="*70)
    print("📸 SNAPSHOT MIGRATION - Creating Initial Snapshots")
    print("="*70 + "\n")
    
    # Initialize snapshot service
    snapshot_service = SnapshotService(
        snapshots_collection=snapshots_collection,
        wallets_collection=wallets_collection,
        price_service=price_service
    )
    
    # Get all unique user IDs
    user_ids = wallets_collection.distinct("user_id")
    
    print(f"Found {len(user_ids)} users with wallets\n")
    
    created_count = 0
    failed_count = 0
    skipped_count = 0
    
    for i, user_id in enumerate(user_ids, 1):
        print(f"[{i}/{len(user_ids)}] Processing user: {user_id}")
        
        try:
            snapshot_id = await snapshot_service.save_daily_snapshot(
                user_id=user_id,
                force=False  # Skip if snapshot already exists
            )
            
            if snapshot_id:
                created_count += 1
                print(f"  ✅ Created snapshot: {snapshot_id}\n")
            else:
                skipped_count += 1
                print(f"  ⏭️  Skipped (snapshot already exists)\n")
        
        except Exception as e:
            failed_count += 1
            print(f"  ❌ Failed: {e}\n")
    
    print("\n" + "="*70)
    print("MIGRATION COMPLETE")
    print("="*70)
    print(f"✅ Created:  {created_count}")
    print(f"⏭️  Skipped:  {skipped_count}")
    print(f"❌ Failed:   {failed_count}")
    print(f"📊 Total:    {len(user_ids)}")
    print("="*70 + "\n")
    
    # Show snapshot stats
    stats = snapshot_service.get_snapshot_stats()
    print("Snapshot Statistics:")
    print(f"  Total snapshots: {stats['total_snapshots']}")
    print(f"  Users with snapshots: {stats['users_with_snapshots']}")
    print(f"  Average portfolio value: ${stats['average_value_usd']:,.2f}")
    print(f"  Storage used: {stats['total_storage_mb']:.2f} MB")
    print()


async def create_snapshot_for_user(user_id: str):
    """Create snapshot for a specific user (manual trigger)."""
    
    print(f"\n📸 Creating snapshot for user: {user_id}\n")
    
    snapshot_service = SnapshotService(
        snapshots_collection=snapshots_collection,
        wallets_collection=wallets_collection,
        price_service=price_service
    )
    
    try:
        snapshot_id = await snapshot_service.save_daily_snapshot(
            user_id=user_id,
            force=True  # Force creation even if exists
        )
        
        if snapshot_id:
            print(f"\n✅ Snapshot created: {snapshot_id}\n")
        else:
            print(f"\n⚠️  Snapshot creation failed or skipped\n")
    
    except Exception as e:
        print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Portfolio Snapshot Migration")
    parser.add_argument(
        "--user-id",
        help="Create snapshot for specific user ID only",
        default=None
    )
    
    args = parser.parse_args()
    
    if args.user_id:
        asyncio.run(create_snapshot_for_user(args.user_id))
    else:
        asyncio.run(migrate_all_users())