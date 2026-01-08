# backend/app/services/snapshot_service.py
"""
Portfolio Snapshot Service

Captures and retrieves historical portfolio snapshots for accurate charts.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict
from pymongo.collection import Collection
from bson import ObjectId

from app.services.price_service import PriceService
from app.models.snapshot_models import (
    PortfolioSnapshot,
    SnapshotBalance,
    SnapshotHistoryPoint,
    SnapshotHistoryResponse
)


class SnapshotService:
    """Service for managing portfolio snapshots"""
    
    def __init__(
        self,
        snapshots_collection: Collection,
        wallets_collection: Collection,
        price_service: PriceService
    ):
        self.snapshots = snapshots_collection
        self.wallets = wallets_collection
        self.price_service = price_service
        
        print("[SNAPSHOT] Snapshot service initialized")
    
    # ============================================================
    # SNAPSHOT CREATION
    # ============================================================
    
    async def save_daily_snapshot(
        self,
        user_id: str,
        wallet_id: Optional[str] = None,
        force: bool = False
    ) -> Optional[str]:
        """
        Save a portfolio snapshot for a user.
        
        Args:
            user_id: User ID
            wallet_id: Optional wallet ID (None = all wallets)
            force: Force creation even if snapshot exists today
        
        Returns:
            Snapshot ID if created, None if already exists
        """
        from app.services.adapters import get_adapter_for_chain
        import os
        
        print(f"[SNAPSHOT] Creating snapshot for user {user_id}")
        if wallet_id:
            print(f"[SNAPSHOT]   Wallet filter: {wallet_id}")
        
        # Get snapshot date (midnight UTC)
        now = datetime.utcnow()
        snapshot_date = datetime(now.year, now.month, now.day, 0, 0, 0)
        
        # Check if snapshot already exists
        if not force:
            existing = self.snapshots.find_one({
                "user_id": user_id,
                "wallet_id": wallet_id,
                "snapshot_date": snapshot_date
            })
            
            if existing:
                print(f"[SNAPSHOT] ⚠️  Snapshot already exists for {snapshot_date.date()}")
                return None
        
        # Get user wallets
        wallet_filter = {"user_id": user_id}
        if wallet_id:
            wallet_filter["_id"] = ObjectId(wallet_id)
        
        wallets = list(self.wallets.find(wallet_filter))
        
        if not wallets:
            print(f"[SNAPSHOT] ❌ No wallets found for user {user_id}")
            return None
        
        print(f"[SNAPSHOT] Found {len(wallets)} wallet(s)")
        
        # Fetch balances for each wallet
        all_balances: List[SnapshotBalance] = []
        total_value_usd = 0.0
        chain_breakdown: Dict[str, float] = {}
        tokens_seen = set()
        
        for wallet_doc in wallets:
            address = wallet_doc.get("address")
            chain = wallet_doc.get("chain", "aptos")
            
            print(f"[SNAPSHOT]   Processing {chain} wallet: {address[:8]}...")
            
            try:
                # Get adapter for chain
                rpc_url = os.getenv(
                    "APTOS_RPC_URL" if chain == "aptos" else "SOLANA_RPC_URL",
                    "https://fullnode.testnet.aptoslabs.com/v1"
                )
                adapter = get_adapter_for_chain(chain, rpc_url=rpc_url)
                
                # Fetch balances
                balances = adapter.get_token_balances(address)
                
                print(f"[SNAPSHOT]     Found {len(balances)} tokens")
                
                # Process each balance
                for balance in balances:
                    symbol = balance.get("symbol")
                    amount = balance.get("amount", 0)
                    
                    if not symbol or amount <= 0:
                        continue
                    
                    # Get price
                    try:
                        price_usd = self.price_service.get_price(symbol, chain=chain)
                        
                        if price_usd and price_usd > 0:
                            value_usd = float(amount) * float(price_usd)
                            
                            # Add to snapshot
                            all_balances.append(SnapshotBalance(
                                symbol=symbol,
                                amount=float(amount),
                                price_usd=float(price_usd),
                                value_usd=float(value_usd),
                                chain=chain
                            ))
                            
                            total_value_usd += value_usd
                            chain_breakdown[chain] = chain_breakdown.get(chain, 0) + value_usd
                            tokens_seen.add(symbol)
                            
                            print(f"[SNAPSHOT]       ✓ {symbol}: {amount} × ${price_usd} = ${value_usd:.2f}")
                        else:
                            print(f"[SNAPSHOT]       ✗ {symbol}: No price available")
                    
                    except Exception as price_err:
                        print(f"[SNAPSHOT]       ✗ {symbol}: Price fetch failed - {price_err}")
                        continue
            
            except Exception as wallet_err:
                print(f"[SNAPSHOT]     ❌ Failed to fetch wallet balances: {wallet_err}")
                continue
        
        if not all_balances:
            print(f"[SNAPSHOT] ❌ No valid balances found")
            return None
        
        # Create snapshot document
        snapshot = PortfolioSnapshot(
            user_id=user_id,
            wallet_id=wallet_id,
            snapshot_date=snapshot_date,
            timestamp=now,
            total_value_usd=round(total_value_usd, 2),
            total_tokens=len(tokens_seen),
            wallet_count=len(wallets),
            balances=all_balances,
            chain_breakdown=chain_breakdown
        )
        
        # Save to database
        snapshot_dict = snapshot.model_dump()
        result = self.snapshots.insert_one(snapshot_dict)
        
        print(f"[SNAPSHOT] ✅ Snapshot created:")
        print(f"[SNAPSHOT]   Total value: ${total_value_usd:.2f}")
        print(f"[SNAPSHOT]   Tokens: {len(tokens_seen)}")
        print(f"[SNAPSHOT]   Wallets: {len(wallets)}")
        print(f"[SNAPSHOT]   ID: {result.inserted_id}")
        
        return str(result.inserted_id)
    
    async def save_all_user_snapshots(self) -> int:
        """
        Save snapshots for all users (called by cron job).
        
        Returns:
            Number of snapshots created
        """
        print("\n" + "="*60)
        print("[SNAPSHOT] 📸 Starting daily snapshot job...")
        print("="*60)
        
        # Get all unique user IDs from wallets
        user_ids = self.wallets.distinct("user_id")
        
        print(f"[SNAPSHOT] Found {len(user_ids)} users with wallets")
        
        created_count = 0
        failed_count = 0
        skipped_count = 0
        
        for user_id in user_ids:
            try:
                snapshot_id = await self.save_daily_snapshot(user_id)
                
                if snapshot_id:
                    created_count += 1
                else:
                    skipped_count += 1
            
            except Exception as e:
                print(f"[SNAPSHOT] ❌ Failed to create snapshot for user {user_id}: {e}")
                failed_count += 1
        
        print("\n" + "="*60)
        print(f"[SNAPSHOT] Daily snapshot job complete:")
        print(f"  ✅ Created: {created_count}")
        print(f"  ⚠️  Skipped: {skipped_count}")
        print(f"  ❌ Failed: {failed_count}")
        print("="*60 + "\n")
        
        return created_count
    
    # ============================================================
    # SNAPSHOT RETRIEVAL
    # ============================================================
    
    def get_snapshot_history(
        self,
        user_id: str,
        days: int = 30,
        wallet_id: Optional[str] = None
    ) -> Optional[SnapshotHistoryResponse]:
        """
        Get historical snapshots for a user.
        
        Args:
            user_id: User ID
            days: Number of days to fetch
            wallet_id: Optional wallet filter
        
        Returns:
            Snapshot history or None
        """
        print(f"[SNAPSHOT] Fetching history for user {user_id} ({days} days)")
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query snapshots
        query = {
            "user_id": user_id,
            "wallet_id": wallet_id,
            "snapshot_date": {
                "$gte": start_date,
                "$lte": end_date
            }
        }
        
        snapshots = list(self.snapshots.find(query).sort("snapshot_date", 1))
        
        print(f"[SNAPSHOT] Found {len(snapshots)} snapshots")
        
        if not snapshots:
            print(f"[SNAPSHOT] No snapshots found")
            return None
        
        # Calculate coverage
        coverage_percent = (len(snapshots) / days) * 100
        
        print(f"[SNAPSHOT] Coverage: {coverage_percent:.1f}%")
        
        # Format for charts
        values = [
            SnapshotHistoryPoint(
                timestamp=int(s["timestamp"].timestamp()),
                value=s["total_value_usd"],
                token_count=s["total_tokens"],
                wallet_count=s["wallet_count"]
            )
            for s in snapshots
        ]
        
        # Calculate metrics
        current_value = snapshots[-1]["total_value_usd"]
        first_value = snapshots[0]["total_value_usd"]
        period_change = current_value - first_value
        period_change_percent = (period_change / first_value * 100) if first_value > 0 else 0
        
        return SnapshotHistoryResponse(
            values=values,
            current_value=round(current_value, 2),
            period_change=round(period_change, 2),
            period_change_percent=round(period_change_percent, 2),
            data_points=len(values),
            data_source="snapshots",
            coverage_percent=round(coverage_percent, 2)
        )
    
    # ============================================================
    # STATISTICS
    # ============================================================
    
    def get_snapshot_stats(self) -> Dict:
        """Get statistics about snapshots."""
        total = self.snapshots.count_documents({})
        
        if total == 0:
            return {
                "total_snapshots": 0,
                "oldest_snapshot": None,
                "newest_snapshot": None,
                "users_with_snapshots": 0,
                "average_value_usd": 0,
                "total_storage_mb": 0
            }
        
        # Get oldest and newest
        oldest = self.snapshots.find_one(sort=[("snapshot_date", 1)])
        newest = self.snapshots.find_one(sort=[("snapshot_date", -1)])
        
        # Get unique users
        users = len(self.snapshots.distinct("user_id"))
        
        # Calculate average value
        pipeline = [
            {"$group": {"_id": None, "avg_value": {"$avg": "$total_value_usd"}}}
        ]
        avg_result = list(self.snapshots.aggregate(pipeline))
        avg_value = avg_result[0]["avg_value"] if avg_result else 0
        
        # Estimate storage (rough)
        storage_mb = (total * 2048) / (1024 * 1024)  # Assume ~2KB per snapshot
        
        return {
            "total_snapshots": total,
            "oldest_snapshot": oldest["snapshot_date"] if oldest else None,
            "newest_snapshot": newest["snapshot_date"] if newest else None,
            "users_with_snapshots": users,
            "average_value_usd": round(avg_value, 2),
            "total_storage_mb": round(storage_mb, 2)
        }
    
    # ============================================================
    # CLEANUP
    # ============================================================
    
    def delete_old_snapshots(self, days_to_keep: int = 90) -> int:
        """
        Delete snapshots older than specified days.
        
        Args:
            days_to_keep: Number of days to keep (default 90)
        
        Returns:
            Number of deleted snapshots
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        result = self.snapshots.delete_many({
            "snapshot_date": {"$lt": cutoff_date}
        })
        
        deleted = result.deleted_count
        
        print(f"[SNAPSHOT] Deleted {deleted} snapshots older than {days_to_keep} days")
        
        return deleted