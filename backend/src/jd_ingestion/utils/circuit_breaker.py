"""
Circuit Breaker Pattern Implementation for Enhanced Resilience
"""

import asyncio
import time
from enum import Enum
from typing import Any, Optional, Dict, List
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
import threading
from ..utils.logging import get_logger

logger = get_logger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit is open, failing fast
    HALF_OPEN = "half_open"  # Testing if service is recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5  # Number of failures to open circuit
    recovery_timeout: float = 60.0  # Time in seconds before trying half-open
    success_threshold: int = 3  # Successes needed in half-open to close
    timeout: float = 30.0  # Operation timeout
    expected_exception: tuple = (Exception,)  # Exceptions that count as failures


@dataclass
class CircuitBreakerMetrics:
    """Metrics tracking for circuit breaker."""

    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    total_requests: int = 0
    total_failures: int = 0
    total_successes: int = 0
    state_changes: List[str] = field(default_factory=list)


class CircuitBreaker:
    """
    Async Circuit Breaker for protecting external service calls.

    Automatically opens when failure threshold is reached,
    and allows testing recovery after timeout period.
    """

    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitState.CLOSED
        self.metrics = CircuitBreakerMetrics()
        self._lock = threading.Lock()

        logger.info(
            "Circuit breaker initialized",
            name=self.name,
            failure_threshold=self.config.failure_threshold,
            recovery_timeout=self.config.recovery_timeout,
        )

    @asynccontextmanager
    async def protect(self, operation_name: str = "unknown"):
        """
        Context manager to protect an operation with circuit breaker.

        Usage:
            async with circuit_breaker.protect("api_call"):
                result = await some_external_api_call()
        """
        start_time = time.time()

        # Check if circuit is open
        if not self._can_execute():
            self._record_blocked_request()
            raise CircuitBreakerOpenException(
                f"Circuit breaker '{self.name}' is OPEN. Operation '{operation_name}' blocked."
            )

        try:
            # Execute operation with timeout
            async with asyncio.timeout(self.config.timeout):
                self.metrics.total_requests += 1
                yield

            # Success
            execution_time = time.time() - start_time
            self._record_success(execution_time)

        except asyncio.TimeoutError as e:
            execution_time = time.time() - start_time
            logger.warning(
                "Circuit breaker operation timeout",
                name=self.name,
                operation=operation_name,
                timeout=self.config.timeout,
                execution_time=execution_time,
            )
            self._record_failure(e)
            raise

        except self.config.expected_exception as e:
            execution_time = time.time() - start_time
            self._record_failure(e, execution_time)
            raise

        except Exception as e:
            # Unexpected exceptions don't count as failures
            execution_time = time.time() - start_time
            logger.error(
                "Unexpected exception in circuit breaker",
                name=self.name,
                operation=operation_name,
                error=str(e),
                execution_time=execution_time,
            )
            raise

    def _can_execute(self) -> bool:
        """Check if operation can be executed based on current state."""
        with self._lock:
            current_time = time.time()

            if self.state == CircuitState.CLOSED:
                return True

            elif self.state == CircuitState.OPEN:
                # Check if enough time has passed to try half-open
                if (
                    self.metrics.last_failure_time
                    and current_time - self.metrics.last_failure_time
                    >= self.config.recovery_timeout
                ):
                    self._transition_to_half_open()
                    return True
                return False

            elif self.state == CircuitState.HALF_OPEN:
                return True

            return False

    def _record_success(self, execution_time: Optional[float] = None):
        """Record a successful operation."""
        with self._lock:
            self.metrics.success_count += 1
            self.metrics.total_successes += 1
            self.metrics.last_success_time = time.time()

            logger.debug(
                "Circuit breaker success recorded",
                name=self.name,
                success_count=self.metrics.success_count,
                state=self.state.value,
                execution_time=execution_time,
            )

            # State transitions based on success
            if self.state == CircuitState.HALF_OPEN:
                if self.metrics.success_count >= self.config.success_threshold:
                    self._transition_to_closed()

            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.metrics.failure_count = 0

    def _record_failure(
        self, exception: Exception, execution_time: Optional[float] = None
    ):
        """Record a failed operation."""
        with self._lock:
            self.metrics.failure_count += 1
            self.metrics.total_failures += 1
            self.metrics.last_failure_time = time.time()

            logger.warning(
                "Circuit breaker failure recorded",
                name=self.name,
                failure_count=self.metrics.failure_count,
                state=self.state.value,
                error=str(exception),
                execution_time=execution_time,
            )

            # State transitions based on failure
            if self.state == CircuitState.CLOSED:
                if self.metrics.failure_count >= self.config.failure_threshold:
                    self._transition_to_open()

            elif self.state == CircuitState.HALF_OPEN:
                self._transition_to_open()

    def _record_blocked_request(self):
        """Record a request that was blocked by open circuit."""
        with self._lock:
            self.metrics.total_requests += 1
            logger.debug(
                "Circuit breaker blocked request",
                name=self.name,
                state=self.state.value,
            )

    def _transition_to_open(self):
        """Transition circuit to OPEN state."""
        if self.state != CircuitState.OPEN:
            previous_state = self.state.value
            self.state = CircuitState.OPEN
            self.metrics.state_changes.append(
                f"{previous_state} -> OPEN at {time.time()}"
            )

            logger.warning(
                "Circuit breaker opened",
                name=self.name,
                previous_state=previous_state,
                failure_count=self.metrics.failure_count,
                failure_threshold=self.config.failure_threshold,
            )

    def _transition_to_half_open(self):
        """Transition circuit to HALF_OPEN state."""
        if self.state != CircuitState.HALF_OPEN:
            previous_state = self.state.value
            self.state = CircuitState.HALF_OPEN
            self.metrics.success_count = 0  # Reset success counter
            self.metrics.state_changes.append(
                f"{previous_state} -> HALF_OPEN at {time.time()}"
            )

            logger.info(
                "Circuit breaker half-opened",
                name=self.name,
                previous_state=previous_state,
            )

    def _transition_to_closed(self):
        """Transition circuit to CLOSED state."""
        if self.state != CircuitState.CLOSED:
            previous_state = self.state.value
            self.state = CircuitState.CLOSED
            self.metrics.failure_count = 0  # Reset failure counter
            self.metrics.success_count = 0  # Reset success counter
            self.metrics.state_changes.append(
                f"{previous_state} -> CLOSED at {time.time()}"
            )

            logger.info(
                "Circuit breaker closed", name=self.name, previous_state=previous_state
            )

    def get_metrics(self) -> Dict[str, Any]:
        """Get current circuit breaker metrics."""
        with self._lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "failure_count": self.metrics.failure_count,
                "success_count": self.metrics.success_count,
                "total_requests": self.metrics.total_requests,
                "total_failures": self.metrics.total_failures,
                "total_successes": self.metrics.total_successes,
                "last_failure_time": self.metrics.last_failure_time,
                "last_success_time": self.metrics.last_success_time,
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "success_threshold": self.config.success_threshold,
                "recent_state_changes": self.metrics.state_changes[
                    -10:
                ],  # Last 10 changes
                "failure_rate": (
                    self.metrics.total_failures / self.metrics.total_requests
                    if self.metrics.total_requests > 0
                    else 0
                ),
            }

    def reset(self):
        """Reset circuit breaker to initial state."""
        with self._lock:
            self.state = CircuitState.CLOSED
            self.metrics = CircuitBreakerMetrics()
            logger.info("Circuit breaker reset", name=self.name)


class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open."""

    pass


class CircuitBreakerManager:
    """Global manager for circuit breakers."""

    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.Lock()

    def get_breaker(
        self, name: str, config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """Get or create a circuit breaker."""
        with self._lock:
            if name not in self._breakers:
                if config is None:
                    config = CircuitBreakerConfig()
                self._breakers[name] = CircuitBreaker(name, config)
            return self._breakers[name]

    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all circuit breakers."""
        with self._lock:
            return {
                name: breaker.get_metrics() for name, breaker in self._breakers.items()
            }

    def reset_all(self):
        """Reset all circuit breakers."""
        with self._lock:
            for breaker in self._breakers.values():
                breaker.reset()
            logger.info("All circuit breakers reset")


# Global circuit breaker manager
circuit_breaker_manager = CircuitBreakerManager()


def get_circuit_breaker(
    name: str, config: Optional[CircuitBreakerConfig] = None
) -> CircuitBreaker:
    """Convenience function to get a circuit breaker."""
    return circuit_breaker_manager.get_breaker(name, config)


# Pre-configured circuit breakers for common services
def get_openai_circuit_breaker() -> CircuitBreaker:
    """Get circuit breaker configured for OpenAI API calls."""
    config = CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=120.0,  # 2 minutes
        success_threshold=2,
        timeout=60.0,  # 1 minute timeout for API calls
        expected_exception=(ConnectionError, TimeoutError, RuntimeError),
    )
    return get_circuit_breaker("openai_api", config)


def get_database_circuit_breaker() -> CircuitBreaker:
    """Get circuit breaker configured for database operations."""
    config = CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=30.0,  # 30 seconds
        success_threshold=3,
        timeout=30.0,
        expected_exception=(ConnectionError, TimeoutError, OSError),
    )
    return get_circuit_breaker("database", config)
