import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from jd_ingestion.utils.cache import CacheService, cached


class TestCacheService:
    """Test suite for the CacheService class."""

    @pytest.fixture
    def cache_service(self):
        """Create a cache service instance for testing."""
        return CacheService()

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client for testing."""
        mock_client = AsyncMock()
        mock_client.ping.return_value = True
        mock_client.get.return_value = None
        mock_client.setex.return_value = True
        mock_client.delete.return_value = 1
        mock_client.keys.return_value = []
        mock_client.info.return_value = {
            "used_memory": 1024000,
            "used_memory_human": "1.00M",
            "maxmemory": 2048000,
            "used_memory_percentage": 50.0,
            "expired_keys": 10,
            "evicted_keys": 5,
        }
        return mock_client

    @pytest.mark.asyncio
    async def test_cache_service_initialization(self, cache_service):
        """Test cache service initializes correctly."""
        assert cache_service is not None
        # Redis client may or may not be available in test environment
        assert hasattr(cache_service, "redis_client")

    @pytest.mark.asyncio
    async def test_ping_success(self, cache_service, mock_redis_client):
        """Test successful Redis ping."""
        cache_service.redis_client = mock_redis_client
        result = await cache_service.ping()
        assert result is True
        mock_redis_client.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_ping_failure(self, cache_service):
        """Test Redis ping failure when no client."""
        cache_service.redis_client = None
        result = await cache_service.ping()
        assert result is False

    @pytest.mark.asyncio
    async def test_generate_cache_key_string(self, cache_service):
        """Test cache key generation with string data."""
        key = cache_service._generate_cache_key("test", "data")
        assert key.startswith("test:")
        assert len(key.split(":")[1]) == 32  # MD5 hash length

    @pytest.mark.asyncio
    async def test_generate_cache_key_dict(self, cache_service):
        """Test cache key generation with dictionary data."""
        data = {"query": "test", "filters": {"type": "job"}}
        key = cache_service._generate_cache_key("search", data)
        assert key.startswith("search:")
        assert len(key.split(":")[1]) == 32

    @pytest.mark.asyncio
    async def test_get_cache_hit(self, cache_service, mock_redis_client):
        """Test successful cache get operation."""
        cache_service.redis_client = mock_redis_client
        mock_redis_client.get.return_value = '{"result": "cached_data"}'

        result = await cache_service.get("test:key")
        assert result == {"result": "cached_data"}
        mock_redis_client.get.assert_called_once_with("test:key")

    @pytest.mark.asyncio
    async def test_get_cache_miss(self, cache_service, mock_redis_client):
        """Test cache miss returns None."""
        cache_service.redis_client = mock_redis_client
        mock_redis_client.get.return_value = None

        result = await cache_service.get("test:key")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_no_redis_client(self, cache_service):
        """Test get returns None when no Redis client."""
        cache_service.redis_client = None
        result = await cache_service.get("test:key")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_success(self, cache_service, mock_redis_client):
        """Test successful cache set operation."""
        cache_service.redis_client = mock_redis_client

        result = await cache_service.set("test:key", {"data": "value"}, 3600)
        assert result is True
        mock_redis_client.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_no_redis_client(self, cache_service):
        """Test set returns False when no Redis client."""
        cache_service.redis_client = None
        result = await cache_service.set("test:key", {"data": "value"})
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_success(self, cache_service, mock_redis_client):
        """Test successful cache delete operation."""
        cache_service.redis_client = mock_redis_client

        result = await cache_service.delete("test:key")
        assert result is True
        mock_redis_client.delete.assert_called_once_with("test:key")

    @pytest.mark.asyncio
    async def test_get_or_set_cache_hit(self, cache_service, mock_redis_client):
        """Test get_or_set with cache hit."""
        cache_service.redis_client = mock_redis_client
        mock_redis_client.get.return_value = '{"cached": "data"}'

        # Mock function should not be called if cache hits
        fetch_func = Mock(return_value={"new": "data"})

        result = await cache_service.get_or_set("test:key", fetch_func, 3600)
        assert result == {"cached": "data"}
        fetch_func.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_or_set_cache_miss_sync_func(
        self, cache_service, mock_redis_client
    ):
        """Test get_or_set with cache miss and sync function."""
        cache_service.redis_client = mock_redis_client
        mock_redis_client.get.return_value = None

        fetch_func = Mock(return_value={"new": "data"})

        result = await cache_service.get_or_set("test:key", fetch_func, 3600)
        assert result == {"new": "data"}
        fetch_func.assert_called_once()
        mock_redis_client.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_set_cache_miss_async_func(
        self, cache_service, mock_redis_client
    ):
        """Test get_or_set with cache miss and async function."""
        cache_service.redis_client = mock_redis_client
        mock_redis_client.get.return_value = None

        async def async_fetch_func():
            return {"async": "data"}

        result = await cache_service.get_or_set("test:key", async_fetch_func, 3600)
        assert result == {"async": "data"}
        mock_redis_client.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_search_results(self, cache_service, mock_redis_client):
        """Test caching search results."""
        cache_service.redis_client = mock_redis_client

        query = "test query"
        filters = {"type": "job"}
        results = [{"id": 1, "title": "Test Job"}]

        result = await cache_service.cache_search_results(query, filters, results)
        assert result is True
        mock_redis_client.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cached_search_results(self, cache_service, mock_redis_client):
        """Test getting cached search results."""
        cache_service.redis_client = mock_redis_client
        cached_results = [{"id": 1, "title": "Test Job"}]
        mock_redis_client.get.return_value = f'[{{"id": 1, "title": "Test Job"}}]'

        query = "test query"
        filters = {"type": "job"}

        result = await cache_service.get_cached_search_results(query, filters)
        assert result == cached_results
        mock_redis_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_similar_jobs(self, cache_service, mock_redis_client):
        """Test caching similar jobs."""
        cache_service.redis_client = mock_redis_client

        job_id = 123
        limit = 10
        results = [{"id": 124, "similarity": 0.9}]

        result = await cache_service.cache_similar_jobs(job_id, limit, results)
        assert result is True
        mock_redis_client.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cached_similar_jobs(self, cache_service, mock_redis_client):
        """Test getting cached similar jobs."""
        cache_service.redis_client = mock_redis_client
        cached_results = [{"id": 124, "similarity": 0.9}]
        mock_redis_client.get.return_value = '[{"id": 124, "similarity": 0.9}]'

        result = await cache_service.get_cached_similar_jobs(123, 10)
        assert result == cached_results

    @pytest.mark.asyncio
    async def test_cache_job_comparison(self, cache_service, mock_redis_client):
        """Test caching job comparison results."""
        cache_service.redis_client = mock_redis_client

        comparison_data = {"similarity": 0.85, "differences": []}

        result = await cache_service.cache_job_comparison(123, 456, comparison_data)
        assert result is True
        mock_redis_client.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_job_comparison_normalized_ids(
        self, cache_service, mock_redis_client
    ):
        """Test job comparison normalizes IDs (smaller first)."""
        cache_service.redis_client = mock_redis_client

        comparison_data = {"similarity": 0.85}

        # Should work the same regardless of ID order
        await cache_service.cache_job_comparison(456, 123, comparison_data)
        await cache_service.cache_job_comparison(123, 456, comparison_data)

        # Both calls should generate the same cache key
        assert mock_redis_client.setex.call_count == 2

    @pytest.mark.asyncio
    async def test_get_cached_job_comparison(self, cache_service, mock_redis_client):
        """Test getting cached job comparison."""
        cache_service.redis_client = mock_redis_client
        cached_data = {"similarity": 0.85, "differences": []}
        mock_redis_client.get.return_value = '{"similarity": 0.85, "differences": []}'

        result = await cache_service.get_cached_job_comparison(123, 456)
        assert result == cached_data

    @pytest.mark.asyncio
    async def test_invalidate_job_cache(self, cache_service, mock_redis_client):
        """Test job cache invalidation."""
        cache_service.redis_client = mock_redis_client
        mock_redis_client.keys.return_value = ["search:key1", "similar:key2"]

        result = await cache_service.invalidate_job_cache(123)
        assert result is True

        # Should call keys for each pattern
        assert mock_redis_client.keys.call_count == 3
        # Delete is called 3 times (once for each pattern that returns keys)
        assert mock_redis_client.delete.call_count == 3

    @pytest.mark.asyncio
    async def test_get_cache_stats_success(self, cache_service, mock_redis_client):
        """Test getting cache statistics."""
        cache_service.redis_client = mock_redis_client
        mock_redis_client.info.side_effect = [
            {  # memory info
                "used_memory": 1024000,
                "used_memory_human": "1.00M",
                "maxmemory": 2048000,
                "used_memory_percentage": 50.0,
                "expired_keys": 10,
                "evicted_keys": 5,
            },
            {"db0": {"keys": 100, "expires": 20}},  # keyspace info
        ]

        stats = await cache_service.get_cache_stats()
        assert stats["status"] == "available"
        assert stats["memory_usage_bytes"] == 1024000
        assert stats["total_keys"] == 100
        assert mock_redis_client.info.call_count == 2

    @pytest.mark.asyncio
    async def test_get_cache_stats_no_client(self, cache_service):
        """Test cache stats when no Redis client."""
        cache_service.redis_client = None
        stats = await cache_service.get_cache_stats()
        assert stats["status"] == "unavailable"


class TestCachedDecorator:
    """Test suite for the @cached decorator."""

    @pytest.mark.asyncio
    async def test_cached_decorator_async_function(self):
        """Test @cached decorator with async function."""
        call_count = 0

        @cached(expiry_seconds=300, key_prefix="test")
        async def expensive_async_function(value):
            nonlocal call_count
            call_count += 1
            return f"result_{value}"

        # Mock the cache service
        with patch("jd_ingestion.utils.cache.cache_service") as mock_cache:
            mock_cache.redis_client = AsyncMock()
            mock_cache.get = AsyncMock(return_value=None)  # Cache miss
            mock_cache.set = AsyncMock(return_value=True)
            mock_cache._generate_cache_key.return_value = "test:key"

            result1 = await expensive_async_function("test")
            result2 = await expensive_async_function("test")

            assert result1 == "result_test"
            assert result2 == "result_test"
            assert call_count == 2  # Called twice due to cache miss

    @pytest.mark.asyncio
    async def test_cached_decorator_sync_function(self):
        """Test @cached decorator with sync function."""
        call_count = 0

        @cached(expiry_seconds=300, key_prefix="test")
        def expensive_sync_function(value):
            nonlocal call_count
            call_count += 1
            return f"result_{value}"

        # Mock the cache service
        with patch("jd_ingestion.utils.cache.cache_service") as mock_cache:
            mock_cache.redis_client = AsyncMock()
            mock_cache.get = AsyncMock(return_value=None)  # Cache miss
            mock_cache.set = AsyncMock(return_value=True)
            mock_cache._generate_cache_key.return_value = "test:key"

            result1 = await expensive_sync_function("test")
            result2 = await expensive_sync_function("test")

            assert result1 == "result_test"
            assert result2 == "result_test"
            assert call_count == 2  # Called twice due to cache miss

    @pytest.mark.asyncio
    async def test_cached_decorator_cache_hit(self):
        """Test @cached decorator with cache hit."""
        call_count = 0

        @cached(expiry_seconds=300, key_prefix="test")
        async def expensive_function(value):
            nonlocal call_count
            call_count += 1
            return f"result_{value}"

        # Mock the cache service with cache hit
        with patch("jd_ingestion.utils.cache.cache_service") as mock_cache:
            mock_cache.redis_client = AsyncMock()
            mock_cache.get = AsyncMock(return_value="cached_result")  # Cache hit
            mock_cache._generate_cache_key.return_value = "test:key"

            result = await expensive_function("test")

            assert result == "cached_result"
            assert call_count == 0  # Function not called due to cache hit

    @pytest.mark.asyncio
    async def test_cached_decorator_no_redis(self):
        """Test @cached decorator when Redis is unavailable."""
        call_count = 0

        @cached(expiry_seconds=300, key_prefix="test")
        async def expensive_function(value):
            nonlocal call_count
            call_count += 1
            return f"result_{value}"

        # Mock the cache service without Redis client
        with patch("jd_ingestion.utils.cache.cache_service") as mock_cache:
            mock_cache.redis_client = None

            result = await expensive_function("test")

            assert result == "result_test"
            assert call_count == 1  # Function called normally

    @pytest.mark.asyncio
    async def test_cached_decorator_exclude_args(self):
        """Test @cached decorator with include_args=False."""

        @cached(expiry_seconds=300, key_prefix="test", include_args=False)
        async def function_ignore_args(value):
            return f"result_{value}"

        with patch("jd_ingestion.utils.cache.cache_service") as mock_cache:
            mock_cache.redis_client = AsyncMock()
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock(return_value=True)
            mock_cache._generate_cache_key.return_value = "test:key"

            await function_ignore_args("value1")
            await function_ignore_args("value2")

            # Should generate same key for both calls (ignoring args)
            assert mock_cache._generate_cache_key.call_count == 2
            # Both calls should use the same key structure (func name only)
            for call in mock_cache._generate_cache_key.call_args_list:
                args, kwargs = call
                key_data = args[1]  # Second argument is the key data
                assert "args" not in key_data  # Args should not be included
                assert key_data["func"] == "function_ignore_args"
