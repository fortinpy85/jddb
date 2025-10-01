import pytest
import asyncio
import time

from jd_ingestion.utils.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    CircuitBreakerOpenException,
    CircuitBreakerMetrics,
)


class TestCircuitBreaker:
    """Test suite for the CircuitBreaker class."""

    @pytest.fixture
    def default_config(self):
        """Create default circuit breaker config."""
        return CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=1.0,  # Short timeout for testing
            success_threshold=2,
            timeout=2.0,
            expected_exception=(ValueError, RuntimeError),
        )

    @pytest.fixture
    def circuit_breaker(self, default_config):
        """Create a circuit breaker instance for testing."""
        return CircuitBreaker("test_service", default_config)

    @pytest.fixture
    def fast_recovery_config(self):
        """Circuit breaker config with very fast recovery for testing."""
        return CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=0.1,  # 100ms recovery
            success_threshold=1,
            timeout=1.0,
            expected_exception=(Exception,),
        )

    def test_circuit_breaker_initialization(self, circuit_breaker, default_config):
        """Test circuit breaker initializes correctly."""
        assert circuit_breaker.name == "test_service"
        assert circuit_breaker.config == default_config
        assert circuit_breaker.state == CircuitState.CLOSED
        assert isinstance(circuit_breaker.metrics, CircuitBreakerMetrics)
        assert circuit_breaker.metrics.failure_count == 0
        assert circuit_breaker.metrics.total_requests == 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_successful_operation(self, circuit_breaker):
        """Test successful operation in closed state."""

        async def successful_operation():
            return "success"

        async with circuit_breaker.protect("test_op"):
            result = await successful_operation()

        assert result == "success"
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.metrics.total_requests == 1
        assert circuit_breaker.metrics.total_successes == 1
        assert circuit_breaker.metrics.failure_count == 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_failure_counting(self, circuit_breaker):
        """Test failure counting and state transitions."""

        async def failing_operation():
            raise ValueError("Operation failed")

        # First failure
        with pytest.raises(ValueError):
            async with circuit_breaker.protect("test_op"):
                await failing_operation()

        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.metrics.failure_count == 1
        assert circuit_breaker.metrics.total_failures == 1

        # Second failure
        with pytest.raises(ValueError):
            async with circuit_breaker.protect("test_op"):
                await failing_operation()

        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.metrics.failure_count == 2

        # Third failure - should open circuit
        with pytest.raises(ValueError):
            async with circuit_breaker.protect("test_op"):
                await failing_operation()

        assert circuit_breaker.state == CircuitState.OPEN
        assert circuit_breaker.metrics.failure_count == 3

    @pytest.mark.asyncio
    async def test_circuit_breaker_open_state_blocks_operations(self, circuit_breaker):
        """Test that open circuit breaker blocks operations."""
        # Force circuit to open state
        circuit_breaker.state = CircuitState.OPEN
        circuit_breaker.metrics.failure_count = 3
        circuit_breaker.metrics.last_failure_time = time.time()

        # Attempt operation - should be blocked
        with pytest.raises(
            CircuitBreakerOpenException, match="Circuit breaker 'test_service' is OPEN"
        ):
            async with circuit_breaker.protect("blocked_op"):
                await asyncio.sleep(0.1)

        # Operation should not have been executed
        assert circuit_breaker.metrics.total_requests == 0  # Request was blocked

    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_recovery(self, fast_recovery_config):
        """Test circuit breaker recovery through half-open state."""
        circuit_breaker = CircuitBreaker("recovery_test", fast_recovery_config)

        # Force circuit to open state
        circuit_breaker.state = CircuitState.OPEN
        circuit_breaker.metrics.failure_count = 2
        circuit_breaker.metrics.last_failure_time = (
            time.time() - 0.2
        )  # Past recovery timeout

        async def successful_recovery():
            return "recovered"

        # Should transition to half-open and then closed on success
        async with circuit_breaker.protect("recovery_op"):
            result = await successful_recovery()

        assert result == "recovered"
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.metrics.failure_count == 0  # Reset on recovery

    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_failure(self, fast_recovery_config):
        """Test circuit breaker failure in half-open state."""
        circuit_breaker = CircuitBreaker("failure_test", fast_recovery_config)

        # Force circuit to open state
        circuit_breaker.state = CircuitState.OPEN
        circuit_breaker.metrics.failure_count = 2
        circuit_breaker.metrics.last_failure_time = (
            time.time() - 0.2
        )  # Past recovery timeout

        async def still_failing():
            raise Exception("Still broken")

        # Should fail and go back to open
        with pytest.raises(Exception, match="Still broken"):
            async with circuit_breaker.protect("failing_recovery"):
                await still_failing()

        assert circuit_breaker.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_circuit_breaker_timeout_handling(self, circuit_breaker):
        """Test operation timeout handling."""

        async def slow_operation():
            await asyncio.sleep(3.0)  # Longer than timeout
            return "too_slow"

        with pytest.raises(asyncio.TimeoutError):
            async with circuit_breaker.protect("slow_op"):
                await slow_operation()

        # Timeout should count as a failure
        assert circuit_breaker.metrics.failure_count == 1
        assert circuit_breaker.metrics.total_failures == 1

    @pytest.mark.asyncio
    async def test_circuit_breaker_unexpected_exception_handling(self, circuit_breaker):
        """Test handling of unexpected exceptions that don't count as failures."""

        async def unexpected_error():
            raise KeyError("Unexpected error")  # Not in expected_exception tuple

        with pytest.raises(KeyError, match="Unexpected error"):
            async with circuit_breaker.protect("unexpected_op"):
                await unexpected_error()

        # Unexpected exceptions should not count as failures
        assert circuit_breaker.metrics.failure_count == 0
        assert circuit_breaker.metrics.total_failures == 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_expected_exception_types(self):
        """Test circuit breaker with specific expected exception types."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            expected_exception=(ValueError,),  # Only ValueError counts
        )
        circuit_breaker = CircuitBreaker("specific_test", config)

        # ValueError should count as failure
        async def value_error_op():
            raise ValueError("Expected error")

        with pytest.raises(ValueError):
            async with circuit_breaker.protect("value_error"):
                await value_error_op()

        assert circuit_breaker.metrics.failure_count == 1

        # RuntimeError should not count as failure
        async def runtime_error_op():
            raise RuntimeError("Unexpected error")

        with pytest.raises(RuntimeError):
            async with circuit_breaker.protect("runtime_error"):
                await runtime_error_op()

        assert circuit_breaker.metrics.failure_count == 1  # Should remain 1

    @pytest.mark.asyncio
    async def test_circuit_breaker_success_resets_failure_count(self, circuit_breaker):
        """Test that success resets failure count in closed state."""

        async def failing_operation():
            raise ValueError("Failure")

        async def successful_operation():
            return "success"

        # Two failures
        for _ in range(2):
            with pytest.raises(ValueError):
                async with circuit_breaker.protect("fail_op"):
                    await failing_operation()

        assert circuit_breaker.metrics.failure_count == 2

        # Success should reset failure count
        async with circuit_breaker.protect("success_op"):
            await successful_operation()

        assert circuit_breaker.metrics.failure_count == 0
        assert circuit_breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_breaker_metrics_tracking(self, circuit_breaker):
        """Test comprehensive metrics tracking."""

        async def successful_op():
            return "ok"

        async def failing_op():
            raise ValueError("fail")

        # Success
        async with circuit_breaker.protect("success"):
            await successful_op()

        # Failure
        with pytest.raises(ValueError):
            async with circuit_breaker.protect("failure"):
                await failing_op()

        metrics = circuit_breaker.metrics
        assert metrics.total_requests == 2
        assert metrics.total_successes == 1
        assert metrics.total_failures == 1
        assert metrics.failure_count == 1
        assert metrics.last_success_time is not None
        assert metrics.last_failure_time is not None

    def test_circuit_breaker_state_transitions(self, circuit_breaker):
        """Test manual state transitions."""
        assert circuit_breaker.state == CircuitState.CLOSED

        # Simulate state changes
        circuit_breaker.state = CircuitState.OPEN
        assert circuit_breaker.state == CircuitState.OPEN

        circuit_breaker.state = CircuitState.HALF_OPEN
        assert circuit_breaker.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_circuit_breaker_concurrent_operations(self, circuit_breaker):
        """Test circuit breaker with concurrent operations."""

        async def concurrent_operation(op_id):
            await asyncio.sleep(0.1)
            return f"result_{op_id}"

        # Run multiple concurrent operations
        tasks = [circuit_breaker.protect(f"op_{i}").__aenter__() for i in range(5)]

        # All should succeed concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Clean up context managers
        for i, task in enumerate(tasks):
            if not isinstance(results[i], Exception):
                await results[i].__aexit__(None, None, None)

        assert circuit_breaker.metrics.total_requests >= 5

    def test_circuit_breaker_config_defaults(self):
        """Test CircuitBreakerConfig default values."""
        config = CircuitBreakerConfig()
        assert config.failure_threshold == 5
        assert config.recovery_timeout == 60.0
        assert config.success_threshold == 3
        assert config.timeout == 30.0
        assert config.expected_exception == (Exception,)

    def test_circuit_breaker_metrics_initialization(self):
        """Test CircuitBreakerMetrics initialization."""
        metrics = CircuitBreakerMetrics()
        assert metrics.failure_count == 0
        assert metrics.success_count == 0
        assert metrics.last_failure_time is None
        assert metrics.last_success_time is None
        assert metrics.total_requests == 0
        assert metrics.total_failures == 0
        assert metrics.total_successes == 0
        assert isinstance(metrics.state_changes, list)
        assert len(metrics.state_changes) == 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_context_manager_cleanup(self, circuit_breaker):
        """Test proper cleanup of context manager resources."""

        async def test_operation():
            return "test"

        # Normal success path
        async with circuit_breaker.protect("cleanup_test"):
            result = await test_operation()

        assert result == "test"
        # Metrics should be properly updated
        assert circuit_breaker.metrics.total_requests == 1
        assert circuit_breaker.metrics.total_successes == 1

    @pytest.mark.asyncio
    async def test_circuit_breaker_with_different_operation_names(
        self, circuit_breaker
    ):
        """Test circuit breaker with different operation names."""

        async def operation_a():
            return "a"

        async def operation_b():
            raise ValueError("b failed")

        # Success with operation A
        async with circuit_breaker.protect("operation_a"):
            result_a = await operation_a()

        # Failure with operation B
        with pytest.raises(ValueError):
            async with circuit_breaker.protect("operation_b"):
                await operation_b()

        assert result_a == "a"
        assert circuit_breaker.metrics.total_requests == 2
        assert circuit_breaker.metrics.total_successes == 1
        assert circuit_breaker.metrics.total_failures == 1
