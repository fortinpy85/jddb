"""
Redis-based caching utilities for performance optimization.
"""

import json
import asyncio
import hashlib
from typing import Any, Optional, Dict, List, Union
import redis.asyncio as redis
from functools import wraps

from ..config import settings
from .logging import get_logger, PerformanceTimer

logger = get_logger(__name__)


class CacheService:
    """Redis-based caching service for performance optimization."""

    def __init__(self):
        """Initialize the cache service."""
        self.redis_client = None
        self._init_redis()

    def _init_redis(self):
        """Initialize Redis client for caching."""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                max_connections=settings.redis_max_connections,
                retry_on_timeout=settings.redis_retry_on_timeout,
                socket_keepalive=settings.redis_socket_keepalive,
            )
            logger.info("Cache service initialized with Redis")
        except Exception as e:
            logger.error("Failed to initialize Redis cache", error=str(e))
            self.redis_client = None

    async def ping(self) -> bool:
        """Test Redis connection."""
        if not self.redis_client:
            return False
        try:
            await self.redis_client.ping()
            return True
        except Exception as e:
            logger.error("Redis ping failed", error=str(e))
            return False

    def _generate_cache_key(self, prefix: str, data: Union[str, Dict, List]) -> str:
        """Generate a consistent cache key from data."""
        if isinstance(data, str):
            key_data = data
        else:
            key_data = json.dumps(data, sort_keys=True)

        hash_key = hashlib.md5(key_data.encode()).hexdigest()
        return f"{prefix}:{hash_key}"

    async def get(self, key: str) -> Optional[Any]:
        """Get cached value by key."""
        if not self.redis_client:
            return None

        try:
            with PerformanceTimer("cache_get", tags={"key_prefix": key.split(":")[0]}):
                cached_data = await self.redis_client.get(key)
                if cached_data:
                    return json.loads(cached_data)
                return None
        except Exception as e:
            logger.error("Cache get failed", key=key, error=str(e))
            return None

    async def set(self, key: str, value: Any, expiry_seconds: int = 3600) -> bool:
        """Set cache value with expiry."""
        if not self.redis_client:
            return False

        try:
            with PerformanceTimer("cache_set", tags={"key_prefix": key.split(":")[0]}):
                serialized_value = json.dumps(value, default=str)
                await self.redis_client.setex(key, expiry_seconds, serialized_value)
                return True
        except Exception as e:
            logger.error("Cache set failed", key=key, error=str(e))
            return False

    async def delete(self, key: str) -> bool:
        """Delete cache entry."""
        if not self.redis_client:
            return False

        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error("Cache delete failed", key=key, error=str(e))
            return False

    async def get_or_set(
        self, key: str, fetch_func, expiry_seconds: int = 3600, *args, **kwargs
    ) -> Optional[Any]:
        """Get from cache or set if not exists."""
        # Try to get from cache first
        cached_value = await self.get(key)
        if cached_value is not None:
            logger.debug("Cache hit", key=key)
            return cached_value

        # If not in cache, fetch and set
        try:
            logger.debug("Cache miss, fetching data", key=key)
            if asyncio.iscoroutinefunction(fetch_func):
                value = await fetch_func(*args, **kwargs)
            else:
                value = fetch_func(*args, **kwargs)

            if value is not None:
                await self.set(key, value, expiry_seconds)

            return value
        except Exception as e:
            logger.error("Cache get_or_set fetch failed", key=key, error=str(e))
            return None

    async def cache_search_results(
        self,
        query: str,
        filters: Dict[str, Any],
        results: List[Dict],
        expiry_seconds: int = 1800,  # 30 minutes
    ) -> bool:
        """Cache search results."""
        cache_key = self._generate_cache_key(
            "search", {"query": query, "filters": filters}
        )
        return await self.set(cache_key, results, expiry_seconds)

    async def get_cached_search_results(
        self, query: str, filters: Dict[str, Any]
    ) -> Optional[List[Dict]]:
        """Get cached search results."""
        cache_key = self._generate_cache_key(
            "search", {"query": query, "filters": filters}
        )
        return await self.get(cache_key)

    async def cache_similar_jobs(
        self,
        job_id: int,
        limit: int,
        results: List[Dict],
        expiry_seconds: int = 3600,  # 1 hour
    ) -> bool:
        """Cache similar jobs results."""
        cache_key = self._generate_cache_key(
            "similar", {"job_id": job_id, "limit": limit}
        )
        return await self.set(cache_key, results, expiry_seconds)

    async def get_cached_similar_jobs(
        self, job_id: int, limit: int
    ) -> Optional[List[Dict]]:
        """Get cached similar jobs."""
        cache_key = self._generate_cache_key(
            "similar", {"job_id": job_id, "limit": limit}
        )
        return await self.get(cache_key)

    async def cache_job_comparison(
        self,
        job_id1: int,
        job_id2: int,
        comparison_data: Dict,
        expiry_seconds: int = 7200,  # 2 hours
    ) -> bool:
        """Cache job comparison results."""
        # Normalize job IDs (smaller first for consistent key)
        ids = sorted([job_id1, job_id2])
        cache_key = self._generate_cache_key(
            "comparison", {"job_id1": ids[0], "job_id2": ids[1]}
        )
        return await self.set(cache_key, comparison_data, expiry_seconds)

    async def get_cached_job_comparison(
        self, job_id1: int, job_id2: int
    ) -> Optional[Dict]:
        """Get cached job comparison."""
        ids = sorted([job_id1, job_id2])
        cache_key = self._generate_cache_key(
            "comparison", {"job_id1": ids[0], "job_id2": ids[1]}
        )
        return await self.get(cache_key)

    async def invalidate_job_cache(self, job_id: int) -> bool:
        """Invalidate all cache entries related to a specific job."""
        if not self.redis_client:
            return False

        try:
            # Find keys that contain this job_id
            patterns = [
                f"search:*job_id*{job_id}*",
                f"similar:*job_id*{job_id}*",
                f"comparison:*job_id*{job_id}*",
            ]

            for pattern in patterns:
                keys = await self.redis_client.keys(pattern)
                if keys:
                    await self.redis_client.delete(*keys)

            logger.info("Job cache invalidated", job_id=job_id)
            return True
        except Exception as e:
            logger.error("Cache invalidation failed", job_id=job_id, error=str(e))
            return False

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache usage statistics."""
        if not self.redis_client:
            return {"status": "unavailable"}

        try:
            info = await self.redis_client.info("memory")
            keyspace = await self.redis_client.info("keyspace")

            stats = {
                "status": "available",
                "memory_usage_bytes": info.get("used_memory", 0),
                "memory_usage_human": info.get("used_memory_human", "0B"),
                "max_memory_bytes": info.get("maxmemory", 0),
                "memory_usage_percent": info.get("used_memory_percentage", 0),
                "total_keys": (
                    sum([db_info["keys"] for db_info in keyspace.values()])
                    if keyspace
                    else 0
                ),
                "expired_keys": info.get("expired_keys", 0),
                "evicted_keys": info.get("evicted_keys", 0),
            }

            return stats
        except Exception as e:
            logger.error("Failed to get cache stats", error=str(e))
            return {"status": "error", "error": str(e)}


# Global cache service instance
cache_service = CacheService()


def cached(
    expiry_seconds: int = 3600, key_prefix: str = "func", include_args: bool = True
):
    """Decorator for caching function results."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not cache_service.redis_client:
                # If cache is not available, just call the function
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)

            # Generate cache key
            if include_args:
                key_data = {"func": func.__name__, "args": args, "kwargs": kwargs}
            else:
                key_data = {"func": func.__name__}

            cache_key = cache_service._generate_cache_key(key_prefix, key_data)

            # Try to get cached result
            cached_result = await cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result

            # If not cached, call function and cache result
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            if result is not None:
                await cache_service.set(cache_key, result, expiry_seconds)

            return result

        return wrapper

    return decorator
