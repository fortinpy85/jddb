"""
Rate Limiting Service

API rate limiting and cost management for external services, particularly OpenAI API.
Implements token bucket algorithm with sliding window counters for precise rate limiting.
"""

import asyncio
import time
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
import hashlib

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from ..database.models import AIUsageTracking
from ..utils.logging import get_logger
from ..utils.cache import cache_service

logger = get_logger(__name__)


class RateLimitType(Enum):
    """Types of rate limits."""

    REQUESTS_PER_MINUTE = "requests_per_minute"
    TOKENS_PER_MINUTE = "tokens_per_minute"
    COST_PER_HOUR = "cost_per_hour"
    COST_PER_DAY = "cost_per_day"


@dataclass
class RateLimit:
    """Rate limit configuration."""

    limit: int
    window_seconds: int
    burst_allowance: float = 1.2  # Allow 20% burst


@dataclass
class RateLimitStatus:
    """Current rate limit status."""

    limit_type: RateLimitType
    current_usage: int
    limit: int
    window_remaining_seconds: int
    reset_time: datetime
    is_exceeded: bool


class TokenBucket:
    """Token bucket implementation for rate limiting."""

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()
        self._lock = asyncio.Lock()

    async def consume(self, tokens: int = 1) -> bool:
        """Attempt to consume tokens from bucket."""
        async with self._lock:
            now = time.time()
            # Add tokens based on time passed
            time_passed = now - self.last_refill
            self.tokens = min(
                self.capacity, self.tokens + (time_passed * self.refill_rate)
            )
            self.last_refill = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    async def get_status(self) -> Dict[str, float]:
        """Get current bucket status."""
        async with self._lock:
            now = time.time()
            time_passed = now - self.last_refill
            current_tokens = min(
                self.capacity, self.tokens + (time_passed * self.refill_rate)
            )

            return {
                "current_tokens": current_tokens,
                "capacity": self.capacity,
                "fill_rate": self.refill_rate,
                "utilization": 1.0 - (current_tokens / self.capacity),
            }


class SlidingWindowCounter:
    """Sliding window counter for tracking usage over time windows."""

    def __init__(self, window_seconds: int):
        self.window_seconds = window_seconds
        self.requests = deque()
        self._lock = asyncio.Lock()

    async def add_request(
        self, amount: int = 1, timestamp: Optional[float] = None
    ) -> None:
        """Add a request to the counter."""
        if timestamp is None:
            timestamp = time.time()

        async with self._lock:
            self.requests.append((timestamp, amount))
            await self._cleanup_old_requests()

    async def get_count(self) -> int:
        """Get current count within the window."""
        async with self._lock:
            await self._cleanup_old_requests()
            return sum(amount for _, amount in self.requests)

    async def _cleanup_old_requests(self) -> None:
        """Remove requests outside the current window."""
        cutoff = time.time() - self.window_seconds
        while self.requests and self.requests[0][0] < cutoff:
            self.requests.popleft()


class RateLimitingService:
    """Service for managing API rate limits and cost optimization."""

    def __init__(self):
        # Rate limit configurations
        self.rate_limits: Dict[str, Dict[RateLimitType, RateLimit]] = {
            "openai": {
                RateLimitType.REQUESTS_PER_MINUTE: RateLimit(
                    3000, 60
                ),  # OpenAI's RPM limit
                RateLimitType.TOKENS_PER_MINUTE: RateLimit(
                    150000, 60
                ),  # OpenAI's TPM limit
                RateLimitType.COST_PER_HOUR: RateLimit(50, 3600),  # $50/hour limit
                RateLimitType.COST_PER_DAY: RateLimit(500, 86400),  # $500/day limit
            }
        }

        # Token buckets for services
        self.token_buckets: Dict[str, Dict[RateLimitType, TokenBucket]] = {}
        self.sliding_windows: Dict[str, Dict[RateLimitType, SlidingWindowCounter]] = {}

        # Initialize token buckets and sliding windows
        self._initialize_rate_limiters()

        # Cache settings
        self.cache_ttl = 60  # 1 minute cache

    def _initialize_rate_limiters(self) -> None:
        """Initialize token buckets and sliding windows for all services."""
        for service, limits in self.rate_limits.items():
            self.token_buckets[service] = {}
            self.sliding_windows[service] = {}

            for limit_type, rate_limit in limits.items():
                # Token bucket with burst allowance
                capacity = int(rate_limit.limit * rate_limit.burst_allowance)
                refill_rate = rate_limit.limit / rate_limit.window_seconds

                self.token_buckets[service][limit_type] = TokenBucket(
                    capacity, refill_rate
                )
                self.sliding_windows[service][limit_type] = SlidingWindowCounter(
                    rate_limit.window_seconds
                )

    async def check_rate_limit(
        self,
        service: str,
        operation_type: str,
        estimated_tokens: int = 1,
        estimated_cost: float = 0.0,
        user_id: Optional[str] = None,
    ) -> Tuple[bool, List[RateLimitStatus]]:
        """
        Check if request is within rate limits.

        Returns:
            Tuple of (is_allowed, rate_limit_statuses)
        """
        try:
            if service not in self.rate_limits:
                logger.warning("Unknown service for rate limiting", service=service)
                return True, []

            statuses = []
            is_allowed = True

            # Check each rate limit type
            limits = self.rate_limits[service]

            for limit_type, rate_limit in limits.items():
                # Determine request amount based on limit type
                if limit_type == RateLimitType.REQUESTS_PER_MINUTE:
                    amount = 1
                elif limit_type == RateLimitType.TOKENS_PER_MINUTE:
                    amount = estimated_tokens
                elif limit_type in [
                    RateLimitType.COST_PER_HOUR,
                    RateLimitType.COST_PER_DAY,
                ]:
                    amount = int(estimated_cost * 100)  # Convert to cents for precision
                else:
                    continue

                # Check token bucket
                bucket = self.token_buckets[service][limit_type]
                can_consume = await bucket.consume(amount)

                # Get sliding window count
                window = self.sliding_windows[service][limit_type]
                current_usage = await window.get_count()

                # Calculate window reset time
                reset_time = datetime.now() + timedelta(
                    seconds=rate_limit.window_seconds
                )
                window_remaining = rate_limit.window_seconds

                # Determine if limit is exceeded
                is_exceeded = (
                    not can_consume or current_usage + amount > rate_limit.limit
                )

                status = RateLimitStatus(
                    limit_type=limit_type,
                    current_usage=current_usage,
                    limit=rate_limit.limit,
                    window_remaining_seconds=window_remaining,
                    reset_time=reset_time,
                    is_exceeded=is_exceeded,
                )

                statuses.append(status)

                if is_exceeded:
                    is_allowed = False
                    logger.warning(
                        "Rate limit exceeded",
                        service=service,
                        limit_type=limit_type.value,
                        current_usage=current_usage,
                        limit=rate_limit.limit,
                        user_id=user_id,
                    )

            return is_allowed, statuses

        except Exception as e:
            logger.error("Error checking rate limits", service=service, error=str(e))
            # Fail open - allow request if rate limiting fails
            return True, []

    async def record_usage(
        self,
        service: str,
        operation_type: str,
        tokens_used: int = 1,
        cost: float = 0.0,
        user_id: Optional[str] = None,
        timestamp: Optional[float] = None,
    ) -> None:
        """Record actual API usage for rate limiting."""
        try:
            if service not in self.rate_limits:
                return

            if timestamp is None:
                timestamp = time.time()

            # Record usage in sliding windows
            windows = self.sliding_windows[service]

            await windows[RateLimitType.REQUESTS_PER_MINUTE].add_request(1, timestamp)
            await windows[RateLimitType.TOKENS_PER_MINUTE].add_request(
                tokens_used, timestamp
            )
            await windows[RateLimitType.COST_PER_HOUR].add_request(
                int(cost * 100), timestamp
            )
            await windows[RateLimitType.COST_PER_DAY].add_request(
                int(cost * 100), timestamp
            )

            logger.debug(
                "Recorded API usage",
                service=service,
                operation_type=operation_type,
                tokens=tokens_used,
                cost=cost,
                user_id=user_id,
            )

        except Exception as e:
            logger.error("Error recording API usage", service=service, error=str(e))

    async def get_usage_stats(
        self, db: AsyncSession, service: str, period_hours: int = 24
    ) -> Dict[str, any]:
        """Get usage statistics for a service over a time period."""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=period_hours)

            # Get usage from database
            query = select(
                func.count(AIUsageTracking.id).label("total_requests"),
                func.sum(AIUsageTracking.total_tokens).label("total_tokens"),
                func.sum(AIUsageTracking.cost_usd).label("total_cost"),
                func.avg(AIUsageTracking.response_time_ms).label("avg_response_time"),
            ).where(
                and_(
                    AIUsageTracking.service_type == service,
                    AIUsageTracking.request_timestamp >= start_time,
                    AIUsageTracking.request_timestamp <= end_time,
                )
            )

            result = await db.execute(query)
            row = result.fetchone()

            # Get current rate limit statuses
            current_statuses = {}
            if service in self.sliding_windows:
                for limit_type, window in self.sliding_windows[service].items():
                    current_count = await window.get_count()
                    limit = self.rate_limits[service][limit_type].limit

                    current_statuses[limit_type.value] = {
                        "current": current_count,
                        "limit": limit,
                        "utilization": current_count / limit if limit > 0 else 0,
                    }

            return {
                "service": service,
                "period_hours": period_hours,
                "total_requests": row.total_requests or 0,
                "total_tokens": row.total_tokens or 0,
                "total_cost": float(row.total_cost or 0),
                "avg_response_time_ms": float(row.avg_response_time or 0),
                "current_rate_limits": current_statuses,
                "period_start": start_time.isoformat(),
                "period_end": end_time.isoformat(),
            }

        except Exception as e:
            logger.error("Error getting usage stats", service=service, error=str(e))
            return {"service": service, "period_hours": period_hours, "error": str(e)}

    async def get_cost_optimization_recommendations(
        self, db: AsyncSession, service: str = "openai"
    ) -> List[Dict[str, any]]:
        """Generate cost optimization recommendations based on usage patterns."""
        try:
            recommendations = []

            # Analyze usage patterns from last 7 days
            end_time = datetime.now()
            start_time = end_time - timedelta(days=7)

            # Get usage by operation type
            operation_query = (
                select(
                    AIUsageTracking.operation_type,
                    func.count(AIUsageTracking.id).label("requests"),
                    func.sum(AIUsageTracking.total_tokens).label("tokens"),
                    func.sum(AIUsageTracking.cost_usd).label("cost"),
                    func.avg(AIUsageTracking.total_tokens).label(
                        "avg_tokens_per_request"
                    ),
                )
                .where(
                    and_(
                        AIUsageTracking.service_type == service,
                        AIUsageTracking.request_timestamp >= start_time,
                    )
                )
                .group_by(AIUsageTracking.operation_type)
            )

            result = await db.execute(operation_query)
            operations = result.fetchall()

            # Analyze each operation type
            total_cost = sum(op.cost or 0 for op in operations)

            for op in operations:
                if not op.cost:
                    continue

                op_cost = float(op.cost)
                cost_percentage = (op_cost / total_cost) * 100 if total_cost > 0 else 0

                # High cost operations
                if cost_percentage > 30:
                    recommendations.append(
                        {
                            "type": "high_cost_operation",
                            "priority": "high",
                            "operation": op.operation_type,
                            "cost_percentage": cost_percentage,
                            "description": f"{op.operation_type} represents {cost_percentage:.1f}% of total costs",
                            "recommendation": "Consider implementing caching or batch processing for this operation",
                        }
                    )

                # Inefficient token usage
                avg_tokens = float(op.avg_tokens_per_request or 0)
                if avg_tokens > 2000:
                    recommendations.append(
                        {
                            "type": "high_token_usage",
                            "priority": "medium",
                            "operation": op.operation_type,
                            "avg_tokens": avg_tokens,
                            "description": f"Average {avg_tokens:.0f} tokens per request",
                            "recommendation": "Consider chunking inputs or using more efficient prompts",
                        }
                    )

            # Check daily cost trends
            daily_cost_query = (
                select(
                    func.date(AIUsageTracking.request_timestamp).label("date"),
                    func.sum(AIUsageTracking.cost_usd).label("daily_cost"),
                )
                .where(
                    and_(
                        AIUsageTracking.service_type == service,
                        AIUsageTracking.request_timestamp >= start_time,
                    )
                )
                .group_by(func.date(AIUsageTracking.request_timestamp))
                .order_by("date")
            )

            daily_result = await db.execute(daily_cost_query)
            daily_costs = [
                float(row.daily_cost or 0) for row in daily_result.fetchall()
            ]

            if len(daily_costs) >= 3:
                recent_avg = sum(daily_costs[-3:]) / 3
                older_avg = (
                    sum(daily_costs[:-3]) / len(daily_costs[:-3])
                    if len(daily_costs) > 3
                    else recent_avg
                )

                if recent_avg > older_avg * 1.5:
                    recommendations.append(
                        {
                            "type": "cost_trend_increase",
                            "priority": "high",
                            "recent_avg_daily_cost": recent_avg,
                            "previous_avg_daily_cost": older_avg,
                            "increase_percentage": (
                                (recent_avg - older_avg) / older_avg
                            )
                            * 100,
                            "description": f"Daily costs increased by {((recent_avg - older_avg) / older_avg) * 100:.1f}%",
                            "recommendation": "Review recent changes and implement cost monitoring alerts",
                        }
                    )

            # Current rate limit utilization
            current_stats = await self.get_usage_stats(db, service, 1)  # Last hour
            rate_limits = current_stats.get("current_rate_limits", {})

            for limit_type, status in rate_limits.items():
                utilization = status.get("utilization", 0)
                if utilization > 0.8:
                    recommendations.append(
                        {
                            "type": "high_rate_limit_utilization",
                            "priority": "medium",
                            "limit_type": limit_type,
                            "utilization": utilization,
                            "description": f"{limit_type} at {utilization:.1%} capacity",
                            "recommendation": "Consider implementing request queuing or load balancing",
                        }
                    )

            logger.info(
                "Generated cost optimization recommendations",
                service=service,
                recommendations_count=len(recommendations),
            )

            return recommendations

        except Exception as e:
            logger.error(
                "Error generating cost optimization recommendations",
                service=service,
                error=str(e),
            )
            return []

    async def update_rate_limits(
        self, service: str, new_limits: Dict[RateLimitType, RateLimit]
    ) -> bool:
        """Update rate limits for a service."""
        try:
            if service not in self.rate_limits:
                self.rate_limits[service] = {}

            # Update limits
            for limit_type, rate_limit in new_limits.items():
                self.rate_limits[service][limit_type] = rate_limit

                # Recreate token bucket with new limits
                capacity = int(rate_limit.limit * rate_limit.burst_allowance)
                refill_rate = rate_limit.limit / rate_limit.window_seconds

                self.token_buckets[service][limit_type] = TokenBucket(
                    capacity, refill_rate
                )

            logger.info("Updated rate limits", service=service, limits=new_limits)
            return True

        except Exception as e:
            logger.error("Error updating rate limits", service=service, error=str(e))
            return False

    async def get_recommended_delay(self, service: str, operation_type: str) -> float:
        """Get recommended delay before next request to avoid rate limits."""
        try:
            if service not in self.token_buckets:
                return 0.0

            # Check token bucket status
            max_delay = 0.0

            for limit_type, bucket in self.token_buckets[service].items():
                status = await bucket.get_status()
                if status["current_tokens"] < 1:
                    # Calculate delay needed to get at least 1 token
                    delay = (1 - status["current_tokens"]) / status["fill_rate"]
                    max_delay = max(max_delay, delay)

            return min(max_delay, 60.0)  # Cap at 60 seconds

        except Exception as e:
            logger.error(
                "Error calculating recommended delay", service=service, error=str(e)
            )
            return 0.0


# Global instance
rate_limiting_service = RateLimitingService()
