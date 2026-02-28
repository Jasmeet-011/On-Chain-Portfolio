# backend/app/services/adapters/__init__.py
"""
Chain Adapter Factory

Provides unified interface for getting blockchain adapters.
Supports: Aptos, Solana, Ethereum, Polygon, Base (and their testnets)
"""
from typing import Optional, Dict, Any, List
import os

from .base_chain_adapter import BaseChainAdapter
from .base_network_adapter import BaseNetworkAdapter, BaseSepoliaAdapter, get_base_adapter
# Import Aptos adapter
try:
    from .aptos_adapter import AptosAdapter
    APTOS_AVAILABLE = True
except ImportError:
    APTOS_AVAILABLE = False
    print("[ADAPTERS] ⚠️ Aptos adapter not available")

# Import Solana adapter
try:
    from .solana_adapter import SolanaAdapter
    SOLANA_AVAILABLE = True
except ImportError:
    SOLANA_AVAILABLE = False
    print("[ADAPTERS] ⚠️ Solana adapter not available")

# Import EVM adapters
try:
    from .evm_adapter import EVMAdapter
    from .ethereum_adapter import (
        EthereumAdapter, 
        EthereumSepoliaAdapter,
        get_ethereum_adapter
    )
    from .polygon_adapter import (
        PolygonAdapter,
        PolygonAmoyAdapter,
        get_polygon_adapter
    )
    from .base_network_adapter import (
        BaseNetworkAdapter as BaseMainnetAdapter,
        BaseSepoliaAdapter,
        get_base_adapter
    )
    EVM_AVAILABLE = True
except ImportError as e:
    EVM_AVAILABLE = False
    print(f"[ADAPTERS] ⚠️ EVM adapters not available: {e}")
    print("[ADAPTERS] Install web3 with: pip install web3")


# ============================================================
# Supported Chains Configuration
# ============================================================

SUPPORTED_CHAINS = {
    # Non-EVM Chains
    "aptos": {
        "name": "Aptos",
        "type": "move",
        "native_token": "APT",
        "testnet": "testnet",
        "mainnet": "mainnet",
        "available": APTOS_AVAILABLE
    },
    "solana": {
        "name": "Solana",
        "type": "svm",
        "native_token": "SOL",
        "testnet": "devnet",
        "mainnet": "mainnet",
        "available": SOLANA_AVAILABLE
    },
    
    # EVM Chains
    "ethereum": {
        "name": "Ethereum",
        "type": "evm",
        "native_token": "ETH",
        "chain_id": 1,
        "testnet": "sepolia",
        "testnet_chain_id": 11155111,
        "mainnet": "mainnet",
        "available": EVM_AVAILABLE
    },
    "ethereum_sepolia": {
        "name": "Ethereum Sepolia",
        "type": "evm",
        "native_token": "ETH",
        "chain_id": 11155111,
        "is_testnet": True,
        "parent_chain": "ethereum",
        "available": EVM_AVAILABLE
    },
    "polygon": {
        "name": "Polygon",
        "type": "evm",
        "native_token": "MATIC",
        "chain_id": 137,
        "testnet": "amoy",
        "testnet_chain_id": 80002,
        "mainnet": "mainnet",
        "available": EVM_AVAILABLE
    },
    "polygon_amoy": {
        "name": "Polygon Amoy",
        "type": "evm",
        "native_token": "MATIC",
        "chain_id": 80002,
        "is_testnet": True,
        "parent_chain": "polygon",
        "available": EVM_AVAILABLE
    },
    "base": {
        "name": "Base",
        "type": "evm",
        "native_token": "ETH",
        "chain_id": 8453,
        "testnet": "sepolia",
        "testnet_chain_id": 84532,
        "mainnet": "mainnet",
        "available": EVM_AVAILABLE
    },
    "base_sepolia": {
        "name": "Base Sepolia",
        "type": "evm",
        "native_token": "ETH",
        "chain_id": 84532,
        "is_testnet": True,
        "parent_chain": "base",
        "available": EVM_AVAILABLE
    },
}

# Testnet aliases for easier use
TESTNET_ALIASES = {
    "eth_testnet": "ethereum_sepolia",
    "eth_sepolia": "ethereum_sepolia",
    "polygon_testnet": "polygon_amoy",
    "matic_testnet": "polygon_amoy",
    "base_testnet": "base_sepolia",
    "aptos_testnet": "aptos",      # Uses testnet RPC
    "solana_testnet": "solana",    # Uses devnet RPC
    # Generic EVM wallets (MetaMask / Coinbase / WalletConnect) default to Ethereum Sepolia
    "evm": "ethereum_sepolia",
}


# ============================================================
# Adapter Factory
# ============================================================

def get_adapter_for_chain(
    chain: str,
    rpc_url: str = None,
    network: str = None  # "mainnet" or "testnet"
) -> BaseChainAdapter:
    """
    Get the appropriate adapter for a blockchain.
    
    Args:
        chain: Chain identifier (e.g., "ethereum", "polygon", "aptos")
        rpc_url: Custom RPC URL (optional)
        network: "mainnet" or "testnet" (optional, for EVM chains)
    
    Returns:
        Chain adapter instance
    
    Raises:
        ValueError: If chain is not supported
    """
    # Resolve aliases
    chain_lower = chain.lower().strip()
    if chain_lower in TESTNET_ALIASES:
        chain_lower = TESTNET_ALIASES[chain_lower]
    
    # Check if chain is supported
    if chain_lower not in SUPPORTED_CHAINS:
        available = [c for c, info in SUPPORTED_CHAINS.items() if info.get("available")]
        raise ValueError(
            f"Unsupported chain: {chain}. "
            f"Available chains: {', '.join(available)}"
        )
    
    chain_info = SUPPORTED_CHAINS[chain_lower]
    
    if not chain_info.get("available"):
        raise ValueError(
            f"Chain {chain} is not available. "
            f"Please install required dependencies."
        )
    
    # ============================================================
    # Non-EVM Chains
    # ============================================================
    
    if chain_lower == "aptos":
        if not APTOS_AVAILABLE:
            raise ValueError("Aptos adapter not available")
        
        # Use testnet RPC by default
        default_rpc = os.getenv(
            "APTOS_RPC_URL",
            "https://fullnode.testnet.aptoslabs.com/v1"
        )
        return AptosAdapter(rpc_url=rpc_url or default_rpc)
    
    elif chain_lower == "solana":
        if not SOLANA_AVAILABLE:
            raise ValueError("Solana adapter not available")
        
        # Use devnet by default
        default_rpc = os.getenv(
            "SOLANA_RPC_URL",
            "https://api.devnet.solana.com"
        )
        return SolanaAdapter(rpc_url=rpc_url or default_rpc)
    
    # ============================================================
    # EVM Chains
    # ============================================================
    
    if not EVM_AVAILABLE:
        raise ValueError(
            f"EVM adapters not available. "
            f"Install web3 with: pip install web3"
        )
    
    # Ethereum
    if chain_lower in ["ethereum", "ethereum_sepolia"]:
        if chain_lower == "ethereum_sepolia" or network == "testnet":
            rpc = rpc_url or os.getenv("ETHEREUM_SEPOLIA_RPC_URL")
            return EthereumSepoliaAdapter(rpc_url=rpc)
        else:
            rpc = rpc_url or os.getenv("ETHEREUM_RPC_URL")
            return EthereumAdapter(rpc_url=rpc)
    
    # Polygon
    elif chain_lower in ["polygon", "polygon_amoy"]:
        if chain_lower == "polygon_amoy" or network == "testnet":
            rpc = rpc_url or os.getenv("POLYGON_AMOY_RPC_URL")
            return PolygonAmoyAdapter(rpc_url=rpc)
        else:
            rpc = rpc_url or os.getenv("POLYGON_RPC_URL")
            return PolygonAdapter(rpc_url=rpc)
    
    # Base
    elif chain_lower in ["base", "base_sepolia"]:
        if chain_lower == "base_sepolia" or network == "testnet":
            rpc = rpc_url or os.getenv("BASE_SEPOLIA_RPC_URL")
            return BaseSepoliaAdapter(rpc_url=rpc)
        else:
            rpc = rpc_url or os.getenv("BASE_RPC_URL")
            return BaseMainnetAdapter(rpc_url=rpc)
    
    else:
        raise ValueError(f"Unknown chain: {chain}")


# ============================================================
# Utility Functions
# ============================================================

def list_supported_chains(include_testnets: bool = True) -> List[Dict[str, Any]]:
    """
    Get list of all supported chains.
    
    Args:
        include_testnets: Include testnet chains
    
    Returns:
        List of chain info dictionaries
    """
    chains = []
    
    for chain_id, info in SUPPORTED_CHAINS.items():
        if not include_testnets and info.get("is_testnet"):
            continue
        
        chains.append({
            "id": chain_id,
            "name": info["name"],
            "type": info["type"],
            "native_token": info["native_token"],
            "available": info.get("available", False),
            "is_testnet": info.get("is_testnet", False),
            "chain_id": info.get("chain_id")
        })
    
    return chains


def get_chain_info(chain: str) -> Optional[Dict[str, Any]]:
    """
    Get information about a specific chain.
    
    Args:
        chain: Chain identifier
    
    Returns:
        Chain info dictionary or None
    """
    chain_lower = chain.lower().strip()
    
    # Resolve aliases
    if chain_lower in TESTNET_ALIASES:
        chain_lower = TESTNET_ALIASES[chain_lower]
    
    return SUPPORTED_CHAINS.get(chain_lower)


def is_evm_chain(chain: str) -> bool:
    """Check if a chain is EVM-compatible."""
    info = get_chain_info(chain)
    return info.get("type") == "evm" if info else False


def get_native_token(chain: str) -> Optional[str]:
    """Get native token symbol for a chain."""
    info = get_chain_info(chain)
    return info.get("native_token") if info else None


def get_testnet_for_chain(chain: str) -> Optional[str]:
    """Get testnet chain ID for a mainnet chain."""
    info = get_chain_info(chain)
    if not info:
        return None
    
    testnet = info.get("testnet")
    if testnet:
        # Return full testnet chain ID
        return f"{chain}_{testnet}" if testnet != "testnet" else f"{chain}_testnet"
    
    return None


# ============================================================
# Export all adapters and utilities
# ============================================================

__all__ = [
    # Base
    "BaseChainAdapter",
    "get_adapter_for_chain",
    
    # Aptos
    "AptosAdapter",
    
    # Solana
    "SolanaAdapter",
    
    # EVM Base
    "EVMAdapter",
    
    # Ethereum
    "EthereumAdapter",
    "EthereumSepoliaAdapter",
    "get_ethereum_adapter",
    
    # Polygon
    "PolygonAdapter",
    "PolygonAmoyAdapter",
    "get_polygon_adapter",
    
    # Base Chain
    "BaseMainnetAdapter",
    "BaseSepoliaAdapter",
    "get_base_adapter",
    
    # Utilities
    "SUPPORTED_CHAINS",
    "list_supported_chains",
    "get_chain_info",
    "is_evm_chain",
    "get_native_token",
    "get_testnet_for_chain",
]