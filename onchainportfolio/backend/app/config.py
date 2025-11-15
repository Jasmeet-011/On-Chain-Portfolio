from pydantic import BaseModel, Field
import os

class Settings(BaseModel):
    env: str = Field(default=os.getenv("ENV", "dev"))
    # Aptos public fullnode URL; defaults to mainnet
    aptos_node_url: str = Field(default=os.getenv("APTOS_NODE_URL", "https://fullnode.mainnet.aptoslabs.com/v1"))
    # Simple in-process cache TTLs (seconds)
    prices_ttl_seconds: int = int(os.getenv("PRICES_TTL_SECONDS", "60"))
    balances_ttl_seconds: int = int(os.getenv("BALANCES_TTL_SECONDS", "30"))

settings = Settings()
