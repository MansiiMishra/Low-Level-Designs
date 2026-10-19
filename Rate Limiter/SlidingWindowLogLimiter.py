import time
from collections import deque
from typing import Dict
from RateLimitResult import RateLimitResult
from Limiter import Limiter

# this uses a queue, FIFO.
# the log is used to look at the previous timestamps. the remaining time is calacuted on the bases of the oldest timestamp in the queue. 
# if the queue is full, then we can calculate the remaining time by looking at the oldest timestamp and subtracting it from the current time.
class SlidingWindowLogLimiter(Limiter):
    def __init__(self, max_requests: int, window_ms: int):
        self._max_requests = max_requests
        self._window_ms = window_ms
        self._logs: Dict[str, RequestLog] = {}

    def allow(self, key: str):
        log = self._get_or_create_log(key)

        now = int(time.time() * 1000)
        cutoff = now - self._window_ms

        while log.timestamps and log.timestamps[0] < cutoff:
            log.timestamps.popleft()

        if len(log.timestamps) < self._max_requests:
            log.timestamps.append(now)
            remaining = self._max_requests - len(log.timestamps)
            return RateLimitResult(True, remaining, None)

        oldest_timestamp = log.timestamps[0]
        retry_after_ms = (oldest_timestamp + self._window_ms) - now
        return RateLimitResult(False, 0, retry_after_ms)

    def _get_or_create_log(self, key: str):
        if key not in self._logs:
            self._logs[key] = RequestLog(deque())
        return self._logs[key]


class RequestLog:
    def __init__(self, timestamps: deque):
        self.timestamps = timestamps
