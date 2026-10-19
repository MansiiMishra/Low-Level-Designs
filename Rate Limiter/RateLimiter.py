from typing import Dict, List
from LimiterFactory import LimiterFactory
from Limiter import Limiter
class RateLimiter:
    def __init__(self, configs: List[dict], default_config: dict):
        factory = LimiterFactory()
        self._limiters: Dict[str, Limiter] = {}

        # use the factory to fetch the endpoint, once we have the endpoint, we can create the limiter.
        for config in configs:
            endpoint = config.get("endpoint")
            if endpoint is None:
                continue

            # this calls the factory.
            # but if the factory is unable to create, it throws an error, where is that error consumed?
            limiter = factory.create(config)
            self._limiters[endpoint] = limiter

        # what is the default limiter here?
        self._default_limiter = factory.create(default_config)

    # can this allow method be renamed? this seems confusing to me
    def allow(self, client_id: str, endpoint: str):
        limiter = self._limiters.get(endpoint, self._default_limiter)
        return limiter.allow(client_id)
