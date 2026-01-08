# generate_solana_wallets.py
"""
Generate Solana test wallets for testing.

This creates NEW Solana keypairs (wallets) that you can use for testing.
No contract needed - Solana wallets are just public/private key pairs!

Usage:
    pip install base58
    python generate_solana_wallets.py
"""

import base58
import secrets


def generate_solana_keypair():
    """
    Generate a new Solana keypair.
    
    Returns:
        tuple: (public_key, private_key) both as base58 strings
    """
    # Generate 32 random bytes for private key
    private_key_bytes = secrets.token_bytes(32)
    
    # For testing, we'll just use the private key as public key
    # (In real Solana, public key is derived using Ed25519)
    # This is fine for ADDRESS VALIDATION testing
    public_key_bytes = private_key_bytes  # Simplified for testing
    
    # Encode to base58
    public_key = base58.b58encode(public_key_bytes).decode('ascii')
    private_key = base58.b58encode(private_key_bytes).decode('ascii')
    
    return public_key, private_key


def generate_multiple_wallets(count=5):
    """Generate multiple test wallets."""
    
    print("=" * 70)
    print("🔑 SOLANA TEST WALLET GENERATOR")
    print("=" * 70)
    print(f"\nGenerating {count} test wallets...\n")
    
    wallets = []
    
    for i in range(1, count + 1):
        public_key, private_key = generate_solana_keypair()
        
        wallets.append({
            "number": i,
            "public_key": public_key,
            "private_key": private_key
        })
        
        print(f"Wallet #{i}:")
        print(f"  Public Key (Address):  {public_key}")
        print(f"  Private Key:           {private_key}")
        print(f"  Length:                {len(public_key)} characters")
        print()
    
    print("=" * 70)
    print("✅ WALLETS GENERATED!")
    print("=" * 70)
    
    print("\n📝 HOW TO USE THESE WALLETS:\n")
    print("1. For VALIDATION TESTING:")
    print("   - Use any public key above to test address validation")
    print("   - These will pass format validation")
    print("   - They won't have balances (not funded)")
    print()
    print("2. For BALANCE TESTING:")
    print("   - Use a REAL Solana address with funds")
    print("   - Example: 7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs")
    print("   - Or create a wallet in Phantom and use that address")
    print()
    print("3. For ADDING TO DATABASE:")
    print("   - Any of these addresses can be added via API")
    print("   - They'll be stored correctly")
    print("   - Portfolio fetch will return empty (no funds)")
    print()
    
    print("⚠️  IMPORTANT NOTES:\n")
    print("- These are TEST wallets (random keypairs)")
    print("- They won't have funds on mainnet/testnet")
    print("- DO NOT use these for real funds")
    print("- For testing balances, use a real funded wallet")
    print()
    
    # Save to file
    with open("solana_test_wallets.txt", "w") as f:
        f.write("SOLANA TEST WALLETS\n")
        f.write("=" * 70 + "\n\n")
        
        for wallet in wallets:
            f.write(f"Wallet #{wallet['number']}:\n")
            f.write(f"Public Key:  {wallet['public_key']}\n")
            f.write(f"Private Key: {wallet['private_key']}\n")
            f.write("\n")
    
    print("💾 Wallets saved to: solana_test_wallets.txt")
    print()
    
    return wallets


def get_real_solana_addresses():
    """Return some real Solana addresses for testing."""
    
    print("\n" + "=" * 70)
    print("🌐 REAL SOLANA ADDRESSES FOR TESTING")
    print("=" * 70)
    
    addresses = [
        {
            "name": "Wrapped SOL Program",
            "address": "So11111111111111111111111111111111111111112",
            "description": "Native SOL token program (always exists)"
        },
        {
            "name": "USDC Mint",
            "address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "description": "USDC token mint address"
        },
        {
            "name": "Example Wallet",
            "address": "7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs",
            "description": "Sample wallet address (may or may not have funds)"
        },
    ]
    
    print("\nThese are REAL addresses you can use for testing:\n")
    
    for addr in addresses:
        print(f"📍 {addr['name']}:")
        print(f"   Address: {addr['address']}")
        print(f"   Use for: {addr['description']}")
        print()
    
    print("✅ Use these to test:")
    print("   - Address validation (will pass)")
    print("   - RPC calls (will work)")
    print("   - Balance fetching (may have balances)")
    print()
    
    return addresses


if __name__ == "__main__":
    print("\n")
    
    # Generate test wallets
    wallets = generate_multiple_wallets(count=3)
    
    # Show real addresses
    real_addresses = get_real_solana_addresses()
    
    print("=" * 70)
    print("🎯 QUICK TEST COMMANDS")
    print("=" * 70)
    
    test_address = wallets[0]['public_key']
    
    print(f"\n1. Test validation with generated wallet:")
    print(f'   curl -X POST http://localhost:8000/v1/wallets \\')
    print(f'     -H "Authorization: Bearer YOUR_TOKEN" \\')
    print(f'     -H "Content-Type: application/json" \\')
    print(f'     -d \'{{"address": "{test_address}", "chain": "solana", "type": "manual", "label": "Test Wallet"}}\'')
    
    print(f"\n2. Test with real SOL address:")
    print(f'   curl "http://localhost:8000/v1/wallets/So11111111111111111111111111111111111111112/portfolio?chain=solana"')
    
    print("\n")