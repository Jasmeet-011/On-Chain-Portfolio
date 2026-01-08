# app/config.py
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    env: str = Field(default=os.getenv("ENV", "dev"))
    
    # Aptos Settings
    aptos_node_url: str = Field(
        default=os.getenv("APTOS_NODE_URL", "https://fullnode.testnet.aptoslabs.com/v1")
    )
    
    # Solana Settings (NEW)
    solana_rpc_url: str = Field(
        default=os.getenv("SOLANA_RPC_URL", "https://api.testnet.solana.com")
    )
    solana_rpc_backup: str = Field(
        default=os.getenv("SOLANA_RPC_BACKUP", "")
    )
    
    # Cache TTL
    prices_ttl_seconds: int = int(os.getenv("PRICES_TTL_SECONDS", "60"))
    balances_ttl_seconds: int = int(os.getenv("BALANCES_TTL_SECONDS", "30"))
    
    # AI
    gemini_api_key: str = Field(default=os.getenv("GEMINI_API_KEY", ""))
    
    # MongoDB
    mongodb_uri: str = Field(default=os.getenv("MONGODB_URI", "mongodb://localhost:27017"))
    mongo_db_name: str = Field(default=os.getenv("MONGO_DB_NAME", "chainiq"))
    
    # JWT Settings
    jwt_secret_key: str = Field(
        default=os.getenv("JWT_SECRET_KEY", "your-super-secret-key-change-in-production")
    )
    jwt_algorithm: str = Field(default="HS256")
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24 hours
    
    # Wallet Validation Settings
    validate_wallet_on_chain: bool = Field(
        default=os.getenv("VALIDATE_WALLET_ON_CHAIN", "false").lower() == "true"
    )
    
    # Supported Chains (NEW)
    supported_chains: list[str] = ["aptos", "solana"]

settings = Settings()