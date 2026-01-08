# app/services/adapters/__init__.py
"""
Blockchain adapter module.

Provides a unified interface for interacting with different blockchains.
"""

from typing import Optional
from .base import ChainAdapter
from .aptos_adapter import AptosAdapter
from .solana_adapter import SolanaAdapter

__all__ = [
    "ChainAdapter",
    "AptosAdapter",
    "SolanaAdapter",
    "get_adapter",
    "get_adapter_for_chain",
]


def get_adapter_for_chain(
    chain: str,
    rpc_url: Optional[str] = None,
    backup_rpc_url: Optional[str] = None
) -> ChainAdapter:
    """
    Factory function to get the appropriate adapter for a chain.
    
    Args:
        chain: Chain identifier ("aptos", "solana", etc.)
        rpc_url: RPC endpoint (if None, uses default from config)
        backup_rpc_url: Backup RPC endpoint (optional, for Solana)
    
    Returns:
        ChainAdapter instance for the specified chain
    
    Raises:
        ValueError: If chain is not supported
    
    Example:
        >>> adapter = get_adapter_for_chain("aptos")
        >>> balances = adapter.get_token_balances("0x123...")
    """
    from app.config import settings  # Import once at top of function
    
    chain_lower = chain.lower().strip()
    
    if chain_lower == "aptos":
        # Use provided RPC or default from settings
        url = rpc_url or settings.aptos_node_url
        return AptosAdapter(rpc_url=url)
    
    elif chain_lower == "solana":
        # Use provided RPC or default from settings
        url = rpc_url or settings.solana_rpc_url
        # Use provided backup or default from settings
        backup = backup_rpc_url or (settings.solana_rpc_backup if settings.solana_rpc_backup else None)
        return SolanaAdapter(rpc_url=url, backup_rpc_url=backup)
    
    else:
        # Try to get supported chains from settings, fallback to hardcoded
        supported = getattr(settings, "supported_chains", ["aptos", "solana"])
        raise ValueError(
            f"Unsupported chain: {chain}. "
            f"Supported chains: {', '.join(supported)}"
        )


# Convenience alias
get_adapter = get_adapter_for_chain