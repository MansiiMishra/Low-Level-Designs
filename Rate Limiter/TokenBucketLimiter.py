import time
from typing import Dict
from RateLimitResult import RateLimitResult
from Limiter import Limiter

class TokenBucketLimiter(Limiter):
    def __init__(self, capacity: int, refill_rate_per_second: int):
        self._capacity = capacity
        self._refill_rate_per_second = refill_rate_per_second
        self._buckets: Dict[str, TokenBucket] = {}

    def allow(self, key: str):
        bucket = self._get_or_create_bucket(key)

        now = int(time.time() * 1000)
        elapsed = now - bucket.last_refill_time
        tokens_to_add = (elapsed * self._refill_rate_per_second) / 1000
        bucket.tokens = min(self._capacity, bucket.tokens + tokens_to_add)
        bucket.last_refill_time = now

        if bucket.tokens >= 1:
            bucket.tokens -= 1
            remaining = int(bucket.tokens)
            return RateLimitResult(True, remaining, None)

        tokens_needed = 1 - bucket.tokens
        retry_after_ms = int((tokens_needed * 1000) / self._refill_rate_per_second + 0.999)
        return RateLimitResult(False, 0, retry_after_ms)

    def _get_or_create_bucket(self, key: str):
        if key not in self._buckets:
            self._buckets[key] = TokenBucket(self._capacity, int(time.time() * 1000))
        return self._buckets[key]


class TokenBucket:
    def __init__(self, tokens: float, last_refill_time: int):
        self.tokens = tokens
        self.last_refill_time = last_refill_time
