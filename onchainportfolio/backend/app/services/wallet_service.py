# app/services/wallet_service.py
from typing import Optional, List, Dict, Any, Literal, Tuple
from bson import ObjectId
from datetime import datetime, timezone

from .db import wallets_collection, users_collection
from .adapters import get_adapter_for_chain

WalletType = Literal["petra", "phantom", "solflare", "manual"]
ChainType = Literal["aptos", "solana"]

# ============================================================
# Wallet Validation (Multi-Chain)
# ============================================================

def validate_wallet_address(
    address: str, 
    chain: ChainType,
    check_on_chain: bool = False
) -> Tuple[bool, Optional[str]]:
    """
    Validate wallet address for specified chain.
    
    Args:
        address: Wallet address
        chain: Chain identifier ("aptos", "solana")
        check_on_chain: Whether to verify address exists on blockchain
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Get the appropriate adapter for this chain
        adapter = get_adapter_for_chain(chain)
        
        # Step 1: Format validation
        is_valid, error = adapter.validate_address(address)
        if not is_valid:
            return False, error
        
        # Step 2: On-chain verification (optional)
        if check_on_chain:
            exists, error = adapter.verify_on_chain(address)
            if not exists:
                return False, error or f"Address not found on {chain} blockchain"
        
        return True, None
    
    except Exception as e:
        return False, f"Validation error: {str(e)}"


def normalize_wallet_address(address: str, chain: ChainType) -> str:
    """
    Normalize address for specified chain.
    
    Args:
        address: Raw address
        chain: Chain identifier
    
    Returns:
        Normalized address
    """
    try:
        adapter = get_adapter_for_chain(chain)
        return adapter.normalize_address(address)
    except Exception:
        # Fallback to basic normalization
        return address.strip()


# ============================================================
# Wallet CRUD Operations (Multi-Chain)
# ============================================================

def create_wallet(
    user_id: str,
    address: str,
    chain: ChainType = "aptos",  # ← NEW: Chain parameter
    wallet_type: WalletType = "manual",
    label: str = "Main Wallet",
    is_primary: bool = False,
    validate_on_chain: bool = False
) -> Optional[dict]:
    """
    Create a new wallet for a user.
    
    Args:
        user_id: User ID
        address: Wallet address
        chain: Blockchain ("aptos", "solana")  ← NEW
        wallet_type: Wallet type ("petra", "phantom", "manual", etc.)
        label: Display name
        is_primary: Whether this is the primary wallet
        validate_on_chain: If True, verify address exists on blockchain
    
    Returns:
        Created wallet document or None if failed
    """
    try:
        # Validate address
        is_valid, error_msg = validate_wallet_address(
            address, 
            chain,
            check_on_chain=validate_on_chain
        )
        
        if not is_valid:
            print(f"[ERROR] Address validation failed: {error_msg}")
            return None
        
        normalized_addr = normalize_wallet_address(address, chain)
        
        # Check if wallet already exists for this user + chain
        # ✅ IMPORTANT: Same address can exist on different chains!
        existing = wallets_collection.find_one({
            "user_id": user_id,
            "address": normalized_addr,
            "chain": chain  # ← NEW: Include chain in duplicate check
        })
        
        if existing:
            print(f"[WARN] Wallet {normalized_addr} on {chain} already exists for user {user_id}")
            return None
        
        # If this is the first wallet or is_primary=True, make it primary
        user_wallets = list_user_wallets(user_id)
        if not user_wallets or is_primary:
            # Remove primary flag from other wallets
            if is_primary:
                wallets_collection.update_many(
                    {"user_id": user_id},
                    {"$set": {"is_primary": False}}
                )
            is_primary = True
        
        # Create wallet document
        wallet_doc = {
            "user_id": user_id,
            "address": normalized_addr,
            "chain": chain,  # ← NEW: Store chain
            "type": wallet_type,
            "label": label,
            "is_primary": is_primary,
            "created_at": datetime.now(timezone.utc).isoformat()
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
        
        print(f"[INFO] Created {chain} wallet {normalized_addr} for user {user_id}")
        return wallet_doc
        
    except Exception as e:
        print(f"[ERROR] Failed to create wallet: {e}")
        import traceback
        traceback.print_exc()
        return None


def list_user_wallets(user_id: str, chain: Optional[ChainType] = None) -> List[Dict[str, Any]]:
    """
    Get all wallets for a user, optionally filtered by chain.
    
    Args:
        user_id: User ID
        chain: Optional chain filter ("aptos", "solana", or None for all)
    
    Returns:
        List of wallet documents
    """
    try:
        query = {"user_id": user_id}
        
        # Add chain filter if specified
        if chain:
            query["chain"] = chain
        
        wallets = list(wallets_collection.find(query))
        
        # Convert ObjectId to string
        for wallet in wallets:
            wallet["id"] = str(wallet["_id"])
            del wallet["_id"]
        
        return wallets
    except Exception as e:
        print(f"[ERROR] Failed to list wallets: {e}")
        return []


def get_wallet_by_id(wallet_id: str) -> Optional[dict]:
    """Get a specific wallet by its ID."""
    try:
        wallet = wallets_collection.find_one({"_id": ObjectId(wallet_id)})
        if wallet:
            wallet["id"] = str(wallet["_id"])
            del wallet["_id"]
        return wallet
    except Exception as e:
        print(f"[ERROR] Failed to get wallet: {e}")
        return None


def get_wallet_by_address(
    user_id: str, 
    address: str,
    chain: Optional[ChainType] = None
) -> Optional[dict]:
    """
    Get a specific wallet by user_id and address.
    
    Args:
        user_id: User ID
        address: Wallet address
        chain: Optional chain (if None, searches all chains)
    
    Returns:
        Wallet document or None
    """
    try:
        query = {
            "user_id": user_id,
            "address": address  # Assume already normalized
        }
        
        # Add chain to query if specified
        if chain:
            query["chain"] = chain
        
        wallet = wallets_collection.find_one(query)
        
        if wallet:
            wallet["id"] = str(wallet["_id"])
            del wallet["_id"]
        return wallet
    except Exception as e:
        print(f"[ERROR] Failed to get wallet by address: {e}")
        return None


def get_primary_wallet(user_id: str) -> Optional[dict]:
    """Get the primary wallet for a user."""
    try:
        wallet = wallets_collection.find_one({
            "user_id": user_id,
            "is_primary": True
        })
        if wallet:
            wallet["id"] = str(wallet["_id"])
            del wallet["_id"]
        return wallet
    except Exception as e:
        print(f"[ERROR] Failed to get primary wallet: {e}")
        return None


def update_wallet_label(user_id: str, address: str, new_label: str) -> bool:
    """Update the label/name of a wallet."""
    try:
        result = wallets_collection.update_one(
            {"user_id": user_id, "address": address},
            {"$set": {"label": new_label}}
        )
        return result.modified_count > 0 or result.matched_count > 0
    except Exception as e:
        print(f"[ERROR] Failed to update wallet label: {e}")
        return False


def set_primary_wallet(user_id: str, address: str) -> bool:
    """
    Set a specific wallet as the primary wallet.
    Removes primary flag from all other wallets.
    """
    try:
        # Check if wallet exists
        wallet = wallets_collection.find_one({
            "user_id": user_id,
            "address": address
        })
        
        if not wallet:
            print(f"[WARN] Wallet {address} not found for user {user_id}")
            return False
        
        # Remove primary from all wallets
        wallets_collection.update_many(
            {"user_id": user_id},
            {"$set": {"is_primary": False}}
        )
        
        # Set this wallet as primary
        wallets_collection.update_one(
            {"user_id": user_id, "address": address},
            {"$set": {"is_primary": True}}
        )
        
        # Update user's legacy wallet_address field
        users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"wallet_address": address}}
        )
        
        print(f"[INFO] Set {address} as primary for user {user_id}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to set primary wallet: {e}")
        return False


def delete_wallet(user_id: str, address: str, chain: Optional[ChainType] = None) -> bool:
    """
    Delete a wallet.
    If deleting the primary wallet, automatically sets the next wallet as primary.
    
    Args:
        user_id: User ID
        address: Wallet address
        chain: Optional chain (if None, searches all chains)
    """
    try:
        query = {
            "user_id": user_id,
            "address": address
        }
        
        if chain:
            query["chain"] = chain
        
        # Check if wallet exists and if it's primary
        wallet = wallets_collection.find_one(query)
        
        if not wallet:
            print(f"[WARN] Wallet {address} not found for user {user_id}")
            return False
        
        was_primary = wallet.get("is_primary", False)
        
        # Delete the wallet
        result = wallets_collection.delete_one(query)
        
        if result.deleted_count == 0:
            return False
        
        # If this was primary, set another wallet as primary
        if was_primary:
            remaining_wallets = list_user_wallets(user_id)
            if remaining_wallets:
                # Set first remaining wallet as primary
                first_wallet = remaining_wallets[0]
                set_primary_wallet(user_id, first_wallet["address"])
            else:
                # No wallets left, clear legacy field
                users_collection.update_one(
                    {"_id": ObjectId(user_id)},
                    {"$set": {"wallet_address": None}}
                )
        
        chain_str = f" on {chain}" if chain else ""
        print(f"[INFO] Deleted wallet {address}{chain_str} for user {user_id}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to delete wallet: {e}")
        return False


def delete_all_user_wallets(user_id: str) -> bool:
    """Delete all wallets for a user."""
    try:
        result = wallets_collection.delete_many({"user_id": user_id})
        
        # Clear legacy field
        users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"wallet_address": None}}
        )
        
        print(f"[INFO] Deleted {result.deleted_count} wallets for user {user_id}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to delete all wallets: {e}")
        return False


# ============================================================
# Multi-Chain Statistics
# ============================================================

def get_wallet_stats_by_chain(user_id: str) -> Dict[str, int]:
    """
    Get count of wallets per chain for a user.
    
    Returns:
        Dict mapping chain to count (e.g., {"aptos": 3, "solana": 2})
    """
    try:
        wallets = list_user_wallets(user_id)
        
        stats = {}
        for wallet in wallets:
            chain = wallet.get("chain", "aptos")  # Default to aptos for old wallets
            stats[chain] = stats.get(chain, 0) + 1
        
        return stats
    except Exception as e:
        print(f"[ERROR] Failed to get wallet stats: {e}")
        return {}


# ============================================================
# Migration Helper (Updated)
# ============================================================

def migrate_user_wallets(user_id: str) -> int:
    """
    Migrate wallets from embedded array to wallets collection.
    Now adds chain="aptos" to all migrated wallets (assume Aptos for old data).
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
                "address": normalize_wallet_address(address, "aptos"),
                "chain": "aptos"  # ← Assume Aptos for old wallets
            })
            
            if existing:
                continue
            
            # Get label
            label = wallet.get("label") or wallet.get("name") or "Wallet"
            
            # Create wallet with chain="aptos"
            result = create_wallet(
                user_id=user_id,
                address=address,
                chain="aptos",  # ← All old wallets are Aptos
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
        
        print(f"[INFO] Migrated {migrated_count} wallets for user {user_id}")
        return migrated_count
        
    except Exception as e:
        print(f"[ERROR] Failed to migrate wallets: {e}")
        return 0


def migrate_all_users() -> Dict[str, int]:
    """Migrate wallets for ALL users."""
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
        
        print(f"[MIGRATION] Complete: {stats}")
        return stats
        
    except Exception as e:
        print(f"[ERROR] Failed to migrate all users: {e}")
        return {"error": str(e)}