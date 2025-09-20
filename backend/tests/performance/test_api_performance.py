"""
API Performance Tests

Tests the performance of critical API endpoints under load
to ensure they meet response time requirements.
"""
import asyncio
import pytest
import time
from typing import List, Dict, Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.jd_ingestion.api.main import app
from src.jd_ingestion.database.connection import get_db
from tests.conftest import test_session


class TestAPIPerformance:
    """Performance tests for critical API endpoints."""

    @pytest.mark.benchmark(group="search")
    def test_search_performance(self, benchmark):
        """Test search endpoint performance."""
        client = TestClient(app)

        def search_operation():
            response = client.get("/api/search?q=manager&limit=10")
            assert response.status_code == 200
            return response.json()

        result = benchmark(search_operation)
        assert "results" in result

    @pytest.mark.benchmark(group="jobs")
    def test_job_listing_performance(self, benchmark):
        """Test job listing endpoint performance."""
        client = TestClient(app)

        def job_listing_operation():
            response = client.get("/api/jobs?limit=20&skip=0")
            assert response.status_code == 200
            return response.json()

        result = benchmark(job_listing_operation)
        assert "jobs" in result

    @pytest.mark.benchmark(group="jobs")
    def test_job_statistics_performance(self, benchmark):
        """Test job statistics endpoint performance."""
        client = TestClient(app)

        def stats_operation():
            response = client.get("/api/jobs/statistics")
            assert response.status_code == 200
            return response.json()

        result = benchmark(stats_operation)
        assert "total_jobs" in result

    @pytest.mark.benchmark(group="translation")
    def test_translation_memory_search(self, benchmark):
        """Test translation memory search performance."""
        client = TestClient(app)

        def tm_search_operation():
            response = client.post("/api/translation-memory/suggestions", json={
                "source_text": "Responsible for strategic planning",
                "source_language": "en",
                "target_language": "fr"
            })
            assert response.status_code == 200
            return response.json()

        result = benchmark(tm_search_operation)
        assert "suggestions" in result

    @pytest.mark.benchmark(group="vector_search")
    def test_vector_similarity_search(self, benchmark):
        """Test vector similarity search performance."""
        client = TestClient(app)

        def vector_search_operation():
            response = client.get("/api/search?q=software engineer&search_type=semantic&limit=10")
            assert response.status_code == 200
            return response.json()

        result = benchmark(vector_search_operation)
        assert "results" in result

    @pytest.mark.benchmark(group="analytics")
    def test_analytics_performance(self, benchmark):
        """Test analytics endpoint performance."""
        client = TestClient(app)

        def analytics_operation():
            response = client.get("/api/analytics/performance-summary")
            assert response.status_code == 200
            return response.json()

        result = benchmark(analytics_operation)
        assert "summary" in result

    def test_concurrent_search_requests(self):
        """Test performance under concurrent load."""
        client = TestClient(app)
        num_concurrent = 10
        search_queries = [
            "software engineer", "project manager", "data scientist",
            "business analyst", "product manager", "developer",
            "designer", "coordinator", "specialist", "director"
        ]

        def make_search_request(query: str):
            start_time = time.time()
            response = client.get(f"/api/search?q={query}&limit=5")
            end_time = time.time()

            assert response.status_code == 200
            return {
                "query": query,
                "response_time": end_time - start_time,
                "status_code": response.status_code,
                "result_count": len(response.json().get("results", []))
            }

        # Execute concurrent requests
        start_time = time.time()
        results = []

        # Simulate concurrent requests (simplified for synchronous client)
        for i in range(num_concurrent):
            query = search_queries[i % len(search_queries)]
            result = make_search_request(query)
            results.append(result)

        total_time = time.time() - start_time

        # Analyze results
        response_times = [r["response_time"] for r in results]
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        successful_requests = len([r for r in results if r["status_code"] == 200])

        print(f"\nConcurrent Request Performance:")
        print(f"  Total requests: {num_concurrent}")
        print(f"  Successful requests: {successful_requests}")
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Average response time: {avg_response_time:.3f}s")
        print(f"  Maximum response time: {max_response_time:.3f}s")
        print(f"  Requests per second: {num_concurrent / total_time:.2f}")

        # Performance assertions
        assert successful_requests == num_concurrent, "All requests should succeed"
        assert avg_response_time < 2.0, f"Average response time too high: {avg_response_time:.3f}s"
        assert max_response_time < 5.0, f"Maximum response time too high: {max_response_time:.3f}s"

    def test_memory_usage_under_load(self):
        """Test memory usage under sustained load."""
        import psutil
        import os

        client = TestClient(app)
        process = psutil.Process(os.getpid())

        # Get initial memory usage
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Perform sustained operations
        for i in range(50):
            # Mix of different operations
            client.get("/api/jobs?limit=20")
            client.get("/api/search?q=engineer&limit=10")
            client.get("/api/analytics/performance-summary")

            if i % 10 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                print(f"Memory usage after {i+1} requests: {current_memory:.1f}MB")

        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        print(f"\nMemory Usage Analysis:")
        print(f"  Initial memory: {initial_memory:.1f}MB")
        print(f"  Final memory: {final_memory:.1f}MB")
        print(f"  Memory increase: {memory_increase:.1f}MB")

        # Memory usage assertions
        assert memory_increase < 100, f"Memory increase too high: {memory_increase:.1f}MB"

    def test_database_connection_pool_performance(self):
        """Test database connection pool performance."""
        client = TestClient(app)

        # Test rapid consecutive database operations
        start_time = time.time()

        for i in range(20):
            response = client.get("/api/jobs/statistics")
            assert response.status_code == 200

        total_time = time.time() - start_time
        avg_time_per_request = total_time / 20

        print(f"\nDatabase Connection Pool Performance:")
        print(f"  Total time for 20 requests: {total_time:.3f}s")
        print(f"  Average time per request: {avg_time_per_request:.3f}s")
        print(f"  Requests per second: {20 / total_time:.2f}")

        # Performance assertions
        assert avg_time_per_request < 0.5, f"Database operations too slow: {avg_time_per_request:.3f}s"