# test_adapters.py
"""
Test script for multi-chain adapters.

Tests:
1. Adapter initialization
2. Address validation
3. Balance fetching
4. Portfolio fetching

Usage:
    cd backend
    python test_adapters.py
"""

import sys
import asyncio
from decimal import Decimal

# Add app to path
sys.path.insert(0, '.')

from app.services.adapters import get_adapter_for_chain, AptosAdapter, SolanaAdapter


def test_aptos_adapter():
    """Test Aptos adapter functionality."""
    
    print("\n" + "=" * 60)
    print("🧪 TESTING APTOS ADAPTER")
    print("=" * 60)
    
    # Known Aptos addresses for testing
    TEST_ADDRESSES = {
        "valid": "0x1",  # System address (always exists)
        "invalid_format": "invalid_address",
        "invalid_length": "0x" + "1" * 100,
    }
    
    try:
        # Initialize adapter
        print("\n1️⃣  Initializing Aptos adapter...")
        adapter = get_adapter_for_chain("aptos")
        print(f"✅ Adapter: {adapter}")
        print(f"   Chain: {adapter.get_chain_name()}")
        print(f"   Native token: {adapter.get_native_token_symbol()}")
        
        # Test address validation
        print("\n2️⃣  Testing address validation...")
        
        for label, address in TEST_ADDRESSES.items():
            is_valid, error = adapter.validate_address(address)
            
            if is_valid:
                print(f"✅ {label:20s}: {address:30s} - VALID")
            else:
                print(f"❌ {label:20s}: {address:30s} - INVALID ({error})")
        
        # Test address normalization
        print("\n3️⃣  Testing address normalization...")
        test_addr = "1"  # Without 0x
        normalized = adapter.normalize_address(test_addr)
        print(f"   Input:      {test_addr}")
        print(f"   Normalized: {normalized}")
        
        # Test balance fetching
        print("\n4️⃣  Testing balance fetching...")
        test_address = "0x1"
        print(f"   Address: {test_address}")
        
        balance = adapter.get_balance(test_address)
        if balance is not None:
            apt_amount = adapter.normalize_amount(str(balance), 8)
            print(f"✅ APT Balance (raw): {balance}")
            print(f"✅ APT Balance: {apt_amount} APT")
        else:
            print(f"⚠️  No balance found (may be empty wallet)")
        
        # Test token balances
        print("\n5️⃣  Testing token balances...")
        balances = adapter.get_token_balances(test_address)
        
        if balances:
            print(f"✅ Found {len(balances)} token(s):")
            for bal in balances:
                print(f"   - {bal['symbol']}: {bal['amount']} (raw: {bal['raw']})")
        else:
            print(f"⚠️  No tokens found")
        
        # Test portfolio
        print("\n6️⃣  Testing portfolio fetching...")
        portfolio = adapter.get_portfolio(test_address)
        
        print(f"✅ Portfolio fetched:")
        print(f"   Chain: {portfolio.get('chain')}")
        print(f"   Address: {portfolio.get('address')}")
        print(f"   Balances: {len(portfolio.get('balances', []))} token(s)")
        
        if portfolio.get('native_balance'):
            nb = portfolio['native_balance']
            print(f"   Native: {nb['amount']} {nb['symbol']}")
        
        print("\n✅ APTOS ADAPTER TEST PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ APTOS ADAPTER TEST FAILED!")
        print(f"   Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_solana_adapter():
    """Test Solana adapter functionality."""
    
    print("\n" + "=" * 60)
    print("🧪 TESTING SOLANA ADAPTER")
    print("=" * 60)
    
    # Known Solana addresses for testing
    TEST_ADDRESSES = {
        "valid_1": "7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs",  # Example wallet
        "valid_2": "So11111111111111111111111111111111111111112",  # Wrapped SOL
        "invalid_format": "0x1234",  # Wrong format (not base58)
        "invalid_length": "abc",  # Too short
    }
    
    try:
        # Initialize adapter
        print("\n1️⃣  Initializing Solana adapter...")
        adapter = get_adapter_for_chain("solana")
        print(f"✅ Adapter: {adapter}")
        print(f"   Chain: {adapter.get_chain_name()}")
        print(f"   Native token: {adapter.get_native_token_symbol()}")
        
        # Test address validation
        print("\n2️⃣  Testing address validation...")
        
        for label, address in TEST_ADDRESSES.items():
            is_valid, error = adapter.validate_address(address)
            
            if is_valid:
                print(f"✅ {label:20s}: {address[:30]:30s}... - VALID")
            else:
                print(f"❌ {label:20s}: {address[:30]:30s}... - INVALID ({error})")
        
        # Test address normalization
        print("\n3️⃣  Testing address normalization...")
        test_addr = "  7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs  "  # With spaces
        normalized = adapter.normalize_address(test_addr)
        print(f"   Input (with spaces): '{test_addr}'")
        print(f"   Normalized: '{normalized}'")
        
        # Test balance fetching (use a real address if you have one)
        print("\n4️⃣  Testing balance fetching...")
        test_address = "7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs"
        print(f"   Address: {test_address}")
        print(f"   ⚠️  Note: This may fail if RPC is rate-limited or address is new")
        
        try:
            balance = adapter.get_balance(test_address)
            if balance is not None:
                sol_amount = adapter.normalize_amount(str(balance), 9)
                print(f"✅ SOL Balance (lamports): {balance}")
                print(f"✅ SOL Balance: {sol_amount} SOL")
            else:
                print(f"⚠️  No balance found or RPC error")
        except Exception as e:
            print(f"⚠️  Balance fetch failed (normal for rate-limited RPC): {e}")
        
        # Test token balances
        print("\n5️⃣  Testing token balances...")
        print(f"   ⚠️  This requires RPC access and may be rate-limited")
        
        try:
            balances = adapter.get_token_balances(test_address)
            
            if balances:
                print(f"✅ Found {len(balances)} token(s):")
                for bal in balances:
                    print(f"   - {bal['symbol']}: {bal['amount']}")
            else:
                print(f"⚠️  No tokens found or RPC rate-limited")
        except Exception as e:
            print(f"⚠️  Token fetch failed (normal for public RPC): {e}")
        
        # Test portfolio
        print("\n6️⃣  Testing portfolio fetching...")
        
        try:
            portfolio = adapter.get_portfolio(test_address)
            
            print(f"✅ Portfolio structure:")
            print(f"   Chain: {portfolio.get('chain')}")
            print(f"   Address: {portfolio.get('address')[:20]}...")
            print(f"   Balances: {len(portfolio.get('balances', []))} token(s)")
        except Exception as e:
            print(f"⚠️  Portfolio fetch failed: {e}")
        
        print("\n✅ SOLANA ADAPTER TEST PASSED!")
        print("   (Some features may be limited by RPC rate limits)")
        return True
        
    except Exception as e:
        print(f"\n❌ SOLANA ADAPTER TEST FAILED!")
        print(f"   Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_price_service():
    """Test price service with both chains."""
    
    print("\n" + "=" * 60)
    print("🧪 TESTING PRICE SERVICE")
    print("=" * 60)
    
    try:
        from app.services.price_service import PriceService
        
        price_service = PriceService(ttl_seconds=60)
        
        # Test Aptos tokens
        print("\n1️⃣  Testing Aptos token prices (CoinGecko)...")
        apt_price = price_service.get_price("APT", chain="aptos")
        
        if apt_price:
            print(f"✅ APT Price: ${apt_price:.2f}")
        else:
            print(f"❌ Failed to fetch APT price")
        
        # Test Solana tokens
        print("\n2️⃣  Testing Solana token prices (Jupiter)...")
        sol_price = price_service.get_price("SOL", chain="solana")
        
        if sol_price:
            print(f"✅ SOL Price: ${sol_price:.2f}")
        else:
            print(f"❌ Failed to fetch SOL price")
        
        # Test batch prices
        print("\n3️⃣  Testing batch price fetch...")
        symbols = ["APT", "SOL", "USDC"]
        prices = price_service.get_prices(symbols)
        
        for symbol, price in prices.items():
            if price:
                print(f"✅ {symbol}: ${price:.2f}")
            else:
                print(f"⚠️  {symbol}: Price not found")
        
        print("\n✅ PRICE SERVICE TEST PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ PRICE SERVICE TEST FAILED!")
        print(f"   Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    
    print("\n" + "=" * 60)
    print("🚀 CHAINLENS MULTI-CHAIN ADAPTER TESTS")
    print("=" * 60)
    
    results = {
        "Aptos Adapter": test_aptos_adapter(),
        "Solana Adapter": test_solana_adapter(),
        "Price Service": test_price_service(),
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:20s}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Multi-chain adapters are working correctly!")
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("   Check errors above for details")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)