# backend/app/services/adapters/base_network_adapter.py
"""
Base Network Adapter - EVM adapter for Base network (Coinbase L2)

Supports:
- Base Mainnet
- Base Sepolia Testnet
"""
from typing import Dict, Any
from .evm_adapter import EVMAdapter


# ============================================================
# Base Mainnet Token Registry
# ============================================================

BASE_MAINNET_TOKENS = {
    # Stablecoins
    "USDC": {
        "address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "decimals": 6,
        "coingecko_id": "usd-coin"
    },
    "USDbC": {
        "address": "0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA",
        "decimals": 6,
        "coingecko_id": "bridged-usdc-base"
    },
    "DAI": {
        "address": "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb",
        "decimals": 18,
        "coingecko_id": "dai"
    },
    
    # Major Tokens
    "WETH": {
        "address": "0x4200000000000000000000000000000000000006",
        "decimals": 18,
        "coingecko_id": "weth"
    },
    "cbETH": {
        "address": "0x2Ae3F1Ec7F1F5012CFEab0185bfc7aa3cf0DEc22",
        "decimals": 18,
        "coingecko_id": "coinbase-wrapped-staked-eth"
    },
    "rETH": {
        "address": "0xB6fe221Fe9EeF5aBa221c348bA20A1Bf5e73624c",
        "decimals": 18,
        "coingecko_id": "rocket-pool-eth"
    },
    
    # Base Ecosystem Tokens
    "AERO": {
        "address": "0x940181a94A35A4569E4529A3CDfB74e38FD98631",
        "decimals": 18,
        "coingecko_id": "aerodrome-finance"
    },
    "BRETT": {
        "address": "0x532f27101965dd16442E59d40670FaF5eBB142E4",
        "decimals": 18,
        "coingecko_id": "brett"
    },
    "DEGEN": {
        "address": "0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed",
        "decimals": 18,
        "coingecko_id": "degen-base"
    },
    "TOSHI": {
        "address": "0xAC1Bd2486aAf3B5C0fc3Fd868558b082a531B2B4",
        "decimals": 18,
        "coingecko_id": "toshi"
    },
    
    # DeFi Tokens
    "COMP": {
        "address": "0x9e1028F5F1D5eDE59748FFceE5532509976840E0",
        "decimals": 18,
        "coingecko_id": "compound-governance-token"
    },
}

# ============================================================
# Base Sepolia Testnet Token Registry
# ============================================================

BASE_SEPOLIA_TOKENS = {
    "USDC": {
        "address": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
        "decimals": 6,
        "coingecko_id": "usd-coin"
    },
    "WETH": {
        "address": "0x4200000000000000000000000000000000000006",
        "decimals": 18,
        "coingecko_id": "weth"
    },
    "DAI": {
        "address": "0xD8B8E3B9F48c5d8CAa63BC4B1A1B4f83A3b3B283",
        "decimals": 18,
        "coingecko_id": "dai"
    },
}


class BaseNetworkAdapter(EVMAdapter):
    """Base mainnet adapter (Coinbase L2)"""
    
    CHAIN_ID = 8453
    CHAIN_NAME = "base"
    NATIVE_TOKEN = "ETH"
    NATIVE_DECIMALS = 18
    DEFAULT_RPC_URL = "https://mainnet.base.org"
    TOKEN_REGISTRY = BASE_MAINNET_TOKENS
    
    def __init__(self, rpc_url: str = None):
        super().__init__(rpc_url)
        print(f"[BASE] Mainnet adapter initialized")


class BaseSepoliaAdapter(EVMAdapter):
    """Base Sepolia testnet adapter"""
    
    CHAIN_ID = 84532
    CHAIN_NAME = "base_sepolia"
    NATIVE_TOKEN = "ETH"
    NATIVE_DECIMALS = 18
    DEFAULT_RPC_URL = "https://base-sepolia-rpc.publicnode.com"
    TOKEN_REGISTRY = BASE_SEPOLIA_TOKENS
    
    def __init__(self, rpc_url: str = None):
        super().__init__(rpc_url)
        print(f"[BASE_SEPOLIA] Testnet adapter initialized")


def get_base_adapter(network: str = "sepolia", rpc_url: str = None) -> EVMAdapter:
    """Get Base adapter for specified network"""
    if network == "mainnet":
        return BaseNetworkAdapter(rpc_url)
    elif network == "sepolia":
        return BaseSepoliaAdapter(rpc_url)
    else:
        raise ValueError(f"Unknown Base network: {network}")