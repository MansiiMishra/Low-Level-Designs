from TokenBucketLimiter import TokenBucketLimiter
from SlidingWindowLogLimiter import SlidingWindowLogLimiter

class LimiterFactory:
    def create(self, config: dict):
        algorithm = config.get("algorithm")
        algo_config = config.get("algoConfig", {})

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
