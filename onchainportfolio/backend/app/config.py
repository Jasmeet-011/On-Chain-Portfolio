# app/config.py
from pydantic import BaseModel, Field
from typing import Dict, Optional, List
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    # ============================================================
    # General Settings
    # ============================================================
    env: str = Field(default=os.getenv("ENV", "dev"))
    debug: bool = Field(default=os.getenv("DEBUG", "false").lower() == "true")
    
    # ============================================================
    # Non-EVM Chain RPCs
    # ============================================================
    
    # Aptos
    aptos_node_url: str = Field(
        default=os.getenv("APTOS_RPC_URL") or os.getenv(
            "APTOS_NODE_URL", 
            "https://fullnode.testnet.aptoslabs.com/v1"
        )
    )
    
    # Solana (use devnet for testing, mainnet-beta for production)
    solana_rpc_url: str = Field(
        default=os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com")
    )
    solana_rpc_backup: str = Field(
        default=os.getenv("SOLANA_RPC_BACKUP", "")
    )
    
    # ============================================================
    # EVM Chain RPCs (Testnets)
    # ============================================================
    
    ethereum_sepolia_rpc_url: str = Field(
        default=os.getenv("ETHEREUM_SEPOLIA_RPC_URL", "https://ethereum-sepolia-rpc.publicnode.com")
    )

    polygon_amoy_rpc_url: str = Field(
        default=os.getenv("POLYGON_AMOY_RPC_URL", "https://polygon-amoy-bor-rpc.publicnode.com")
    )

    base_sepolia_rpc_url: str = Field(
        default=os.getenv("BASE_SEPOLIA_RPC_URL", "https://base-sepolia-rpc.publicnode.com")
    )
    
    # ============================================================
    # EVM Chain RPCs (Mainnets)
    # ============================================================
    
    ethereum_rpc_url: str = Field(
        default=os.getenv("ETHEREUM_RPC_URL", "https://eth.llamarpc.com")
    )
    
    polygon_rpc_url: str = Field(
        default=os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com")
    )
    
    base_rpc_url: str = Field(
        default=os.getenv("BASE_RPC_URL", "https://mainnet.base.org")
    )
    
    # ============================================================
    # Database (MongoDB)
    # ============================================================
    
    mongodb_uri: str = Field(
        default=os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    )
    mongo_db_name: str = Field(
        default=os.getenv("MONGO_DB_NAME", "chainiq")
    )
    
    # ============================================================
    # Cache Settings
    # ============================================================

    prices_ttl_seconds: int = int(os.getenv("PRICES_TTL_SECONDS", "300"))
    balances_ttl_seconds: int = int(os.getenv("BALANCES_TTL_SECONDS", "120"))

    # Redis Cache
    redis_url: str = Field(default=os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    redis_enabled: bool = Field(
        default=os.getenv("REDIS_ENABLED", "true").lower() == "true"
    )
    redis_prefix: str = Field(default=os.getenv("REDIS_PREFIX", "chainiq:"))
    
    # ============================================================
    # AI Integration
    # ============================================================
    
    gemini_api_key: str = Field(default=os.getenv("GEMINI_API_KEY", ""))
    
    # ============================================================
    # JWT Authentication
    # ============================================================
    
    jwt_secret_key: str = Field(
        default=os.getenv("JWT_SECRET_KEY", "your-super-secret-key-change-in-production")
    )
    jwt_algorithm: str = Field(default=os.getenv("JWT_ALGORITHM", "HS256"))
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))
    
    # ============================================================
    # External API Keys
    # ============================================================
    
    # Solana NFTs
    helius_api_key: str = Field(default=os.getenv("HELIUS_API_KEY", ""))
    
    # NFT Fallback
    simplehash_api_key: str = Field(default=os.getenv("SIMPLEHASH_API_KEY", ""))
    
    # Price Data
    coingecko_api_key: str = Field(default=os.getenv("COINGECKO_API_KEY", ""))
    
    # EVM Providers (for higher rate limits)
    alchemy_api_key: str = Field(default=os.getenv("ALCHEMY_API_KEY", ""))
    infura_api_key: str = Field(default=os.getenv("INFURA_API_KEY", ""))
    
    # ============================================================
    # Email Service
    # ============================================================
    
    # SendGrid (primary)
    sendgrid_api_key: str = Field(default=os.getenv("SENDGRID_API_KEY", ""))
    
    # SMTP (fallback)
    smtp_host: str = Field(default=os.getenv("SMTP_HOST", ""))
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: str = Field(default=os.getenv("SMTP_USER", ""))
    smtp_password: str = Field(default=os.getenv("SMTP_PASSWORD", ""))
    
    # Email settings
    from_email: str = Field(default=os.getenv("FROM_EMAIL", "alerts@chainlens.app"))
    from_name: str = Field(default=os.getenv("FROM_NAME", "ChainLens"))
    
    # ============================================================
    # Application URLs
    # ============================================================
    
    app_url: str = Field(default=os.getenv("APP_URL", "http://localhost:5173"))
    
    # ============================================================
    # Wallet Validation
    # ============================================================
    
    validate_wallet_on_chain: bool = Field(
        default=os.getenv("VALIDATE_WALLET_ON_CHAIN", "false").lower() == "true"
    )
    
    # ============================================================
    # Feature Flags
    # ============================================================
    
    enable_evm_chains: bool = Field(
        default=os.getenv("ENABLE_EVM_CHAINS", "true").lower() == "true"
    )
    enable_nfts: bool = Field(
        default=os.getenv("ENABLE_NFTS", "true").lower() == "true"
    )
    enable_alerts: bool = Field(
        default=os.getenv("ENABLE_ALERTS", "true").lower() == "true"
    )
    enable_ai_chat: bool = Field(
        default=os.getenv("ENABLE_AI_CHAT", "true").lower() == "true"
    )
    
    # ============================================================
    # Rate Limiting
    # ============================================================
    
    rate_limit_requests: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    rate_limit_window: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    
    # ============================================================
    # Chain Configuration
    # ============================================================
    
    @property
    def supported_chains(self) -> List[str]:
        """Get list of all supported chain identifiers."""
        chains = ["aptos", "solana"]
        
        if self.enable_evm_chains:
            chains.extend([
                "ethereum_sepolia",
                "polygon_amoy",
                "base_sepolia",
                "ethereum",
                "polygon",
                "base",
            ])
        
        return chains
    
    @property
    def chain_configs(self) -> Dict[str, Dict[str, any]]:
        """Get configuration for all supported chains."""
        configs = {
            # Non-EVM Chains
            "aptos": {
                "type": "non-evm",
                "network": "testnet" if "testnet" in self.aptos_node_url else "mainnet",
                "rpc_url": self.aptos_node_url,
                "native_token": "APT",
                "decimals": 8,
                "explorer": "https://explorer.aptoslabs.com",
            },
            "solana": {
                "type": "non-evm",
                "network": "devnet" if "devnet" in self.solana_rpc_url else ("testnet" if "testnet" in self.solana_rpc_url else "mainnet"),
                "rpc_url": self.solana_rpc_url,
                "native_token": "SOL",
                "decimals": 9,
                "explorer": "https://explorer.solana.com",
            },
        }
        
        # Add EVM chains if enabled
        if self.enable_evm_chains:
            configs.update({
                # EVM Testnets
                "ethereum_sepolia": {
                    "type": "evm",
                    "network": "testnet",
                    "rpc_url": self.ethereum_sepolia_rpc_url,
                    "chain_id": 11155111,
                    "native_token": "ETH",
                    "decimals": 18,
                    "explorer": "https://sepolia.etherscan.io",
                },
                "polygon_amoy": {
                    "type": "evm",
                    "network": "testnet",
                    "rpc_url": self.polygon_amoy_rpc_url,
                    "chain_id": 80002,
                    "native_token": "MATIC",
                    "decimals": 18,
                    "explorer": "https://amoy.polygonscan.com",
                },
                "base_sepolia": {
                    "type": "evm",
                    "network": "testnet",
                    "rpc_url": self.base_sepolia_rpc_url,
                    "chain_id": 84532,
                    "native_token": "ETH",
                    "decimals": 18,
                    "explorer": "https://sepolia.basescan.org",
                },
                
                # EVM Mainnets
                "ethereum": {
                    "type": "evm",
                    "network": "mainnet",
                    "rpc_url": self.ethereum_rpc_url,
                    "chain_id": 1,
                    "native_token": "ETH",
                    "decimals": 18,
                    "explorer": "https://etherscan.io",
                },
                "polygon": {
                    "type": "evm",
                    "network": "mainnet",
                    "rpc_url": self.polygon_rpc_url,
                    "chain_id": 137,
                    "native_token": "MATIC",
                    "decimals": 18,
                    "explorer": "https://polygonscan.com",
                },
                "base": {
                    "type": "evm",
                    "network": "mainnet",
                    "rpc_url": self.base_rpc_url,
                    "chain_id": 8453,
                    "native_token": "ETH",
                    "decimals": 18,
                    "explorer": "https://basescan.org",
                },
            })
        
        return configs
    
    # ============================================================
    # Helper Methods
    # ============================================================
    
    def get_rpc_url(self, chain: str) -> str:
        """Get RPC URL for a specific chain."""
        config = self.chain_configs.get(chain.lower())
        return config["rpc_url"] if config else ""
    
    def get_chain_config(self, chain: str) -> Optional[Dict[str, any]]:
        """Get full configuration for a chain."""
        return self.chain_configs.get(chain.lower())
    
    def is_testnet(self, chain: str) -> bool:
        """Check if chain is a testnet."""
        config = self.chain_configs.get(chain.lower())
        return config["network"] == "testnet" if config else False
    
    def is_evm_chain(self, chain: str) -> bool:
        """Check if chain is EVM-based."""
        config = self.chain_configs.get(chain.lower())
        return config["type"] == "evm" if config else False
    
    def get_chain_explorer_url(
        self, 
        chain: str, 
        tx_hash: Optional[str] = None, 
        address: Optional[str] = None
    ) -> str:
        """Generate explorer URL for transaction or address."""
        config = self.chain_configs.get(chain.lower())
        if not config:
            return ""
        
        base_url = config["explorer"]
        
        if tx_hash:
            return f"{base_url}/tx/{tx_hash}"
        elif address:
            return f"{base_url}/address/{address}"
        
        return base_url


# Create singleton instance
settings = Settings()


# ============================================================
# Startup Validation
# ============================================================

def validate_configuration():
    """Validate critical configuration on startup."""
    errors = []
    warnings = []
    
    # Check MongoDB
    if not settings.mongodb_uri:
        errors.append("❌ MONGODB_URI is not set")
    
    # Check JWT secret
    if settings.jwt_secret_key == "your-super-secret-key-change-in-production":
        warnings.append("⚠️  Using default JWT_SECRET_KEY - CHANGE IN PRODUCTION!")
    
    # Check chain RPCs
    if not settings.aptos_node_url and not settings.solana_rpc_url:
        errors.append("❌ No chain RPC URLs configured")
    
    # Check AI integration
    if settings.enable_ai_chat and not settings.gemini_api_key:
        warnings.append("⚠️  AI chat enabled but GEMINI_API_KEY not set")
    
    # Check email service
    if settings.enable_alerts:
        if not settings.sendgrid_api_key and not settings.smtp_host:
            warnings.append("⚠️  Alerts enabled but no email service configured")
    
    # Print results
    if errors or warnings:
        print("\n" + "="*60)
        print("Configuration Validation")
        print("="*60)
        
        if errors:
            print("\n❌ ERRORS:")
            for error in errors:
                print(f"  {error}")
        
        if warnings:
            print("\n⚠️  WARNINGS:")
            for warning in warnings:
                print(f"  {warning}")
        
        print("="*60 + "\n")
        
        if errors and settings.env == "production":
            raise RuntimeError("Configuration errors in production environment")


# Run validation on import
validate_configuration()