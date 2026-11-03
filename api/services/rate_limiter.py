import time
from collections import defaultdict
from fastapi import HTTPException, Request, status

from ytrag.config import settings


class InMemoryRateLimiter:
    """Sliding-window in-memory rate limiter per client IP address.
    
    Note on scaling: This in-memory limiter tracks requests per process worker.
    For multi-worker or distributed deployments across multiple containers,
    a shared Redis store would be used.
    """

    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # client_ip -> list of timestamps
        self.requests: dict[str, list[float]] = defaultdict(list)

    def check(self, request: Request) -> None:
        """Verify that the client IP has not exceeded the request rate limit."""
        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()
        window_start = now - self.window_seconds

        # Clean old timestamps outside sliding window
        self.requests[client_ip] = [
            ts for ts in self.requests[client_ip] if ts > window_start
        ]

        if len(self.requests[client_ip]) >= self.max_requests:
            retry_after = int(self.window_seconds - (now - self.requests[client_ip][0]))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: maximum {self.max_requests} requests per {self.window_seconds}s.",
                headers={"Retry-After": str(max(1, retry_after))},
            )

        # Record this request
        self.requests[client_ip].append(now)


# Global rate limiter instance using configured settings
ask_rate_limiter = InMemoryRateLimiter(
    max_requests=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window,
)
