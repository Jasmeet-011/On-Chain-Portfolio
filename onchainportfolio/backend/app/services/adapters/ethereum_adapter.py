# backend/app/services/adapters/ethereum_adapter.py
"""
Ethereum Adapter - EVM adapter for Ethereum network

Supports:
- Mainnet
- Sepolia Testnet (default for testing)
- Goerli Testnet (deprecated but supported)
"""
from typing import Dict, Any

from .evm_adapter import EVMAdapter


# ============================================================
# Ethereum Mainnet Token Registry
# ============================================================

ETHEREUM_MAINNET_TOKENS = {
    # Stablecoins
    "USDC": {
        "address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "decimals": 6,
        "coingecko_id": "usd-coin"
    },
    "USDT": {
        "address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "decimals": 6,
        "coingecko_id": "tether"
    },
    "DAI": {
        "address": "0x6B175474E89094C44Da98b954EesdeC16B7B1365CA",
        "decimals": 18,
        "coingecko_id": "dai"
    },
    
    # Major Tokens
    "WETH": {
        "address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "decimals": 18,
        "coingecko_id": "weth"
    },
    "WBTC": {
        "address": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        "decimals": 8,
        "coingecko_id": "wrapped-bitcoin"
    },
    "LINK": {
        "address": "0x514910771AF9Ca656af840dff83E8264EcF986CA",
        "decimals": 18,
        "coingecko_id": "chainlink"
    },
    "UNI": {
        "address": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
        "decimals": 18,
        "coingecko_id": "uniswap"
    },
    "AAVE": {
        "address": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9",
        "decimals": 18,
        "coingecko_id": "aave"
    },
    "MKR": {
        "address": "0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2",
        "decimals": 18,
        "coingecko_id": "maker"
    },
    "CRV": {
        "address": "0xD533a949740bb3306d119CC777fa900bA034cd52",
        "decimals": 18,
        "coingecko_id": "curve-dao-token"
    },
    "LDO": {
        "address": "0x5A98FcBEA516Cf06857215779Fd812CA3beF1B32",
        "decimals": 18,
        "coingecko_id": "lido-dao"
    },
}

# ============================================================
# Ethereum Sepolia Testnet Token Registry
# ============================================================

ETHEREUM_SEPOLIA_TOKENS = {
    # Sepolia Testnet tokens (different addresses from mainnet)
    "USDC": {
        "address": "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238",  # Circle's Sepolia USDC
        "decimals": 6,
        "coingecko_id": "usd-coin"
    },
    "LINK": {
        "address": "0x779877A7B0D9E8603169DdbD7836e478b4624789",  # Chainlink Sepolia
        "decimals": 18,
        "coingecko_id": "chainlink"
    },
    "WETH": {
        "address": "0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9",  # Wrapped ETH Sepolia
        "decimals": 18,
        "coingecko_id": "weth"
    },
    # Aave V3 Sepolia tokens
    "DAI": {
        "address": "0xFF34B3d4Aee8ddCd6F9AFFFB6Fe49bD371b8a357",  # Aave DAI
        "decimals": 18,
        "coingecko_id": "dai"
    },
    "USDT": {
        "address": "0xaA8E23Fb1079EA71e0a56F48a2aA51851D8433D0",  # Aave USDT
        "decimals": 6,
        "coingecko_id": "tether"
    },
}


class EthereumAdapter(EVMAdapter):
    """
    Ethereum mainnet adapter.
    
    Uses public RPC by default. For production, use Alchemy/Infura.
    """
    
    CHAIN_ID = 1
    CHAIN_NAME = "ethereum"
    NATIVE_TOKEN = "ETH"
    NATIVE_DECIMALS = 18
    
    # Public RPC endpoints (rate limited but free)
    DEFAULT_RPC_URL = "https://eth.llamarpc.com"
    
    # Alternative public RPCs:
    # - https://cloudflare-eth.com
    # - https://rpc.ankr.com/eth
    # - https://1rpc.io/eth
    
    TOKEN_REGISTRY = ETHEREUM_MAINNET_TOKENS
    
    def __init__(self, rpc_url: str = None):
        super().__init__(rpc_url)
        print(f"[ETHEREUM] Mainnet adapter initialized")


class EthereumSepoliaAdapter(EVMAdapter):
    """
    Ethereum Sepolia testnet adapter.
    
    Sepolia is the recommended testnet for Ethereum development.
    """
    
    CHAIN_ID = 11155111
    CHAIN_NAME = "ethereum_sepolia"
    NATIVE_TOKEN = "ETH"
    NATIVE_DECIMALS = 18
    
    # Public Sepolia RPC endpoints
    DEFAULT_RPC_URL = "https://ethereum-sepolia-rpc.publicnode.com"
    
    # Alternative Sepolia RPCs:
    # - https://ethereum-sepolia.blockpi.network/v1/rpc/public
    # - https://sepolia.drpc.org
    # - https://rpc2.sepolia.org
    
    TOKEN_REGISTRY = ETHEREUM_SEPOLIA_TOKENS
    
    def __init__(self, rpc_url: str = None):
        super().__init__(rpc_url)
        print(f"[ETHEREUM_SEPOLIA] Testnet adapter initialized")


# ============================================================
# Factory function for network selection
# ============================================================

def get_ethereum_adapter(
    network: str = "sepolia",
    rpc_url: str = None
) -> EVMAdapter:
    """
    Get Ethereum adapter for specified network.
    
    Args:
        network: "mainnet" or "sepolia"
        rpc_url: Custom RPC URL (optional)
    
    Returns:
        Appropriate Ethereum adapter
    """
    if network == "mainnet":
        return EthereumAdapter(rpc_url)
    elif network == "sepolia":
        return EthereumSepoliaAdapter(rpc_url)
    else:
        raise ValueError(f"Unknown Ethereum network: {network}")