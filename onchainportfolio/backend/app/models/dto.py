# backend/app/models/dto.py - UPDATED WITH CHAIN FIELD

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


# ============================================================
# Chat Request/Response Models
# ============================================================

class ConversationTurn(BaseModel):
    """A single turn in a conversation."""
    role: str   # "user" or "assistant"
    text: str


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    question: str = Field(min_length=1, max_length=1000)
    scope: str = "all"  # "all", "primary", or specific wallet address
    history: Optional[List["ConversationTurn"]] = None  # Prior conversation turns


class WalletPortfolioResult(BaseModel):
    """Result of fetching portfolio for a single wallet."""
    address: str
    label: str
    chain: str  # ✅ NEW: 'aptos' or 'solana'
    success: bool
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class TokenAggregate(BaseModel):
    """Aggregated token data across wallets."""
    symbol: str
    total_amount: float
    total_usd_value: float
    wallet_count: int


class AggregatedPortfolio(BaseModel):
    """Aggregated portfolio across all wallets."""
    total_usd_value: float
    total_wallets: int
    successful_wallets: int
    failed_wallets: int
    by_token: Optional[List[TokenAggregate]] = None
    wallets: Optional[List[Dict[str, Any]]] = None  # Individual wallet data with chain


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    answer: str
    portfolio: AggregatedPortfolio
    wallet_results: List[WalletPortfolioResult]
    scope_used: str


# ============================================================
# Wallet Management Models
# ============================================================

class WalletCreate(BaseModel):
    """Model for creating a new wallet."""
    address: str
    chain: str = "aptos"  # 'aptos' or 'solana'
    type: str = "manual"  # 'manual', 'petra', 'phantom', etc.
    label: str = "Wallet"
    is_primary: bool = False


class WalletUpdate(BaseModel):
    """Model for updating wallet label."""
    label: str


class SetPrimaryWallet(BaseModel):
    """Model for setting primary wallet."""
    address: str


class WalletResponse(BaseModel):
    """Response model for wallet data."""
    id: str
    user_id: str
    address: str
    chain: str  # 'aptos' or 'solana'
    type: str
    label: str
    is_primary: bool
    created_at: str


class WalletsListResponse(BaseModel):
    """Response model for list of wallets."""
    wallets: List[WalletResponse]
    total: int
    primary: Optional[WalletResponse] = None
    by_chain: Optional[Dict[str, int]] = None  # Count by chain


# ============================================================
# Balance/Portfolio Models
# ============================================================

class TokenBalance(BaseModel):
    """Token balance data."""
    symbol: str
    address: str
    decimals: int
    raw: str
    amount: float
    usd_price: Optional[float] = None
    usd_value: Optional[float] = None
    change_24h: Optional[float] = None   # 24-hour price change %


class PortfolioResponse(BaseModel):
    """Portfolio response for a single wallet."""
    balances: List[TokenBalance]
    total_usd_value: float
    chain: Optional[str] = None  # ✅ NEW: Chain info


# ============================================================
# Transaction Models
# ============================================================

class Transaction(BaseModel):
    """Transaction data."""
    hash: str
    version: Optional[str] = None
    success: bool
    timestamp: str
    gas_used: int
    sender: str
    sequence_number: Optional[int] = None
    type: str
    function: Optional[str] = None
    chain: Optional[str] = None  # ✅ NEW: Chain info


class TransactionDetail(Transaction):
    """Detailed transaction data."""
    payload: Optional[Dict[str, Any]] = None
    events: Optional[List[Dict[str, Any]]] = None
    changes: Optional[List[Dict[str, Any]]] = None


class TransactionsResponse(BaseModel):
    """Response for transaction list."""
    transactions: List[Transaction]
    total: int
    limit: int
    offset: int