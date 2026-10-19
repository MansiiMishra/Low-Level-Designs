from abc import ABC, abstractmethod

# this abstract class acts as a contract for the limiter algorithms.
# here it says, no matter the algo we need to implement the allow method, which takes a key and returns a RateLimitResult.

class Limiter(ABC):
    @abstractmethod
    def allow(self, key: str):
        pass
