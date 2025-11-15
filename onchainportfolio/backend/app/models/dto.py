from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from decimal import Decimal
from datetime import datetime

class TokenBalance(BaseModel):
    symbol: str
    address: str = Field(description="Token type address")
    decimals: int
    raw: str
    amount: Decimal
    usd_price: Optional[Decimal] = None
    usd_value: Optional[Decimal] = None

class PortfolioSummary(BaseModel):
    address: str
    total_usd: Decimal
    tokens: List[TokenBalance]
    by_token: Dict[str, Decimal]
    updated_at: datetime
