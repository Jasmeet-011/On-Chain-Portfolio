#!/usr/bin/env python3
"""
Test Script - EVM Adapters

Tests connectivity and basic functionality for all EVM chains.
Run with: python test_evm_adapters.py
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all imports work."""
    print("\n" + "=" * 60)
    print("Testing Imports")
    print("=" * 60)
    
    try:
        from web3 import Web3
        print("✅ web3 imported successfully")
    except ImportError:
        print("❌ web3 not installed. Run: pip install web3")
        return False
    
    try:
        from app.services.adapters import (
            get_adapter_for_chain,
            list_supported_chains,
            SUPPORTED_CHAINS
        )
        print("✅ Adapter factory imported")
    except ImportError as e:
        print(f"❌ Failed to import adapters: {e}")
        return False
    
    try:
        from app.services.adapters.ethereum_adapter import EthereumSepoliaAdapter
        from app.services.adapters.polygon_adapter import PolygonAmoyAdapter
        from app.services.adapters.base_network_adapter import BaseSepoliaAdapter
        print("✅ All EVM adapters imported")
    except ImportError as e:
        print(f"❌ Failed to import EVM adapters: {e}")
        return False
    
    return True


def test_supported_chains():
    """Test listing supported chains."""
    print("\n" + "=" * 60)
    print("Supported Chains")
    print("=" * 60)
    
    from app.services.adapters import list_supported_chains
    
    chains = list_supported_chains(include_testnets=True)
    
    print(f"\nTotal chains: {len(chains)}")
    print("\nChain List:")
    
    for chain in chains:
        status = "✅" if chain.get("available") else "❌"
        testnet = " (testnet)" if chain.get("is_testnet") else ""
        print(f"  {status} {chain['id']}: {chain['name']}{testnet} - {chain['native_token']}")
    
    return True


def test_ethereum_sepolia():
    """Test Ethereum Sepolia adapter."""
    print("\n" + "=" * 60)
    print("Testing Ethereum Sepolia")
    print("=" * 60)
    
    from app.services.adapters import get_adapter_for_chain
    
    try:
        adapter = get_adapter_for_chain("ethereum_sepolia")
        print(f"✅ Adapter created: {adapter.CHAIN_NAME}")
        
        # Test chain info
        info = adapter.get_chain_info()
        print(f"  Chain ID: {info.get('chain_id')}")
        print(f"  Block Number: {info.get('block_number')}")
        print(f"  Connected: {info.get('connected')}")
        
        # Test address validation
        test_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f5bE21"
        is_valid, error = adapter.validate_address(test_address)
        print(f"  Address validation: {'✅' if is_valid else '❌'} {error or ''}")
        
        # Test normalization
        normalized = adapter.normalize_address(test_address.lower())
        print(f"  Normalized: {normalized}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_polygon_amoy():
    """Test Polygon Amoy adapter."""
    print("\n" + "=" * 60)
    print("Testing Polygon Amoy")
    print("=" * 60)
    
    from app.services.adapters import get_adapter_for_chain
    
    try:
        adapter = get_adapter_for_chain("polygon_amoy")
        print(f"✅ Adapter created: {adapter.CHAIN_NAME}")
        
        info = adapter.get_chain_info()
        print(f"  Chain ID: {info.get('chain_id')}")
        print(f"  Block Number: {info.get('block_number')}")
        print(f"  Connected: {info.get('connected')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_base_sepolia():
    """Test Base Sepolia adapter."""
    print("\n" + "=" * 60)
    print("Testing Base Sepolia")
    print("=" * 60)
    
    from app.services.adapters import get_adapter_for_chain
    
    try:
        adapter = get_adapter_for_chain("base_sepolia")
        print(f"✅ Adapter created: {adapter.CHAIN_NAME}")
        
        info = adapter.get_chain_info()
        print(f"  Chain ID: {info.get('chain_id')}")
        print(f"  Block Number: {info.get('block_number')}")
        print(f"  Connected: {info.get('connected')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_balance_fetch():
    """Test fetching balances from a known address."""
    print("\n" + "=" * 60)
    print("Testing Balance Fetch")
    print("=" * 60)
    
    from app.services.adapters import get_adapter_for_chain
    
    # Vitalik's address (has tokens on most chains)
    test_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    
    for chain in ["ethereum_sepolia", "polygon_amoy", "base_sepolia"]:
        print(f"\n{chain}:")
        try:
            adapter = get_adapter_for_chain(chain)
            
            # Get native balance
            native = adapter.get_native_balance(test_address)
            if native:
                print(f"  {native['symbol']}: {native['amount']}")
            else:
                print(f"  No native balance")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("🧪 EVM ADAPTER TEST SUITE")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    
    if results[0][1]:  # Only continue if imports work
        results.append(("Supported Chains", test_supported_chains()))
        results.append(("Ethereum Sepolia", test_ethereum_sepolia()))
        results.append(("Polygon Amoy", test_polygon_amoy()))
        results.append(("Base Sepolia", test_base_sepolia()))
        results.append(("Balance Fetch", test_balance_fetch()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)