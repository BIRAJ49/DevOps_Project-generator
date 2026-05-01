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

    def allow(
        self,
        key: str,
        limit: int,
        window_seconds: int,
        max_buckets: int,
    ) -> bool:
        now = monotonic()
        cutoff = now - window_seconds
        bucket_limit = max(max_buckets, 1)

        with self._lock:
            bucket = self._requests.get(key)
            if bucket is None:
                self._evict_expired(cutoff)
                if len(self._requests) >= bucket_limit:
                    self._requests.pop(next(iter(self._requests)))
                bucket = deque()
                self._requests[key] = bucket

            while bucket and bucket[0] <= cutoff:
                bucket.popleft()

            if len(bucket) >= limit:
                return False

            bucket.append(now)
            return True

    def _evict_expired(self, cutoff: float) -> None:
        empty_keys = []
        for key, bucket in self._requests.items():
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if not bucket:
                empty_keys.append(key)

        for key in empty_keys:
            self._requests.pop(key, None)


rate_limiter = SlidingWindowRateLimiter()


def rate_limit(
    bucket_name: str,
    limit: int,
    window_seconds: int,
    max_buckets: int = 10000,
) -> Callable:
    async def dependency(request: Request) -> None:
        client_ip = extract_client_ip(request)
        key = f"{bucket_name}:{client_ip}"

        if not rate_limiter.allow(key, limit, window_seconds, max_buckets):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
            )

    return dependency
