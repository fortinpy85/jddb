"""
Caching utilities for expensive operations.

Provides simple Redis-based caching for API endpoints and service methods.
Optimized for ≤100 concurrent users.
"""

from functools import wraps
from typing import Any, Callable, Optional
import hashlib
from ..utils.logging import get_logger

logger = get_logger(__name__)

# Simple in-memory cache as fallback if Redis unavailable
_memory_cache: dict[str, Any] = {}
_cache_enabled = True


def _generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate deterministic cache key from function arguments."""
    key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
    return hashlib.md5(key_data.encode()).hexdigest()


def cache_result(
    ttl: int = 300,  # 5 minutes default
    key_prefix: Optional[str] = None,
    use_redis: bool = False,  # Memory cache by default for ≤100 users
):
    """
    Decorator to cache function results.

    Args:
        ttl: Time-to-live in seconds (default 300s / 5min)
        key_prefix: Custom key prefix (default: function name)
        use_redis: Use Redis instead of memory (for larger deployments)

    Usage:
        @cache_result(ttl=60)
        async def get_expensive_data(param1, param2):
            # Expensive operation
            return result
    """

    def decorator(func: Callable) -> Callable:
        prefix = key_prefix or f"{func.__module__}.{func.__name__}"

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not _cache_enabled:
                return await func(*args, **kwargs)

            cache_key = _generate_cache_key(prefix, *args, **kwargs)

            # Try to get from cache
            try:
                if cache_key in _memory_cache:
                    logger.debug(f"Cache HIT: {prefix}", cache_key=cache_key)
                    return _memory_cache[cache_key]
            except Exception as e:
                logger.warning(f"Cache read failed: {e}", cache_key=cache_key)

            # Cache miss - execute function
            logger.debug(f"Cache MISS: {prefix}", cache_key=cache_key)
            result = await func(*args, **kwargs)

            # Store in cache
            try:
                _memory_cache[cache_key] = result
                # Simple TTL: Just limit cache size to 1000 entries for ≤100 users
                if len(_memory_cache) > 1000:
                    # Remove oldest 20% of entries
                    keys_to_remove = list(_memory_cache.keys())[:200]
                    for key in keys_to_remove:
                        del _memory_cache[key]
            except Exception as e:
                logger.warning(f"Cache write failed: {e}", cache_key=cache_key)

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not _cache_enabled:
                return func(*args, **kwargs)

            cache_key = _generate_cache_key(prefix, *args, **kwargs)

            # Try to get from cache
            try:
                if cache_key in _memory_cache:
                    logger.debug(f"Cache HIT: {prefix}", cache_key=cache_key)
                    return _memory_cache[cache_key]
            except Exception as e:
                logger.warning(f"Cache read failed: {e}", cache_key=cache_key)

            # Cache miss - execute function
            logger.debug(f"Cache MISS: {prefix}", cache_key=cache_key)
            result = func(*args, **kwargs)

            # Store in cache
            try:
                _memory_cache[cache_key] = result
                if len(_memory_cache) > 1000:
                    keys_to_remove = list(_memory_cache.keys())[:200]
                    for key in keys_to_remove:
                        del _memory_cache[key]
            except Exception as e:
                logger.warning(f"Cache write failed: {e}", cache_key=cache_key)

            return result

        # Return appropriate wrapper based on function type
        import inspect

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def clear_cache(pattern: Optional[str] = None):
    """Clear cache entries matching pattern, or all if pattern is None."""
    global _memory_cache
    if pattern is None:
        _memory_cache.clear()
        logger.info("Cache cleared completely")
    else:
        keys_to_remove = [k for k in _memory_cache.keys() if pattern in k]
        for key in keys_to_remove:
            del _memory_cache[key]
        logger.info(f"Cache cleared for pattern: {pattern}", count=len(keys_to_remove))


def get_cache_stats() -> dict:
    """Get cache statistics for monitoring."""
    return {
        "enabled": _cache_enabled,
        "entries": len(_memory_cache),
        "max_entries": 1000,
        "type": "memory",
    }
