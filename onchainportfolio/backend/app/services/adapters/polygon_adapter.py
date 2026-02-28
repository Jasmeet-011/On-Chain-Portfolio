# backend/app/services/adapters/polygon_adapter.py
"""
Polygon (Matic) Adapter - EVM adapter for Polygon network

Supports:
- Polygon Mainnet
- Polygon Amoy Testnet (replaced Mumbai)
"""
from typing import Dict, Any

from .evm_adapter import EVMAdapter


# ============================================================
# Polygon Mainnet Token Registry
# ============================================================

POLYGON_MAINNET_TOKENS = {
    # Stablecoins
    "USDC": {
        "address": "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",  # Native USDC
        "decimals": 6,
        "coingecko_id": "usd-coin"
    },
    "USDC.e": {
        "address": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",  # Bridged USDC
        "decimals": 6,
        "coingecko_id": "usd-coin"
    },
    "USDT": {
        "address": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
        "decimals": 6,
        "coingecko_id": "tether"
    },
    "DAI": {
        "address": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
        "decimals": 18,
        "coingecko_id": "dai"
    },
    
    # Major Tokens
    "WMATIC": {
        "address": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
        "decimals": 18,
        "coingecko_id": "wmatic"
    },
    "WETH": {
        "address": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
        "decimals": 18,
        "coingecko_id": "weth"
    },
    "WBTC": {
        "address": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
        "decimals": 8,
        "coingecko_id": "wrapped-bitcoin"
    },
    "LINK": {
        "address": "0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39",
        "decimals": 18,
        "coingecko_id": "chainlink"
    },
    "AAVE": {
        "address": "0xD6DF932A45C0f255f85145f286eA0b292B21C90B",
        "decimals": 18,
        "coingecko_id": "aave"
    },
    "UNI": {
        "address": "0xb33EaAd8d922B1083446DC23f610c2567fB5180f",
        "decimals": 18,
        "coingecko_id": "uniswap"
    },
    "CRV": {
        "address": "0x172370d5Cd63279eFa6d502DAB29171933a610AF",
        "decimals": 18,
        "coingecko_id": "curve-dao-token"
    },
    "SUSHI": {
        "address": "0x0b3F868E0BE5597D5DB7fEB59E1CADBb0fdDa50a",
        "decimals": 18,
        "coingecko_id": "sushi"
    },
    "GRT": {
        "address": "0x5fe2B58c013d7601147DcdD68C143A77499f5531",
        "decimals": 18,
        "coingecko_id": "the-graph"
    },
}

# ============================================================
# Polygon Amoy Testnet Token Registry
# (Mumbai deprecated Nov 2024, Amoy is new testnet)
# ============================================================

POLYGON_AMOY_TOKENS = {
    # Amoy Testnet tokens
    "LINK": {
        "address": "0x0Fd9e8d3aF1aaee056EB9e802c3A762a667b1904",
        "decimals": 18,
        "coingecko_id": "chainlink"
    },
    # Note: Amoy has limited token availability
    # Most testing can be done with native MATIC
}


class PolygonAdapter(EVMAdapter):
    """
    Polygon mainnet adapter.
    
    Uses public RPC by default. For production, use Alchemy/Infura.
    """
    
    CHAIN_ID = 137
    CHAIN_NAME = "polygon"
    NATIVE_TOKEN = "MATIC"
    NATIVE_DECIMALS = 18
    
    # Public RPC endpoints
    DEFAULT_RPC_URL = "https://polygon-rpc.com"
    
    # Alternative public RPCs:
    # - https://rpc.ankr.com/polygon
    # - https://polygon.llamarpc.com
    # - https://1rpc.io/matic
    
    TOKEN_REGISTRY = POLYGON_MAINNET_TOKENS
    
    def __init__(self, rpc_url: str = None):
        super().__init__(rpc_url)
        print(f"[POLYGON] Mainnet adapter initialized")


class PolygonAmoyAdapter(EVMAdapter):
    """
    Polygon Amoy testnet adapter.
    
    Amoy replaced Mumbai as the official Polygon testnet in November 2024.
    """
    
    CHAIN_ID = 80002
    CHAIN_NAME = "polygon_amoy"
    NATIVE_TOKEN = "MATIC"
    NATIVE_DECIMALS = 18
    
    # Public Amoy RPC endpoints
    DEFAULT_RPC_URL = "https://polygon-amoy-bor-rpc.publicnode.com"
    
    # Alternative Amoy RPCs:
    # - https://polygon-amoy.blockpi.network/v1/rpc/public
    # - https://polygon-amoy.drpc.org
    
    TOKEN_REGISTRY = POLYGON_AMOY_TOKENS
    
    def __init__(self, rpc_url: str = None):
        super().__init__(rpc_url)
        print(f"[POLYGON_AMOY] Testnet adapter initialized")


# ============================================================
# Factory function for network selection
# ============================================================

def get_polygon_adapter(
    network: str = "amoy",
    rpc_url: str = None
) -> EVMAdapter:
    """
    Get Polygon adapter for specified network.
    
    Args:
        network: "mainnet" or "amoy" (testnet)
        rpc_url: Custom RPC URL (optional)
    
    Returns:
        Appropriate Polygon adapter
    """
    if network == "mainnet":
        return PolygonAdapter(rpc_url)
    elif network == "amoy":
        return PolygonAmoyAdapter(rpc_url)
    else:
        raise ValueError(f"Unknown Polygon network: {network}")