# backend/app/schemas/wallet.py
"""
Wallet Schemas - Updated for Multi-Chain Support

Supports: Aptos, Solana, Ethereum, Polygon, Base (and testnets)
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal, List, Dict
from enum import Enum


# ============================================================
# Chain and Wallet Type Enums
# ============================================================

class ChainType(str, Enum):
    """Supported blockchain networks"""
    # Non-EVM
    APTOS = "aptos"
    SOLANA = "solana"

    # EVM Mainnets
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    BASE = "base"

    # EVM Testnets
    ETHEREUM_SEPOLIA = "ethereum_sepolia"
    POLYGON_AMOY = "polygon_amoy"
    BASE_SEPOLIA = "base_sepolia"

    # Multi-chain (auto-detect)
    EVM = "evm"  # Query all EVM chains


class AddressType(str, Enum):
    """Address type for multi-chain support"""
    EVM = "evm"        # 0x prefixed, 42 chars - works on all EVM chains
    SOLANA = "solana"  # Base58 encoded, 32-44 chars
    APTOS = "aptos"    # 0x prefixed, 66 chars (32 bytes + 0x)


class WalletType(str, Enum):
    """Wallet provider types"""
    # Non-EVM wallets
    PETRA = "petra"          # Aptos
    PHANTOM = "phantom"      # Solana (also supports EVM)
    SOLFLARE = "solflare"    # Solana
    
    # EVM wallets
    METAMASK = "metamask"
    COINBASE = "coinbase"
    RAINBOW = "rainbow"
    RABBY = "rabby"
    
    # Generic
    MANUAL = "manual"
    WALLETCONNECT = "walletconnect"


# Chain to wallet type mapping (which wallets support which chains)
CHAIN_WALLET_COMPATIBILITY = {
    ChainType.APTOS: [WalletType.PETRA, WalletType.MANUAL],
    ChainType.SOLANA: [WalletType.PHANTOM, WalletType.SOLFLARE, WalletType.MANUAL],
    ChainType.ETHEREUM: [WalletType.METAMASK, WalletType.COINBASE, WalletType.RAINBOW, WalletType.RABBY, WalletType.PHANTOM, WalletType.WALLETCONNECT, WalletType.MANUAL],
    ChainType.POLYGON: [WalletType.METAMASK, WalletType.COINBASE, WalletType.RAINBOW, WalletType.RABBY, WalletType.PHANTOM, WalletType.WALLETCONNECT, WalletType.MANUAL],
    ChainType.BASE: [WalletType.METAMASK, WalletType.COINBASE, WalletType.RAINBOW, WalletType.RABBY, WalletType.PHANTOM, WalletType.WALLETCONNECT, WalletType.MANUAL],
    ChainType.ETHEREUM_SEPOLIA: [WalletType.METAMASK, WalletType.COINBASE, WalletType.MANUAL],
    ChainType.POLYGON_AMOY: [WalletType.METAMASK, WalletType.COINBASE, WalletType.MANUAL],
    ChainType.BASE_SEPOLIA: [WalletType.METAMASK, WalletType.COINBASE, WalletType.MANUAL],
    ChainType.EVM: [WalletType.METAMASK, WalletType.COINBASE, WalletType.RAINBOW, WalletType.RABBY, WalletType.WALLETCONNECT, WalletType.MANUAL],
}


# EVM chains that share addresses (testnet mode)
EVM_TESTNET_CHAINS = ["ethereum_sepolia", "polygon_amoy", "base_sepolia"]

# EVM chains that share addresses (mainnet mode)
EVM_MAINNET_CHAINS = ["ethereum", "polygon", "base"]


# ============================================================
# Address Detection Utilities
# ============================================================

def detect_address_type(address: str) -> AddressType:
    """
    Detect the type of blockchain address based on format.

    - EVM: 0x prefix + 40 hex chars (42 total)
    - Aptos: 0x prefix + 64 hex chars (66 total)
    - Solana: Base58 encoded, 32-44 chars, no 0x prefix
    """
    if not address:
        raise ValueError("Address cannot be empty")

    addr = address.strip()

    # Check for 0x prefix (EVM or Aptos)
    if addr.startswith("0x") or addr.startswith("0X"):
        hex_part = addr[2:]

        # Check if valid hex
        try:
            int(hex_part, 16)
        except ValueError:
            raise ValueError(f"Invalid hex address: {addr}")

        # EVM addresses are 40 hex chars (20 bytes)
        if len(hex_part) == 40:
            return AddressType.EVM

        # Aptos addresses are 64 hex chars (32 bytes)
        elif len(hex_part) == 64:
            return AddressType.APTOS

        # Could be short Aptos address (variable length)
        elif len(hex_part) < 64:
            return AddressType.APTOS

        else:
            raise ValueError(f"Unknown 0x address format with {len(hex_part)} hex chars")

    # No 0x prefix - likely Solana (Base58)
    else:
        # Solana addresses are Base58 encoded, typically 32-44 chars
        if 32 <= len(addr) <= 44:
            # Basic Base58 character check
            import string
            base58_chars = set(string.digits + string.ascii_letters) - set('0OIl')
            if all(c in base58_chars for c in addr):
                return AddressType.SOLANA

        raise ValueError(f"Unknown address format: {addr[:20]}...")


def get_chains_for_address(address: str, testnet: bool = True) -> List[str]:
    """
    Get all chains that an address can be used on.

    Args:
        address: Wallet address
        testnet: If True, return testnet chains; else mainnet chains

    Returns:
        List of chain identifiers
    """
    addr_type = detect_address_type(address)

    if addr_type == AddressType.EVM:
        return EVM_TESTNET_CHAINS if testnet else EVM_MAINNET_CHAINS
    elif addr_type == AddressType.SOLANA:
        return ["solana"]
    elif addr_type == AddressType.APTOS:
        return ["aptos"]
    else:
        return []


# ============================================================
# Wallet Request Models
# ============================================================

class WalletCreateRequest(BaseModel):
    """Request to add a new wallet."""
    address: str = Field(min_length=10, max_length=200)
    chain: Optional[ChainType] = Field(
        default=None,
        description="Blockchain network (optional - auto-detected for EVM addresses)"
    )
    type: WalletType = Field(default=WalletType.MANUAL, description="Wallet provider type")
    label: str = Field(default="Main Wallet", min_length=1, max_length=100)
    is_primary: bool = False

    @field_validator('address')
    @classmethod
    def validate_address_format(cls, v: str) -> str:
        """Basic address format validation"""
        v = v.strip()
        if not v:
            raise ValueError("Address cannot be empty")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f5bE21",
                "chain": "evm",
                "type": "metamask",
                "label": "My EVM Wallet",
                "is_primary": True
            }
        }


class WalletUpdateLabelRequest(BaseModel):
    """Request to update wallet label."""
    label: str = Field(min_length=1, max_length=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "label": "Trading Wallet"
            }
        }


class WalletSetPrimaryRequest(BaseModel):
    """Request to set a wallet as primary (by address)."""
    address: str = Field(min_length=10, max_length=200)
    chain: Optional[ChainType] = Field(default=None, description="Chain (optional, for disambiguation)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f5bE21",
                "chain": "ethereum_sepolia"
            }
        }


# ============================================================
# Wallet Response Models
# ============================================================

class WalletResponse(BaseModel):
    """Wallet information returned to client."""
    id: str
    user_id: str
    address: str
    chain: str = Field(description="Blockchain network (e.g., ethereum, polygon, base)")
    type: str = Field(description="Wallet provider type (e.g., metamask, manual)")
    label: str
    is_primary: bool
    created_at: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "user_id": "507f191e810c19729de860ea",
                "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f5bE21",
                "chain": "ethereum_sepolia",
                "type": "metamask",
                "label": "Main Wallet",
                "is_primary": True,
                "created_at": "2025-01-15T10:30:00.000Z"
            }
        }


class WalletListResponse(BaseModel):
    """List of wallets with metadata."""
    wallets: List[WalletResponse]
    total: int
    primary: Optional[WalletResponse] = None
    by_chain: Optional[dict] = Field(
        default=None, 
        description="Wallet count by chain"
    )


class WalletBalanceResponse(BaseModel):
    """Token balance for a wallet."""
    symbol: str
    address: str = Field(description="Token contract address")
    decimals: int
    raw: str = Field(description="Raw balance value")
    amount: float
    usd_price: Optional[float] = None
    usd_value: Optional[float] = None
    chain: str


class WalletPortfolioResponse(BaseModel):
    """Complete portfolio for a wallet."""
    wallet_address: str
    chain: str
    balances: List[WalletBalanceResponse]
    total_usd_value: float
    token_count: int


class MultiChainBalanceResponse(BaseModel):
    """Balance for a token on a specific chain."""
    symbol: str
    address: str = Field(description="Token contract address")
    decimals: int
    raw: str = Field(description="Raw balance value")
    amount: float
    usd_price: Optional[float] = None
    usd_value: Optional[float] = None
    chain: str


class MultiChainPortfolioResponse(BaseModel):
    """Aggregated portfolio across multiple chains for an EVM wallet."""
    wallet_address: str
    address_type: str = Field(description="Type of address: evm, solana, aptos")
    chains_queried: List[str]
    balances_by_chain: Dict[str, List[WalletBalanceResponse]] = Field(
        description="Token balances grouped by chain"
    )
    all_balances: List[MultiChainBalanceResponse] = Field(
        description="All balances flattened with chain info"
    )
    total_usd_value: float
    total_token_count: int
    chain_totals: Dict[str, float] = Field(
        description="USD total per chain"
    )


# ============================================================
# Chain Info Response
# ============================================================

class ChainInfoResponse(BaseModel):
    """Information about a supported chain."""
    id: str
    name: str
    type: str = Field(description="Chain type: evm, move, svm")
    native_token: str
    chain_id: Optional[int] = Field(default=None, description="EVM chain ID")
    is_testnet: bool = False
    available: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "ethereum_sepolia",
                "name": "Ethereum Sepolia",
                "type": "evm",
                "native_token": "ETH",
                "chain_id": 11155111,
                "is_testnet": True,
                "available": True
            }
        }


class SupportedChainsResponse(BaseModel):
    """List of all supported chains."""
    chains: List[ChainInfoResponse]
    total: int
    evm_chains: int
    non_evm_chains: int