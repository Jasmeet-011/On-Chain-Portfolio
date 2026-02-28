# app/services/cache.py
"""
Cache Service - Redis with In-Memory Fallback

Provides a unified caching interface that:
- Uses Redis for distributed caching across multiple workers
- Falls back to in-memory cache if Redis is unavailable
- Supports both sync and async operations
- Automatic serialization/deserialization of Python objects

Environment Variables:
- REDIS_URL: Redis connection URL (default: redis://localhost:6379/0)
- REDIS_ENABLED: Enable/disable Redis (default: true)
- REDIS_PREFIX: Key prefix for namespacing (default: chainiq:)
"""
import time
import json
import logging
from typing import Any, Optional, Tuple, Dict
from abc import ABC, abstractmethod

logger = logging.getLogger("chainlens.services.cache")


# ============================================================
# Abstract Cache Interface
# ============================================================

class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl_seconds: int) -> bool:
        """Set value in cache with TTL."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass

    @abstractmethod
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        pass


# ============================================================
# In-Memory Cache (Fallback)
# ============================================================

class InMemoryCache(CacheBackend):
    """
    Simple in-memory TTL cache.

    Used as fallback when Redis is unavailable.
    Note: Not shared across workers in multi-process deployments.
    """

    def __init__(self):
        self._data: Dict[str, Tuple[float, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        now = time.time()
        hit = self._data.get(key)
        if not hit:
            return None
        exp, val = hit
        if now > exp:
            self._data.pop(key, None)
            return None
        return val

    def set(self, key: str, value: Any, ttl_seconds: int) -> bool:
        self._data[key] = (time.time() + ttl_seconds, value)
        return True

    def delete(self, key: str) -> bool:
        return self._data.pop(key, None) is not None

    def exists(self, key: str) -> bool:
        return self.get(key) is not None

    def clear_pattern(self, pattern: str) -> int:
        """Clear keys matching pattern (simple prefix matching)."""
        # Convert Redis-style pattern to simple prefix
        prefix = pattern.rstrip("*")
        keys_to_delete = [k for k in self._data.keys() if k.startswith(prefix)]
        for key in keys_to_delete:
            self._data.pop(key, None)
        return len(keys_to_delete)

    def clear_all(self) -> int:
        """Clear all cached data."""
        count = len(self._data)
        self._data.clear()
        return count


# ============================================================
# Redis Cache
# ============================================================

class RedisCache(CacheBackend):
    """
    Redis-backed cache for distributed caching.

    Features:
    - Shared across all workers
    - Persistent (survives restarts)
    - Supports async operations
    - Automatic JSON serialization
    """

    def __init__(self, redis_url: str, prefix: str = "chainlens:"):
        self.prefix = prefix
        self._client = None
        self._async_client = None
        self._connected = False

        try:
            import redis
            self._client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_timeout=5.0,
                socket_connect_timeout=5.0
            )
            # Test connection
            self._client.ping()
            self._connected = True
            logger.info(f"Redis cache connected: {redis_url}")
        except ImportError:
            logger.warning("Redis package not installed. Install with: pip install redis")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using in-memory fallback.")

    @property
    def is_connected(self) -> bool:
        return self._connected

    def _make_key(self, key: str) -> str:
        """Add prefix to key for namespacing."""
        return f"{self.prefix}{key}"

    def get(self, key: str) -> Optional[Any]:
        if not self._connected:
            return None

        try:
            prefixed_key = self._make_key(key)
            value = self._client.get(prefixed_key)
            if value is None:
                return None
            return json.loads(value)
        except Exception as e:
            logger.warning(f"Redis GET error for {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl_seconds: int) -> bool:
        if not self._connected:
            return False

        try:
            prefixed_key = self._make_key(key)
            serialized = json.dumps(value)
            self._client.setex(prefixed_key, ttl_seconds, serialized)
            return True
        except Exception as e:
            logger.warning(f"Redis SET error for {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        if not self._connected:
            return False

        try:
            prefixed_key = self._make_key(key)
            return self._client.delete(prefixed_key) > 0
        except Exception as e:
            logger.warning(f"Redis DELETE error for {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        if not self._connected:
            return False

        try:
            prefixed_key = self._make_key(key)
            return self._client.exists(prefixed_key) > 0
        except Exception as e:
            logger.warning(f"Redis EXISTS error for {key}: {e}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        if not self._connected:
            return 0

        try:
            prefixed_pattern = self._make_key(pattern)
            keys = self._client.keys(prefixed_pattern)
            if keys:
                return self._client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Redis CLEAR_PATTERN error for {pattern}: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """Get Redis server statistics."""
        if not self._connected:
            return {"connected": False}

        try:
            info = self._client.info()
            return {
                "connected": True,
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_keys": self._client.dbsize(),
                "uptime_seconds": info.get("uptime_in_seconds"),
            }
        except Exception as e:
            return {"connected": False, "error": str(e)}


# ============================================================
# Unified Cache Service
# ============================================================

class CacheService:
    """
    Unified cache service with automatic fallback.

    Uses Redis as primary cache, falls back to in-memory if unavailable.
    Provides a consistent interface regardless of backend.
    """

    def __init__(self):
        self._memory_cache = InMemoryCache()
        self._redis_cache: Optional[RedisCache] = None
        self._use_redis = False
        self._initialized = False

    def initialize(self, redis_url: str = None, redis_enabled: bool = True, prefix: str = "chainlens:"):
        """
        Initialize cache with configuration.

        Args:
            redis_url: Redis connection URL
            redis_enabled: Whether to attempt Redis connection
            prefix: Key prefix for Redis
        """
        if self._initialized:
            return

        if redis_enabled and redis_url:
            self._redis_cache = RedisCache(redis_url, prefix)
            self._use_redis = self._redis_cache.is_connected

        if self._use_redis:
            logger.info("Cache initialized with Redis backend")
        else:
            logger.info("Cache initialized with in-memory backend")

        self._initialized = True

    @property
    def backend_name(self) -> str:
        return "redis" if self._use_redis else "memory"

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Tries Redis first, falls back to memory cache.
        """
        # Try Redis first
        if self._use_redis:
            value = self._redis_cache.get(key)
            if value is not None:
                return value

        # Fallback to memory
        return self._memory_cache.get(key)

    def set(self, key: str, value: Any, ttl_seconds: int) -> bool:
        """
        Set value in cache.

        Sets in both Redis and memory for redundancy.
        """
        success = True

        # Set in Redis
        if self._use_redis:
            success = self._redis_cache.set(key, value, ttl_seconds)

        # Also set in memory for faster local access
        self._memory_cache.set(key, value, ttl_seconds)

        return success

    def delete(self, key: str) -> bool:
        """Delete from both caches."""
        success = True

        if self._use_redis:
            success = self._redis_cache.delete(key)

        self._memory_cache.delete(key)
        return success

    def exists(self, key: str) -> bool:
        """Check if key exists in any cache."""
        if self._use_redis and self._redis_cache.exists(key):
            return True
        return self._memory_cache.exists(key)

    def clear_pattern(self, pattern: str) -> int:
        """Clear keys matching pattern from all caches."""
        count = 0

        if self._use_redis:
            count += self._redis_cache.clear_pattern(pattern)

        count += self._memory_cache.clear_pattern(pattern)
        return count

    def clear_prices(self) -> int:
        """Clear all cached prices."""
        return self.clear_pattern("prices:*")

    def clear_balances(self) -> int:
        """Clear all cached balances."""
        return self.clear_pattern("balances:*")

    def clear_all(self) -> int:
        """Clear all cached data."""
        count = 0

        if self._use_redis:
            count += self._redis_cache.clear_pattern("*")

        count += self._memory_cache.clear_all()
        return count

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {
            "backend": self.backend_name,
            "memory_keys": len(self._memory_cache._data),
        }

        if self._use_redis:
            stats["redis"] = self._redis_cache.get_stats()

        return stats


# ============================================================
# Singleton Instance
# ============================================================

# Create singleton instance
cache = CacheService()


def initialize_cache():
    """Initialize cache from settings. Call this on app startup."""
    try:
        from app.config import settings
        cache.initialize(
            redis_url=settings.redis_url,
            redis_enabled=settings.redis_enabled,
            prefix=settings.redis_prefix
        )
    except Exception as e:
        logger.warning(f"Cache initialization error: {e}. Using defaults.")
        cache.initialize(redis_enabled=False)


# ============================================================
# Legacy TTLCache for backward compatibility
# ============================================================

class TTLCache:
    """Backward-compatible wrapper around CacheService."""

    def get(self, key: str):
        return cache.get(key)

    def set(self, key: str, value: Any, ttl_seconds: int):
        cache.set(key, value, ttl_seconds)
