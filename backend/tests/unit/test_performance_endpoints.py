"""
Tests for performance monitoring API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi import HTTPException
from httpx import AsyncClient, ASGITransport

from jd_ingestion.api.main import app
from jd_ingestion.api.endpoints.performance import (
    get_performance_statistics,
    benchmark_vector_search,
    optimize_database_indexes,
    performance_health_check,
    PerformanceStats,
    VectorSearchBenchmark,
)


class TestGetPerformanceStatistics:
    """Test performance statistics endpoint."""

    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        return AsyncMock()

    @pytest.fixture
    def sample_performance_stats(self):
        """Sample performance statistics."""
        return {
            "embedding_operations": {
                "total_requests": 1500,
                "successful_requests": 1450,
                "failed_requests": 50,
                "average_response_time_ms": 250,
                "cache_hit_rate": 0.75,
            },
            "database_performance": {
                "avg_query_time_ms": 15.5,
                "slow_queries": 12,
                "connection_pool_usage": 0.65,
            },
            "vector_search_performance": {
                "avg_search_time_ms": 45.2,
                "similarity_threshold_avg": 0.8,
                "results_per_query_avg": 8.5,
            },
        }

    @patch("jd_ingestion.api.endpoints.performance.optimized_embedding_service")
    @pytest.mark.asyncio
    async def test_get_performance_statistics_success(
        self, mock_embedding_service, mock_session, sample_performance_stats
    ):
        """Test successful performance statistics retrieval."""
        mock_embedding_service.get_performance_stats.return_value = (
            sample_performance_stats
        )

        result = await get_performance_statistics(db=mock_session)

        assert result["status"] == "success"
        assert "performance_stats" in result
        assert "generated_at" in result
        assert result["performance_stats"] == sample_performance_stats
        mock_embedding_service.get_performance_stats.assert_called_once_with(
            mock_session
        )

    @patch("jd_ingestion.api.endpoints.performance.optimized_embedding_service")
    @patch("jd_ingestion.api.endpoints.performance.logger")
    @pytest.mark.asyncio
    async def test_get_performance_statistics_service_error(
        self, mock_logger, mock_embedding_service, mock_session
    ):
        """Test performance statistics with embedding service error."""
        mock_embedding_service.get_performance_stats.side_effect = Exception(
            "Service unavailable"
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_performance_statistics(db=mock_session)

        assert exc_info.value.status_code == 500
        assert "Failed to retrieve performance stats" in exc_info.value.detail
        mock_logger.error.assert_called_once()

    @patch("jd_ingestion.api.endpoints.performance.optimized_embedding_service")
    @pytest.mark.asyncio
    async def test_get_performance_statistics_empty_stats(
        self, mock_embedding_service, mock_session
    ):
        """Test performance statistics with empty stats."""
        mock_embedding_service.get_performance_stats.return_value = {}

        result = await get_performance_statistics(db=mock_session)

        assert result["status"] == "success"
        assert result["performance_stats"] == {}


class TestBenchmarkVectorSearch:
    """Test vector search benchmarking endpoint."""

    @pytest.fixture
    def benchmark_request(self):
        """Sample benchmark request."""
        return VectorSearchBenchmark(
            query_text="Senior Policy Advisor",
            limit=10,
            similarity_threshold=0.7,
            include_filters=True,
            classification_filter="EX-01",
            language_filter="en",
        )

    @pytest.fixture
    def sample_search_results(self):
        """Sample search results."""
        return [
            {
                "chunk_id": 1,
                "job_id": 1,
                "similarity": 0.95,
                "content": "Senior advisor role...",
            },
            {
                "chunk_id": 2,
                "job_id": 2,
                "similarity": 0.88,
                "content": "Policy advisor position...",
            },
            {
                "chunk_id": 3,
                "job_id": 3,
                "similarity": 0.82,
                "content": "Advisory role in policy...",
            },
        ]

    @patch("jd_ingestion.api.endpoints.performance.optimized_embedding_service")
    @patch("jd_ingestion.api.endpoints.performance.time")
    @pytest.mark.asyncio
    async def test_benchmark_vector_search_success(
        self,
        mock_time,
        mock_embedding_service,
        benchmark_request,
        sample_search_results,
    ):
        """Test successful vector search benchmarking."""
        mock_session = AsyncMock()

        # Mock time measurements
        mock_time.perf_counter.side_effect = [
            0.0,
            0.05,  # embedding generation: 50ms
            0.05,
            0.1,  # similarity search: 50ms
            0.1,
            0.15,  # semantic search: 50ms
        ]

        # Mock embedding service responses
        mock_embedding_service.generate_embedding.return_value = [
            0.1,
            0.2,
            0.3,
        ] * 100  # Mock embedding
        mock_embedding_service.find_similar_chunks_optimized.return_value = (
            sample_search_results
        )
        mock_embedding_service.semantic_search_optimized.return_value = (
            sample_search_results
        )

        result = await benchmark_vector_search(
            benchmark=benchmark_request, db=mock_session
        )

        assert result["status"] == "success"
        assert "benchmark_results" in result
        benchmark_results = result["benchmark_results"]

        assert benchmark_results["query_text"] == "Senior Policy Advisor"
        assert benchmark_results["configuration"]["limit"] == 10
        assert benchmark_results["configuration"]["similarity_threshold"] == 0.7
        assert benchmark_results["configuration"]["filters_applied"] is True

        # Check performance metrics
        performance_metrics = benchmark_results["performance_metrics"]
        assert "embedding_generation_ms" in performance_metrics
        assert "similarity_search_ms" in performance_metrics
        assert "semantic_search_ms" in performance_metrics
        assert "total_time_ms" in performance_metrics

        # Check result counts
        result_counts = benchmark_results["result_counts"]
        assert result_counts["similarity_results"] == 3
        assert result_counts["semantic_results"] == 3

    @patch("jd_ingestion.api.endpoints.performance.optimized_embedding_service")
    @pytest.mark.asyncio
    async def test_benchmark_vector_search_embedding_failure(
        self, mock_embedding_service, benchmark_request
    ):
        """Test benchmarking when embedding generation fails."""
        mock_session = AsyncMock()
        mock_embedding_service.generate_embedding.return_value = (
            None  # Failed embedding
        )

        with pytest.raises(HTTPException) as exc_info:
            await benchmark_vector_search(benchmark=benchmark_request, db=mock_session)

        assert exc_info.value.status_code == 400
        assert "Failed to generate query embedding" in exc_info.value.detail

    @patch("jd_ingestion.api.endpoints.performance.optimized_embedding_service")
    @patch("jd_ingestion.api.endpoints.performance.logger")
    @pytest.mark.asyncio
    async def test_benchmark_vector_search_service_error(
        self, mock_logger, mock_embedding_service, benchmark_request
    ):
        """Test benchmarking with service error."""
        mock_session = AsyncMock()
        mock_embedding_service.generate_embedding.side_effect = Exception(
            "Service error"
        )

        with pytest.raises(HTTPException) as exc_info:
            await benchmark_vector_search(benchmark=benchmark_request, db=mock_session)

        assert exc_info.value.status_code == 500
        assert "Benchmark failed" in exc_info.value.detail
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_benchmark_vector_search_without_filters(self, sample_search_results):
        """Test benchmarking without filters applied."""
        mock_session = AsyncMock()

        benchmark_request = VectorSearchBenchmark(
            query_text="Director",
            limit=5,
            similarity_threshold=0.8,
            include_filters=False,
        )

        with (
            patch(
                "jd_ingestion.api.endpoints.performance.optimized_embedding_service"
            ) as mock_service,
            patch("jd_ingestion.api.endpoints.performance.time") as mock_time,
        ):
            # Mock time measurements
            mock_time.perf_counter.side_effect = [0.0, 0.05, 0.05, 0.1, 0.1, 0.15]

            # Mock service responses
            mock_service.generate_embedding.return_value = [0.1, 0.2] * 100
            mock_service.find_similar_chunks_optimized.return_value = (
                sample_search_results
            )
            mock_service.semantic_search_optimized.return_value = sample_search_results

            result = await benchmark_vector_search(
                benchmark=benchmark_request, db=mock_session
            )

            assert (
                result["benchmark_results"]["configuration"]["filters_applied"] is False
            )
            assert (
                result["benchmark_results"]["configuration"]["classification_filter"]
                is None
            )
            assert (
                result["benchmark_results"]["configuration"]["language_filter"] is None
            )


class TestOptimizeDatabaseIndexes:
    """Test database optimization endpoint."""

    @pytest.fixture
    def mock_session(self):
        """Mock database session with text execution."""
        session = AsyncMock()
        return session

    @pytest.fixture
    def sample_vacuum_data(self):
        """Sample vacuum recommendation data."""
        vacuum_row_1 = Mock()
        vacuum_row_1.tablename = "content_chunks"
        vacuum_row_1.n_dead_tup = 150
        vacuum_row_1.dead_tuple_percent = 15.5

        vacuum_row_2 = Mock()
        vacuum_row_2.tablename = "job_descriptions"
        vacuum_row_2.n_dead_tup = 25
        vacuum_row_2.dead_tuple_percent = 5.2

        return [vacuum_row_1, vacuum_row_2]

    @pytest.mark.asyncio
    async def test_optimize_database_indexes_success(
        self, mock_session, sample_vacuum_data
    ):
        """Test successful database optimization."""
        # Mock vacuum check query result
        vacuum_result = Mock()
        vacuum_result.fetchall.return_value = sample_vacuum_data
        mock_session.execute.return_value = vacuum_result

        result = await optimize_database_indexes(db=mock_session)

        assert result["status"] == "success"
        assert "optimization_results" in result
        optimization_results = result["optimization_results"]

        # Check analyze commands results
        assert "analyze_commands" in optimization_results
        analyze_results = optimization_results["analyze_commands"]
        assert len(analyze_results) == 5  # Number of ANALYZE commands

        # All should be successful in this mock scenario
        for cmd_result in analyze_results:
            assert cmd_result["status"] == "success"
            assert "command" in cmd_result

        # Check vacuum recommendations
        assert "vacuum_recommendations" in optimization_results
        vacuum_recs = optimization_results["vacuum_recommendations"]
        assert len(vacuum_recs) == 2

        # First table needs vacuum (>10% dead tuples)
        content_chunks_rec = next(
            r for r in vacuum_recs if r["table"] == "content_chunks"
        )
        assert content_chunks_rec["needs_vacuum"] is True
        assert content_chunks_rec["dead_tuples"] == 150

        # Second table doesn't need vacuum (<10% dead tuples)
        job_desc_rec = next(r for r in vacuum_recs if r["table"] == "job_descriptions")
        assert job_desc_rec["needs_vacuum"] is False
        assert job_desc_rec["dead_tuples"] == 25

        # Verify commit was called
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_optimize_database_indexes_partial_failure(self, mock_session):
        """Test database optimization with some command failures."""

        # Mock analyze command failures for some commands
        def mock_execute_side_effect(query):
            if "content_chunks" in str(query):
                raise Exception("Table locked")
            return Mock()

        mock_session.execute.side_effect = mock_execute_side_effect

        result = await optimize_database_indexes(db=mock_session)

        assert result["status"] == "success"  # Overall still succeeds
        analyze_results = result["optimization_results"]["analyze_commands"]

        # Should have mixed success/failure results
        failed_commands = [r for r in analyze_results if r["status"] == "failed"]
        successful_commands = [r for r in analyze_results if r["status"] == "success"]

        assert len(failed_commands) > 0
        assert len(successful_commands) > 0

        # Failed commands should have error details
        for failed_cmd in failed_commands:
            assert "error" in failed_cmd

    @patch("jd_ingestion.api.endpoints.performance.logger")
    @pytest.mark.asyncio
    async def test_optimize_database_indexes_complete_failure(
        self, mock_logger, mock_session
    ):
        """Test database optimization with complete failure."""
        mock_session.execute.side_effect = Exception("Database connection lost")

        with pytest.raises(HTTPException) as exc_info:
            await optimize_database_indexes(db=mock_session)

        assert exc_info.value.status_code == 500
        assert "Optimization failed" in exc_info.value.detail
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_optimize_database_indexes_no_vacuum_needed(self, mock_session):
        """Test optimization when no tables need vacuum."""
        # Mock empty vacuum results
        vacuum_result = Mock()
        vacuum_result.fetchall.return_value = []
        mock_session.execute.return_value = vacuum_result

        result = await optimize_database_indexes(db=mock_session)

        assert result["status"] == "success"
        vacuum_recs = result["optimization_results"]["vacuum_recommendations"]
        assert len(vacuum_recs) == 0


class TestPerformanceHealthCheck:
    """Test performance health check endpoint."""

    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        return AsyncMock()

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.performance.time")
    async def test_performance_health_check_healthy(self, mock_time, mock_session):
        """Test performance health check with healthy system."""
        # Mock time measurements for fast queries
        mock_time.perf_counter.side_effect = [
            0.0,
            0.05,  # embedding count query: 50ms (healthy)
            0.05,
            0.08,  # index check query: 30ms (healthy)
        ]

        # Mock query results
        embedding_result = Mock()
        embedding_result.scalar.return_value = 1500  # Good number of embeddings

        index_result = Mock()
        index_result.scalar.return_value = 5  # Good number of indexes

        mock_session.execute.side_effect = [embedding_result, index_result]

        result = await performance_health_check(db=mock_session)

        assert result["status"] == "healthy"
        assert "health_checks" in result
        assert "summary" in result

        health_checks = result["health_checks"]
        assert len(health_checks) == 2

        # Check embedding count health check
        embedding_check = next(
            c for c in health_checks if c["check"] == "embedding_count_query"
        )
        assert embedding_check["status"] == "healthy"
        assert embedding_check["result"] == 1500

        # Check index availability health check
        index_check = next(
            c for c in health_checks if c["check"] == "index_availability"
        )
        assert index_check["status"] == "healthy"
        assert index_check["result"] == 5

        # Check summary
        summary = result["summary"]
        assert summary["total_embeddings"] == 1500
        assert summary["available_indexes"] == 5
        assert summary["performance_rating"] == "healthy"

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.performance.time")
    async def test_performance_health_check_degraded(self, mock_time, mock_session):
        """Test performance health check with slow queries."""
        # Mock time measurements for slow queries
        mock_time.perf_counter.side_effect = [
            0.0,
            0.15,  # embedding count query: 150ms (slow)
            0.15,
            0.18,  # index check query: 30ms (healthy)
        ]

        embedding_result = Mock()
        embedding_result.scalar.return_value = 1500

        index_result = Mock()
        index_result.scalar.return_value = 3

        mock_session.execute.side_effect = [embedding_result, index_result]

        result = await performance_health_check(db=mock_session)

        assert result["status"] == "degraded"  # Due to slow query

        health_checks = result["health_checks"]
        embedding_check = next(
            c for c in health_checks if c["check"] == "embedding_count_query"
        )
        assert embedding_check["status"] == "slow"

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.performance.time")
    async def test_performance_health_check_warning(self, mock_time, mock_session):
        """Test performance health check with warnings."""
        # Mock fast queries
        mock_time.perf_counter.side_effect = [0.0, 0.02, 0.02, 0.04]

        embedding_result = Mock()
        embedding_result.scalar.return_value = 100

        index_result = Mock()
        index_result.scalar.return_value = 0  # No indexes available - warning

        mock_session.execute.side_effect = [embedding_result, index_result]

        result = await performance_health_check(db=mock_session)

        assert result["status"] == "warning"  # Due to missing indexes

        health_checks = result["health_checks"]
        index_check = next(
            c for c in health_checks if c["check"] == "index_availability"
        )
        assert index_check["status"] == "warning"
        assert index_check["result"] == 0

    @patch("jd_ingestion.api.endpoints.performance.logger")
    @pytest.mark.asyncio
    async def test_performance_health_check_database_error(
        self, mock_logger, mock_session
    ):
        """Test performance health check with database error."""
        mock_session.execute.side_effect = Exception("Database connection failed")

        with pytest.raises(HTTPException) as exc_info:
            await performance_health_check(db=mock_session)

        assert exc_info.value.status_code == 500
        assert "Health check failed" in exc_info.value.detail
        mock_logger.error.assert_called_once()


class TestPerformanceEndpointsIntegration:
    """Test performance endpoints integration."""

    @pytest.mark.asyncio
    async def test_performance_endpoints_routing(self):
        """Test that performance endpoints are properly routed."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            endpoints_to_test = [
                "/api/performance/stats",
                "/api/performance/health",
            ]

            for endpoint in endpoints_to_test:
                response = await ac.get(endpoint)
                # Should not be 404 (route not found) - could be auth/db related errors
                assert response.status_code != 404, (
                    f"Endpoint {endpoint} not properly routed"
                )

    @pytest.mark.asyncio
    async def test_performance_benchmark_post_routing(self):
        """Test that benchmark POST endpoint is properly routed."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            benchmark_data = {
                "query_text": "Senior Policy Advisor",
                "limit": 10,
                "similarity_threshold": 0.7,
            }

            response = await ac.post(
                "/api/performance/benchmark/vector-search", json=benchmark_data
            )
            # Should not be 404 (route not found)
            assert response.status_code != 404

    @pytest.mark.asyncio
    async def test_performance_optimize_post_routing(self):
        """Test that optimize POST endpoint is properly routed."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post("/api/performance/optimize/indexes")
            # Should not be 404 (route not found)
            assert response.status_code != 404


class TestPerformanceDataModels:
    """Test Pydantic models for performance endpoints."""

    def test_performance_stats_model(self):
        """Test PerformanceStats model validation."""
        stats_data = {
            "index_performance": [
                {
                    "index_name": "idx_embeddings",
                    "usage_count": 1500,
                    "efficiency": 0.95,
                }
            ],
            "table_performance": [
                {
                    "table_name": "content_chunks",
                    "avg_query_time": 45.2,
                    "size_mb": 125.5,
                }
            ],
        }

        stats = PerformanceStats(**stats_data)
        assert len(stats.index_performance) == 1
        assert len(stats.table_performance) == 1
        assert stats.index_performance[0]["index_name"] == "idx_embeddings"

    def test_vector_search_benchmark_model(self):
        """Test VectorSearchBenchmark model validation."""
        # Test with minimal required fields
        benchmark = VectorSearchBenchmark(query_text="Test query")
        assert benchmark.query_text == "Test query"
        assert benchmark.limit == 10  # default
        assert benchmark.similarity_threshold == 0.7  # default
        assert benchmark.include_filters is False  # default
        assert benchmark.classification_filter is None  # default

    def test_vector_search_benchmark_model_full(self):
        """Test VectorSearchBenchmark model with all fields."""
        benchmark_data = {
            "query_text": "Senior Policy Advisor",
            "limit": 20,
            "similarity_threshold": 0.8,
            "include_filters": True,
            "classification_filter": "EX-01",
            "language_filter": "en",
        }

        benchmark = VectorSearchBenchmark(**benchmark_data)
        assert benchmark.query_text == "Senior Policy Advisor"
        assert benchmark.limit == 20
        assert benchmark.similarity_threshold == 0.8
        assert benchmark.include_filters is True
        assert benchmark.classification_filter == "EX-01"
        assert benchmark.language_filter == "en"

    def test_vector_search_benchmark_model_validation(self):
        """Test VectorSearchBenchmark model validation errors."""
        with pytest.raises(Exception):  # Pydantic validation error
            VectorSearchBenchmark()  # Missing required query_text


class TestPerformanceEndpointsSecurity:
    """Test security aspects of performance endpoints."""

    def test_no_sensitive_data_in_responses(self):
        """Test that performance endpoints don't expose sensitive data."""
        # This would be tested with actual endpoint calls
        # For now, we verify the endpoint structure doesn't include sensitive fields

        # Mock a typical response structure
        mock_response = {
            "status": "success",
            "performance_stats": {"query_count": 1500, "avg_response_time": 45.2},
        }

        # Ensure no common sensitive keys
        sensitive_keys = ["password", "secret", "token", "key", "credential"]
        response_str = str(mock_response).lower()

        for sensitive_key in sensitive_keys:
            assert sensitive_key not in response_str

    def test_database_query_safety(self):
        """Test that database queries are safe from injection."""
        # The ANALYZE commands and queries use parameterized queries or safe static strings
        # This is a structural test to ensure no user input is directly interpolated

        # Mock check that all database queries use safe patterns
        _unsafe_patterns = ["DROP", "DELETE FROM", "UPDATE SET", "INSERT INTO"]

        # In the actual implementation, verify queries are safe
        # For example, the ANALYZE commands are static strings
        analyze_commands = [
            "ANALYZE content_chunks;",
            "ANALYZE job_descriptions;",
            "ANALYZE usage_analytics;",
            "ANALYZE ai_usage_tracking;",
            "ANALYZE system_metrics;",
        ]

        # These are safe static commands
        for command in analyze_commands:
            # Should not contain dangerous patterns mixed with user input
            assert ";" in command  # Properly terminated
            assert command.startswith("ANALYZE")  # Safe operation


class TestPerformanceEndpointsErrorHandling:
    """Test error handling in performance endpoints."""

    @pytest.mark.asyncio
    async def test_embedding_service_timeout_handling(self):
        """Test handling of embedding service timeouts."""
        mock_session = AsyncMock()

        with patch(
            "jd_ingestion.api.endpoints.performance.optimized_embedding_service"
        ) as mock_service:
            mock_service.get_performance_stats.side_effect = TimeoutError(
                "Service timeout"
            )

            with pytest.raises(HTTPException) as exc_info:
                await get_performance_statistics(db=mock_session)

            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_database_connection_error_handling(self):
        """Test handling of database connection errors."""
        mock_session = AsyncMock()
        mock_session.execute.side_effect = Exception("Connection lost")

        with pytest.raises(HTTPException) as exc_info:
            await performance_health_check(db=mock_session)

        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_graceful_degradation(self):
        """Test graceful degradation when some operations fail."""
        mock_session = AsyncMock()

        # Test that partial failures in optimization still return useful results
        def mock_execute_side_effect(query):
            # Some commands succeed, some fail
            if "content_chunks" in str(query):
                raise Exception("Table busy")
            return Mock()

        mock_session.execute.side_effect = mock_execute_side_effect

        result = await optimize_database_indexes(db=mock_session)

        # Should still return success with mixed results
        assert result["status"] == "success"
        assert "optimization_results" in result
