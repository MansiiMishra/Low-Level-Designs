from typing import Dict, List
from LimiterFactory import LimiterFactory
from Limiter import Limiter
class RateLimiter:
    def __init__(self, configs: List[dict], default_config: dict):
        factory = LimiterFactory()
        self._limiters: Dict[str, Limiter] = {}

        for config in configs:
            endpoint = config.get("endpoint")
            if endpoint is None:
                continue
            limiter = factory.create(config)
            self._limiters[endpoint] = limiter

        self._default_limiter = factory.create(default_config)

    def allow(self, client_id: str, endpoint: str):
        limiter = self._limiters.get(endpoint, self._default_limiter)
        return limiter.allow(client_id)
