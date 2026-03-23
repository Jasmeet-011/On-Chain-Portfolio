# backend/app/services/wallet_service.py
"""
Wallet Service - Multi-Chain Wallet Management

Supports: Aptos, Solana, Ethereum, Polygon, Base (and testnets)
"""
from typing import Optional, List, Dict, Any, Tuple
from bson import ObjectId
from datetime import datetime, timezone

from .db import wallets_collection, users_collection, portfolio_events_collection
from .adapters import get_adapter_for_chain, SUPPORTED_CHAINS, is_evm_chain


# ============================================================
# Internal Helpers
# ============================================================

def _emit_wallet_event(
    user_id: str,
    event_type: str,
    wallet_address: str,
    chain: str,
    timestamp: datetime
) -> None:
    """
    Insert a single lifecycle event into portfolio_events.
    Fire-and-forget — failure is logged, never raised.
    """
    try:
        portfolio_events_collection.insert_one({
            "user_id": user_id,
            "event_type": event_type,          # "wallet_added" | "wallet_removed"
            "wallet_address": wallet_address,
            "chain": chain,
            "timestamp": timestamp
        })
    except Exception as e:
        print(f"[WALLET] Failed to log event {event_type}: {e}")


# ============================================================
# Wallet Validation
# ============================================================

def validate_wallet_address(
    address: str,
    chain: str,
    check_on_chain: bool = False
) -> Tuple[bool, Optional[str]]:
    """
    Validate wallet address format and optionally verify on-chain.

    Args:
        address: Wallet address to validate
        chain: Blockchain network (e.g., "ethereum_sepolia", "aptos", "evm")
        check_on_chain: If True, verify address exists on blockchain

    Returns:
        (is_valid, error_message)
    """
    if not address:
        return False, "Address cannot be empty"

    if not chain:
        return False, "Chain must be specified"

    # For "evm" generic chain, use ethereum_sepolia adapter for validation
    # All EVM addresses have the same format (0x + 40 hex chars)
    validation_chain = chain
    if chain == "evm":
        validation_chain = "ethereum_sepolia"  # Use any EVM adapter for format validation

    # Get adapter for chain
    try:
        adapter = get_adapter_for_chain(validation_chain)
    except ValueError as e:
        return False, str(e)

    # Format validation
    is_valid, error = adapter.validate_address(address)
    if not is_valid:
        return False, error

    # On-chain verification (optional) - skip for generic "evm" chain
    if check_on_chain and chain != "evm":
        exists, error = adapter.verify_on_chain(address)
        if not exists:
            return False, error or "Address not found on blockchain"

    return True, None


def normalize_wallet_address(address: str, chain: str) -> str:
    """
    Normalize wallet address to standard format.

    - EVM: Checksum format (0x742d35Cc...)
    - Solana: Base58 format
    - Aptos: Lowercase with 0x prefix
    """
    # For "evm" generic chain, use ethereum_sepolia adapter
    normalization_chain = chain
    if chain == "evm":
        normalization_chain = "ethereum_sepolia"

    try:
        adapter = get_adapter_for_chain(normalization_chain)
        return adapter.normalize_address(address)
    except Exception:
        # Fallback: basic normalization
        addr = address.strip()
        if is_evm_chain(chain) or chain == "evm":
            return addr  # Keep as-is for EVM (checksum matters)
        return addr.lower()


# ============================================================
# Wallet CRUD Operations
# ============================================================

def create_wallet(
    user_id: str,
    address: str,
    chain: str = "ethereum_sepolia",
    wallet_type: str = "manual",
    label: str = "Main Wallet",
    is_primary: bool = False,
    validate_on_chain: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Create a new wallet for a user.
    
    Args:
        user_id: User's MongoDB ID
        address: Wallet address
        chain: Blockchain network
        wallet_type: Wallet provider type (e.g., "metamask", "manual")
        label: Display name for the wallet
        is_primary: Whether this is the primary wallet
        validate_on_chain: If True, verify address on blockchain
    
    Returns:
        Created wallet document or None if failed
    """
    try:
        # Step 1: Validate address
        is_valid, error_msg = validate_wallet_address(
            address,
            chain,
            check_on_chain=validate_on_chain
        )
        
        if not is_valid:
            print(f"[WALLET] Validation failed: {error_msg}")
            return None
        
        # Step 2: Normalize address
        normalized_addr = normalize_wallet_address(address, chain)
        
        # Step 3: Check for active duplicates (same user + address + chain)
        existing_active = wallets_collection.find_one({
            "user_id": user_id,
            "address": normalized_addr,
            "chain": chain,
            "is_active": True
        })
        if existing_active:
            print(f"[WALLET] Wallet already exists for user {user_id} on {chain}")
            return None

        # If a soft-deleted record exists for this address, reactivate it.
        # This preserves the unique index on (user_id, address).
        existing_deleted = wallets_collection.find_one({
            "user_id": user_id,
            "address": normalized_addr,
            "chain": chain,
            "is_active": False
        })
        if existing_deleted:
            now = datetime.now(timezone.utc)
            wallets_collection.update_one(
                {"_id": existing_deleted["_id"]},
                {"$set": {
                    "is_active": True,
                    "deleted_at": None,
                    "label": label,
                    "type": wallet_type,
                    "created_at": now.isoformat()  # reset lifecycle timestamp
                }}
            )
            wallet_doc = dict(existing_deleted)
            wallet_doc["id"] = str(existing_deleted["_id"])
            wallet_doc.pop("_id", None)
            wallet_doc.update({
                "is_active": True,
                "deleted_at": None,
                "label": label,
                "created_at": now.isoformat()
            })
            _emit_wallet_event(user_id, "wallet_added", normalized_addr, chain, now)
            print(f"[WALLET] Reactivated soft-deleted wallet {normalized_addr[:10]}... for user {user_id}")
            return wallet_doc

        # Step 4: Handle primary wallet logic
        user_wallets = list_user_wallets(user_id)
        
        if not user_wallets or is_primary:
            # First wallet or explicitly set as primary
            if is_primary and user_wallets:
                # Remove primary flag from other wallets
                wallets_collection.update_many(
                    {"user_id": user_id},
                    {"$set": {"is_primary": False}}
                )
            is_primary = True
        
        # Step 5: Create wallet document
        now = datetime.now(timezone.utc)
        wallet_doc = {
            "user_id": user_id,
            "address": normalized_addr,
            "chain": chain,
            "type": wallet_type,
            "label": label,
            "is_primary": is_primary,
            "is_active": True,
            "deleted_at": None,
            "created_at": now.isoformat()
        }

        result = wallets_collection.insert_one(wallet_doc)

        # Convert _id to id for JSON response
        wallet_doc["id"] = str(result.inserted_id)
        del wallet_doc["_id"]

        # Update user's legacy wallet_address field if primary
        if is_primary:
            users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"wallet_address": normalized_addr}}
            )

        _emit_wallet_event(user_id, "wallet_added", normalized_addr, chain, now)
        print(f"[WALLET] Created wallet {normalized_addr[:10]}... for user {user_id} on {chain}")
        return wallet_doc
        
    except Exception as e:
        print(f"[WALLET] Error creating wallet: {e}")
        import traceback
        traceback.print_exc()
        return None


def list_user_wallets(
    user_id: str,
    chain: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get all wallets for a user.
    
    Args:
        user_id: User's MongoDB ID
        chain: Optional filter by chain
    
    Returns:
        List of wallet documents
    """
    try:
        query = {"user_id": user_id, "is_active": True}
        if chain:
            query["chain"] = chain

        wallets = list(wallets_collection.find(query))
        
        # Convert ObjectId to string
        for wallet in wallets:
            wallet["id"] = str(wallet["_id"])
            del wallet["_id"]
            
            # Ensure chain field exists (backward compatibility)
            if "chain" not in wallet:
                wallet["chain"] = "aptos"  # Default for old wallets
        
        return wallets
        
    except Exception as e:
        print(f"[WALLET] Error listing wallets: {e}")
        return []


def get_wallet_by_address(
    user_id: str,
    address: str,
    chain: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Get a specific wallet by address.
    
    Args:
        user_id: User's MongoDB ID
        address: Wallet address
        chain: Optional chain filter (for disambiguation)
    
    Returns:
        Wallet document or None
    """
    try:
        # Try exact match first (active only)
        query = {"user_id": user_id, "address": address, "is_active": True}
        if chain:
            query["chain"] = chain

        wallet = wallets_collection.find_one(query)

        # Try case-insensitive match for EVM addresses
        if not wallet:
            query["address"] = address.lower()
            wallet = wallets_collection.find_one(query)
        
        if wallet:
            wallet["id"] = str(wallet["_id"])
            del wallet["_id"]
            if "chain" not in wallet:
                wallet["chain"] = "aptos"
        
        return wallet
        
    except Exception as e:
        print(f"[WALLET] Error getting wallet: {e}")
        return None


def get_primary_wallet(user_id: str) -> Optional[Dict[str, Any]]:
    """Get the primary wallet for a user (any chain)."""
    try:
        wallet = wallets_collection.find_one({
            "user_id": user_id,
            "is_primary": True,
            "is_active": True
        })
        
        if wallet:
            wallet["id"] = str(wallet["_id"])
            del wallet["_id"]
            if "chain" not in wallet:
                wallet["chain"] = "aptos"
        
        return wallet
        
    except Exception as e:
        print(f"[WALLET] Error getting primary wallet: {e}")
        return None


def update_wallet_label(
    user_id: str,
    address: str,
    new_label: str,
    chain: Optional[str] = None
) -> bool:
    """Update wallet label."""
    try:
        query = {"user_id": user_id, "address": address}
        if chain:
            query["chain"] = chain
        
        result = wallets_collection.update_one(
            query,
            {"$set": {"label": new_label}}
        )
        return result.modified_count > 0 or result.matched_count > 0
        
    except Exception as e:
        print(f"[WALLET] Error updating label: {e}")
        return False


def set_primary_wallet(
    user_id: str,
    address: str,
    chain: Optional[str] = None
) -> bool:
    """
    Set a wallet as the primary wallet.
    Removes primary flag from all other wallets.
    """
    try:
        # Find the wallet (active only)
        query = {"user_id": user_id, "address": address, "is_active": True}
        if chain:
            query["chain"] = chain

        wallet = wallets_collection.find_one(query)
        if not wallet:
            print(f"[WALLET] Wallet not found: {address}")
            return False

        # Remove primary from all active wallets
        wallets_collection.update_many(
            {"user_id": user_id, "is_active": True},
            {"$set": {"is_primary": False}}
        )
        
        # Set this wallet as primary
        wallets_collection.update_one(
            query,
            {"$set": {"is_primary": True}}
        )
        
        # Update user's legacy wallet_address field
        users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"wallet_address": address}}
        )
        
        print(f"[WALLET] Set {address[:10]}... as primary for user {user_id}")
        return True
        
    except Exception as e:
        print(f"[WALLET] Error setting primary: {e}")
        return False


def delete_wallet(
    user_id: str,
    address: str,
    chain: Optional[str] = None
) -> bool:
    """
    Soft-delete a wallet (sets is_active=False, deleted_at=now).
    Hard delete is never performed to preserve analytics history.
    If deleting primary wallet, promotes the next active wallet to primary.
    """
    try:
        query = {"user_id": user_id, "address": address, "is_active": True}
        if chain:
            query["chain"] = chain

        wallet = wallets_collection.find_one(query)
        if not wallet:
            print(f"[WALLET] Wallet not found or already deleted: {address}")
            return False

        was_primary = wallet.get("is_primary", False)
        wallet_chain = wallet.get("chain", "unknown")
        now = datetime.now(timezone.utc)

        # Soft delete: mark inactive
        result = wallets_collection.update_one(
            {"_id": wallet["_id"]},
            {"$set": {
                "is_active": False,
                "is_primary": False,
                "deleted_at": now.isoformat()
            }}
        )

        if result.modified_count == 0:
            return False

        _emit_wallet_event(user_id, "wallet_removed", address, wallet_chain, now)

        # If this was primary, promote the next active wallet
        if was_primary:
            remaining_wallets = list_user_wallets(user_id)  # returns active only
            if remaining_wallets:
                set_primary_wallet(user_id, remaining_wallets[0]["address"])
            else:
                users_collection.update_one(
                    {"_id": ObjectId(user_id)},
                    {"$set": {"wallet_address": None}}
                )

        print(f"[WALLET] Soft-deleted wallet {address[:10]}... for user {user_id}")
        return True

    except Exception as e:
        print(f"[WALLET] Error deleting wallet: {e}")
        return False


def delete_all_user_wallets(user_id: str) -> bool:
    """Soft-delete all active wallets for a user."""
    try:
        now = datetime.now(timezone.utc)

        # Fetch active wallets before marking them deleted (for event logging)
        active_wallets = list(wallets_collection.find(
            {"user_id": user_id, "is_active": True},
            {"address": 1, "chain": 1}
        ))

        result = wallets_collection.update_many(
            {"user_id": user_id, "is_active": True},
            {"$set": {
                "is_active": False,
                "is_primary": False,
                "deleted_at": now.isoformat()
            }}
        )

        # Emit one event per wallet
        for w in active_wallets:
            _emit_wallet_event(
                user_id, "wallet_removed",
                w.get("address", ""), w.get("chain", "unknown"), now
            )

        # Clear legacy field
        users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"wallet_address": None}}
        )

        print(f"[WALLET] Soft-deleted {result.modified_count} wallets for user {user_id}")
        return True

    except Exception as e:
        print(f"[WALLET] Error deleting all wallets: {e}")
        return False


# ============================================================
# Utility Functions
# ============================================================

def get_wallet_stats_by_chain(user_id: str) -> Dict[str, int]:
    """Get wallet count grouped by chain."""
    try:
        pipeline = [
            {"$match": {"user_id": user_id, "is_active": True}},
            {"$group": {"_id": "$chain", "count": {"$sum": 1}}}
        ]
        
        results = wallets_collection.aggregate(pipeline)
        
        stats = {}
        for result in results:
            chain = result["_id"] or "aptos"  # Default for old wallets
            stats[chain] = result["count"]
        
        return stats
        
    except Exception as e:
        print(f"[WALLET] Error getting stats: {e}")
        return {}


def get_wallets_by_chain(user_id: str) -> Dict[str, List[Dict[str, Any]]]:
    """Get wallets grouped by chain."""
    wallets = list_user_wallets(user_id)
    
    by_chain = {}
    for wallet in wallets:
        chain = wallet.get("chain", "aptos")
        if chain not in by_chain:
            by_chain[chain] = []
        by_chain[chain].append(wallet)
    
    return by_chain


# ============================================================
# Migration Functions
# ============================================================

def migrate_user_wallets(user_id: str) -> int:
    """
    Migrate wallets from embedded array to wallets collection.
    Adds chain="aptos" for backward compatibility.
    
    Returns:
        Number of wallets migrated
    """
    try:
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return 0
        
        embedded_wallets = user.get("wallets", [])
        if not embedded_wallets:
            return 0
        
        migrated_count = 0
        
        for wallet in embedded_wallets:
            address = wallet.get("address")
            if not address:
                continue
            
            # Check if already migrated
            existing = wallets_collection.find_one({
                "user_id": user_id,
                "address": address.lower(),
                "chain": "aptos"  # Old wallets are Aptos
            })
            
            if existing:
                continue
            
            # Get label (try both field names)
            label = wallet.get("label") or wallet.get("name") or "Wallet"
            
            # Create wallet in new collection
            result = create_wallet(
                user_id=user_id,
                address=address,
                chain="aptos",  # Default for old wallets
                wallet_type="manual",
                label=label,
                is_primary=wallet.get("is_primary", False)
            )
            
            if result:
                migrated_count += 1
        
        # Clear embedded wallets after migration
        if migrated_count > 0:
            users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"wallets": []}}
            )
        
        print(f"[WALLET] Migrated {migrated_count} wallets for user {user_id}")
        return migrated_count
        
    except Exception as e:
        print(f"[WALLET] Migration error: {e}")
        return 0


def migrate_all_users() -> Dict[str, int]:
    """
    Migrate wallets for all users.
    
    Returns:
        Statistics dictionary
    """
    try:
        users = users_collection.find({})
        
        stats = {
            "total_users": 0,
            "users_with_wallets": 0,
            "total_wallets_migrated": 0
        }
        
        for user in users:
            stats["total_users"] += 1
            user_id = str(user["_id"])
            
            if user.get("wallets"):
                stats["users_with_wallets"] += 1
                migrated = migrate_user_wallets(user_id)
                stats["total_wallets_migrated"] += migrated
        
        print(f"[WALLET] Migration complete: {stats}")
        return stats
        
    except Exception as e:
        print(f"[WALLET] Migration error: {e}")
        return {"error": str(e)}