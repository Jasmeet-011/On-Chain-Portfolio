# app/services/adapters/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal


class ChainAdapter(ABC):
    """
    Abstract base class for blockchain adapters.
    
    Each blockchain (Aptos, Solana, Ethereum, etc.) implements this interface
    to provide a consistent API for portfolio fetching, validation, etc.
    """
    
    def __init__(self, rpc_url: str):
        """
        Initialize the adapter with RPC endpoint.
        
        Args:
            rpc_url: Primary RPC endpoint for this chain
        """
        self.rpc_url = rpc_url
        self.chain_name = self.get_chain_name()
    
    @abstractmethod
    def get_chain_name(self) -> str:
        """
        Return the chain identifier.
        
        Returns:
            Chain name (e.g., "aptos", "solana", "ethereum")
        """
        pass
    
    @abstractmethod
    def validate_address(self, address: str) -> Tuple[bool, Optional[str]]:
        """
        Validate address format for this chain.
        
        Args:
            address: Wallet address to validate
            
        Returns:
            Tuple of (is_valid, error_message)
            - (True, None) if valid
            - (False, "error message") if invalid
        """
        pass
    
    @abstractmethod
    def normalize_address(self, address: str) -> str:
        """
        Normalize address to standard format for this chain.
        
        Args:
            address: Raw address input
            
        Returns:
            Normalized address (e.g., lowercase with 0x prefix for Aptos)
        """
        pass
    
    @abstractmethod
    def get_balance(self, address: str, token_identifier: Optional[str] = None) -> Optional[int]:
        """
        Get raw token balance for an address.
        
        Args:
            address: Wallet address
            token_identifier: Token identifier (mint address, contract address, etc.)
                             If None, get native token balance
        
        Returns:
            Raw balance as integer, or None if error/not found
        """
        pass
    
    @abstractmethod
    def get_token_balances(self, address: str) -> List[Dict[str, Any]]:
        """
        Get all token balances for an address.
        
        Args:
            address: Wallet address
            
        Returns:
            List of token balance dictionaries with structure:
            [
                {
                    "symbol": "APT",
                    "address": "0x1::aptos_coin::AptosCoin",
                    "decimals": 8,
                    "raw": "100000000",
                    "amount": 1.0
                },
                ...
            ]
        """
        pass
    
    @abstractmethod
    def get_portfolio(self, address: str) -> Dict[str, Any]:
        """
        Get complete portfolio data for an address (balances + metadata).
        
        Args:
            address: Wallet address
            
        Returns:
            Portfolio dictionary with structure:
            {
                "chain": "aptos",
                "address": "0x...",
                "balances": [...],
                "total_usd_value": 1234.56,
                "native_balance": {...}
            }
        """
        pass
    
    @abstractmethod
    def get_transactions(
        self, 
        address: str, 
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get transaction history for an address.
        
        Args:
            address: Wallet address
            limit: Max number of transactions to return
            offset: Pagination offset
            
        Returns:
            List of transaction dictionaries
        """
        pass
    
    # ============================================================
    # Optional Methods (can be overridden for chain-specific features)
    # ============================================================
    
    def verify_on_chain(self, address: str) -> Tuple[bool, Optional[str]]:
        """
        Verify address exists on blockchain (optional).
        
        Default implementation: assume valid if format is correct.
        Override for chains where on-chain verification is important.
        
        Args:
            address: Wallet address
            
        Returns:
            Tuple of (exists, error_message)
        """
        return True, None
    
    def get_native_token_symbol(self) -> str:
        """
        Get the native token symbol for this chain.
        
        Returns:
            Native token symbol (e.g., "APT", "SOL", "ETH")
        """
        return self.get_chain_name().upper()
    
    def get_native_token_decimals(self) -> int:
        """
        Get the decimals for the native token.
        
        Returns:
            Number of decimals (e.g., 8 for APT, 9 for SOL, 18 for ETH)
        """
        return 18  # Default, override per chain
    
    def supports_nfts(self) -> bool:
        """Whether this chain adapter supports NFT fetching."""
        return False
    
    def get_nfts(self, address: str) -> List[Dict[str, Any]]:
        """
        Get NFTs owned by address (if supported).
        
        Returns empty list if not implemented.
        """
        return []
    
    # ============================================================
    # Helper Methods
    # ============================================================
    
    def normalize_amount(self, raw: str, decimals: int) -> Decimal:
        """
        Convert raw amount to decimal with proper precision.
        
        Args:
            raw: Raw amount as string
            decimals: Token decimals
            
        Returns:
            Normalized Decimal amount
        """
        from decimal import getcontext
        getcontext().prec = 50
        return Decimal(raw) / (Decimal(10) ** decimals)
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} chain={self.chain_name} rpc={self.rpc_url}>"