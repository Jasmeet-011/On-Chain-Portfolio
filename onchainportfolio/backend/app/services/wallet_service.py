# app/services/wallet_service.py
from typing import Optional, List, Dict, Any, Literal, Tuple
from bson import ObjectId
from datetime import datetime, timezone
import re

from .db import wallets_collection, users_collection

WalletType = Literal["petra", "manual"]

# ============================================================
# Wallet Validation
# ============================================================

def validate_aptos_address_format(address: str) -> Tuple[bool, Optional[str]]:
    """
    Validate Aptos address format (strict validation).
    Returns: (is_valid, error_message)
    
    Rules:
    - Must start with 0x
    - Must contain only hexadecimal characters (0-9, a-f, A-F)
    - Must be between 1-64 hex characters (after 0x)
    - Accepts both short form (0x1) and long form (0x0000...0001)
    """
    if not address:
        return False, "Address cannot be empty"
    
    # Remove whitespace
    addr = address.strip()
    
    # Check 0x prefix
    if not addr.lower().startswith("0x"):
        return False, "Address must start with '0x'"
    
    # Extract hex part
    hex_part = addr[2:]
    
    # Check length
    if len(hex_part) == 0:
        return False, "Address must have at least one character after '0x'"
    
    if len(hex_part) > 64:
        return False, "Address cannot be longer than 64 hex characters (excluding '0x')"
    
    # Check if all characters are valid hex
    if not re.match(r'^[0-9a-fA-F]+$', hex_part):
        return False, "Address must contain only hexadecimal characters (0-9, a-f, A-F)"
    
    return True, None


def validate_aptos_address_on_chain(address: str, aptos_client=None) -> Tuple[bool, Optional[str]]:
    """
    Check if address exists on Aptos blockchain.
    Returns: (exists, error_message)
    
    Note: This is optional and requires an AptosClient instance.
    """
    if aptos_client is None:
        # If no client provided, skip on-chain validation
        return True, None
    
    try:
        # Normalize address
        normalized = normalize_address(address)
        
        # Try to fetch account resources
        resources = aptos_client.get_account_resources(normalized)
        
        # If we get a list (even empty), account exists
        # Note: New accounts exist but have no resources until first transaction
        if isinstance(resources, list):
            return True, None
        
        return False, "Address not found on Aptos blockchain"
        
    except Exception as e:
        # If there's an error, log it but don't fail validation
        # (Maybe node is down, network issue, etc.)
        print(f"[WARN] Could not verify address on-chain: {e}")
        return True, None  # Assume valid if we can't check


def validate_aptos_address(address: str, check_on_chain: bool = False, aptos_client=None) -> Tuple[bool, Optional[str]]:
    """
    Complete address validation.
    Returns: (is_valid, error_message)
    
    Args:
        address: Aptos address to validate
        check_on_chain: If True, verify address exists on blockchain
        aptos_client: AptosClient instance (required if check_on_chain=True)
    """
    # Step 1: Format validation (always required)
    is_valid_format, format_error = validate_aptos_address_format(address)
    if not is_valid_format:
        return False, format_error
    
    # Step 2: On-chain validation (optional)
    if check_on_chain:
        exists_on_chain, chain_error = validate_aptos_address_on_chain(address, aptos_client)
        if not exists_on_chain:
            return False, chain_error or "Address not found on blockchain"
    
    return True, None


def normalize_address(address: str) -> str:
    """Normalize address to lowercase with 0x prefix."""
    addr = address.lower().strip()
    if not addr.startswith("0x"):
        addr = "0x" + addr
    return addr


# ============================================================
# Wallet CRUD Operations
# ============================================================

def create_wallet(
    user_id: str,
    address: str,
    wallet_type: WalletType = "manual",
    label: str = "Main Wallet",
    is_primary: bool = False,
    validate_on_chain: bool = False,
    aptos_client=None
) -> Optional[dict]:
    """
    Create a new wallet for a user.
    Returns the created wallet document or None if failed.
    
    Args:
        user_id: User ID
        address: Wallet address
        wallet_type: "petra" or "manual"
        label: Display name for wallet (NOT "name")
        is_primary: Whether this is the primary wallet
        validate_on_chain: If True, verify address exists on blockchain
        aptos_client: AptosClient instance (required if validate_on_chain=True)
    """
    try:
        # Step 1: Validate address format and optionally check on-chain
        is_valid, error_msg = validate_aptos_address(
            address, 
            check_on_chain=validate_on_chain,
            aptos_client=aptos_client
        )
        
        if not is_valid:
            print(f"[ERROR] Address validation failed: {error_msg}")
            return None
        
        normalized_addr = normalize_address(address)
        
        # Check if wallet already exists for this user
        existing = wallets_collection.find_one({
            "user_id": user_id,
            "address": normalized_addr
        })
        
        if existing:
            print(f"[WARN] Wallet {normalized_addr} already exists for user {user_id}")
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
            "type": wallet_type,
            "label": label,  # ✅ Uses "label" consistently
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
        
        print(f"[INFO] Created wallet {normalized_addr} for user {user_id}")
        return wallet_doc
        
    except Exception as e:
        print(f"[ERROR] Failed to create wallet: {e}")
        return None


def list_user_wallets(user_id: str) -> List[Dict[str, Any]]:
    """
    Get all wallets for a user.
    Returns list of wallet documents.
    """
    try:
        wallets = list(wallets_collection.find({"user_id": user_id}))
        
        # Convert ObjectId to string for JSON serialization
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


def get_wallet_by_address(user_id: str, address: str) -> Optional[dict]:
    """Get a specific wallet by user_id and address."""
    try:
        normalized_addr = normalize_address(address)
        wallet = wallets_collection.find_one({
            "user_id": user_id,
            "address": normalized_addr
        })
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
        normalized_addr = normalize_address(address)
        result = wallets_collection.update_one(
            {"user_id": user_id, "address": normalized_addr},
            {"$set": {"label": new_label}}  # ✅ Uses "label"
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
        normalized_addr = normalize_address(address)
        
        # Check if wallet exists
        wallet = wallets_collection.find_one({
            "user_id": user_id,
            "address": normalized_addr
        })
        
        if not wallet:
            print(f"[WARN] Wallet {normalized_addr} not found for user {user_id}")
            return False
        
        # Remove primary from all wallets
        wallets_collection.update_many(
            {"user_id": user_id},
            {"$set": {"is_primary": False}}
        )
        
        # Set this wallet as primary
        wallets_collection.update_one(
            {"user_id": user_id, "address": normalized_addr},
            {"$set": {"is_primary": True}}
        )
        
        # Update user's legacy wallet_address field
        users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"wallet_address": normalized_addr}}
        )
        
        print(f"[INFO] Set {normalized_addr} as primary for user {user_id}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to set primary wallet: {e}")
        return False


def delete_wallet(user_id: str, address: str) -> bool:
    """
    Delete a wallet.
    If deleting the primary wallet, automatically sets the next wallet as primary.
    """
    try:
        normalized_addr = normalize_address(address)
        
        # Check if wallet exists and if it's primary
        wallet = wallets_collection.find_one({
            "user_id": user_id,
            "address": normalized_addr
        })
        
        if not wallet:
            print(f"[WARN] Wallet {normalized_addr} not found for user {user_id}")
            return False
        
        was_primary = wallet.get("is_primary", False)
        
        # Delete the wallet
        result = wallets_collection.delete_one({
            "user_id": user_id,
            "address": normalized_addr
        })
        
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
        
        print(f"[INFO] Deleted wallet {normalized_addr} for user {user_id}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to delete wallet: {e}")
        return False


def delete_all_user_wallets(user_id: str) -> bool:
    """Delete all wallets for a user (e.g., account deletion)."""
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
# Migration Helper (Improved)
# ============================================================

def migrate_user_wallets(user_id: str) -> int:
    """
    Migrate wallets from embedded array in user document to wallets collection.
    Handles BOTH "name" and "label" fields for backward compatibility.
    Returns number of wallets migrated.
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
                "address": normalize_address(address)
            })
            
            if existing:
                print(f"[INFO] Wallet {address} already migrated for user {user_id}")
                continue
            
            # Get label - try "label" first, fallback to "name"
            label = wallet.get("label") or wallet.get("name") or "Wallet"
            
            # Create wallet in new collection
            result = create_wallet(
                user_id=user_id,
                address=address,
                wallet_type="manual",  # Assume manual for old wallets
                label=label,  # ✅ Always stores as "label"
                is_primary=wallet.get("is_primary", False)
            )
            
            if result:
                migrated_count += 1
        
        # Clear embedded wallets array after successful migration
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
    """
    Migrate wallets for ALL users in database.
    Returns statistics.
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
            
            # Check if user has embedded wallets
            if user.get("wallets"):
                stats["users_with_wallets"] += 1
                
                # Migrate this user's wallets
                migrated = migrate_user_wallets(user_id)
                stats["total_wallets_migrated"] += migrated
        
        print(f"[MIGRATION] Complete: {stats}")
        return stats
        
    except Exception as e:
        print(f"[ERROR] Failed to migrate all users: {e}")
        return {"error": str(e)}