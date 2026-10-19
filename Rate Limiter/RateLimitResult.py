from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    remaining: int
    retry_after_ms: Optional[int]

    # no additional cuntionaly, only takes the values from the limiter algorithm and returns it to the RateLimiter class.

    def is_allowed(self) -> bool:
        return self.allowed

    def get_remaining(self) -> int:
        return self.remaining

    def get_retry_after_ms(self) -> Optional[int]:
        return self.retry_after_ms
