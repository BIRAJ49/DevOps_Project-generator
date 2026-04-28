from collections import defaultdict, deque
from collections.abc import Callable
from threading import Lock
from time import monotonic

from fastapi import HTTPException, Request, status

from backend.utils.request import extract_client_ip


class SlidingWindowRateLimiter:
    def __init__(self) -> None:
        self._lock = Lock()
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        now = monotonic()
        cutoff = now - window_seconds

        with self._lock:
            bucket = self._requests[key]
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()

            if len(bucket) >= limit:
                return False

            bucket.append(now)
            return True


rate_limiter = SlidingWindowRateLimiter()


def rate_limit(bucket_name: str, limit: int, window_seconds: int) -> Callable:
    async def dependency(request: Request) -> None:
        client_ip = extract_client_ip(request)
        key = f"{bucket_name}:{client_ip}"

        if not rate_limiter.allow(key, limit, window_seconds):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
            )

    return dependency

