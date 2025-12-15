#!/usr/bin/env python3
"""
Test script to verify primary fungible store address calculation
"""
import hashlib

def get_primary_fungible_store_address(account_address: str, metadata_address: str) -> str:
    """
    Calculate the deterministic primary fungible store address.
    Formula: sha3_256(32-byte account address | 32-byte metadata address | 0xFC)
    """
    # Normalize addresses - remove 0x and pad to 64 chars (32 bytes)
    acc = account_address.lower().replace("0x", "").zfill(64)
    meta = metadata_address.lower().replace("0x", "").zfill(64)
    
    print(f"Account (padded):  {acc}")
    print(f"Metadata (padded): {meta}")
    
    # Convert to bytes
    acc_bytes = bytes.fromhex(acc)
    meta_bytes = bytes.fromhex(meta)
    suffix = bytes([0xFC])
    
    # Concatenate and hash with SHA3-256
    combined = acc_bytes + meta_bytes + suffix
    print(f"Combined length: {len(combined)} bytes")
    
    hash_result = hashlib.sha3_256(combined).digest()
    result = "0x" + hash_result.hex()
    
    print(f"Calculated store:  {result}")
    return result

# Test with your address
account = "0xe037e246dfd66661c6162e0dff968d64753eea38af08b1da2695e8464dbfce6a"
metadata = "0xa"  # APT metadata

print("=" * 80)
print("Calculating Primary Fungible Store Address")
print("=" * 80)
print(f"Account:  {account}")
print(f"Metadata: {metadata}")
print()

calculated = get_primary_fungible_store_address(account, metadata)

print()
print("Expected from transaction:")
print("0xb9ee08e9ce27a9e44a765451bfe97e6eab89796a9a397a48c66963461898635a")
print()
print("Match:", calculated == "0xb9ee08e9ce27a9e44a765451bfe97e6eab89796a9a397a48c66963461898635a")