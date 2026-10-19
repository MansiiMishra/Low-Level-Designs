from TokenBucketLimiter import TokenBucketLimiter
from SlidingWindowLogLimiter import SlidingWindowLogLimiter


# when there are multiple types of similar task. they can be groups as factory.
# the factory allows to create a constructor based on the current input at runtime. 
# This is called factory design pattern

class LimiterFactory:
    def create(self, config: dict):
        algorithm = config.get("algorithm")
        algo_config = config.get("algoConfig", {})

        # the config is the enpoint input that the ratelimiter gets and passes to the limiterfactory to create a custom constructor.
        # this further calls the specific limiter constructor based on the algortiem type extracted from the config.
        if algorithm == "TokenBucket":
            return TokenBucketLimiter(
                algo_config.get("capacity", 0),
                algo_config.get("refillRatePerSecond", 0),
            )
        if algorithm == "SlidingWindowLog":
            return SlidingWindowLogLimiter(
                algo_config.get("maxRequests", 0),
                algo_config.get("windowMs", 0),
            )

        raise ValueError(f"Unknown algorithm: {algorithm}")
