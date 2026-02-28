# backend/app/services/adapters/base_chain_adapter.py
"""
Backward compatibility module.

This file re-exports BaseChainAdapter from base.py for backward compatibility.
New code should import directly from base.py.

DEPRECATED: Import from base.py instead:
    from app.services.adapters.base import ChainAdapter, BaseChainAdapter
"""
from .base import ChainAdapter, BaseChainAdapter

__all__ = ["ChainAdapter", "BaseChainAdapter"]
