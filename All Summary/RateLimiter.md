# Rate Limiter — Low-Level Design (LLD)

## 1. Requirements (5 minutes)

### Functional Requirements

1. Load rate-limiting configurations at startup.
2. Receive requests containing `clientId` and `endpoint`.
3. Support different rate-limiting algorithms for different endpoints.
4. Configure algorithm-specific parameters, such as token capacity and refill rate.
5. Allow or reject requests based on the client's quota.
6. Return a structured result containing:
   - `allowed`: whether the request is permitted.
   - `remaining`: number of requests remaining.
   - `retryAfterMs`: time until retry, or `null` when allowed.
7. Use a default limiter when an endpoint has no specific configuration.

### Constraints and Out of Scope

- Single-process, in-memory implementation.
- Configuration is loaded once at startup.
- Distributed rate limiting is out of scope.
- Dynamic configuration updates are out of scope.
- Metrics and monitoring are out of scope.
- Advanced configuration validation is out of scope.
- Thread safety can be discussed as an extension.

### Example Configuration

```json
{
  "endpoint": "/search",
  "algorithm": "TokenBucket",
  "algoConfig": {
    "capacity": 1000,
    "refillRatePerSecond": 10
  }
}
```

This configuration allows a burst of up to 1,000 requests and replenishes tokens at 10 per second.

## 2. Core Entities and Relationships

| Entity | Responsibility | Representation |
|---|---|---|
| `RateLimiter` | Entry point; selects the correct limiter and handles fallback | Class |
| `Limiter` | Contract implemented by all rate-limiting algorithms | Interface |
| `LimiterFactory` | Creates the correct algorithm from configuration | Class |
| `RateLimitResult` | Returns the decision and quota metadata | Immutable value object |
| `TokenBucketLimiter` | Implements the Token Bucket algorithm | Class |
| `TokenBucket` | Tracks tokens and last refill time for one client | Class |
| `SlidingWindowLogLimiter` | Implements the Sliding Window Log algorithm | Class |
| `RequestLog` | Stores recent request timestamps for one client | Class |

`Request`, `Client`, and `Endpoint` do not need dedicated classes in this design. The request provides strings for `clientId` and `endpoint`; these values are used as keys.

### Key Relationships

```text
RateLimiter
    ├── Map<Endpoint, Limiter>
    ├── defaultLimiter: Limiter
    └── LimiterFactory
             │
             ├── creates TokenBucketLimiter
             │       └── Map<ClientId, TokenBucket>
             │
             └── creates SlidingWindowLogLimiter
                     └── Map<ClientId, RequestLog>

Limiter (interface)
    ├── TokenBucketLimiter
    └── SlidingWindowLogLimiter

RateLimitResult
    ├── allowed: boolean
    ├── remaining: int
    └── retryAfterMs: long | null
```

**Key design decision:** Each algorithm manages its own per-client state because different algorithms require different data structures.

## 3. Class Design

### 3.1 `RateLimiter` — Orchestrator

**Purpose:** Provides the public entry point and delegates each request to the appropriate algorithm.

**State**

```text
- limiters: Map<String, Limiter>
- defaultLimiter: Limiter
```

**Methods**

```text
+ RateLimiter(configs, defaultConfig)
+ allow(clientId: String, endpoint: String): RateLimitResult
```

**Responsibilities**
- Builds the endpoint-to-limiter map during construction.
- Uses `LimiterFactory` to create each configured limiter.
- Looks up the limiter for an incoming endpoint.
- Uses `defaultLimiter` if no endpoint-specific configuration exists.
- Delegates the rate-limit decision to `Limiter.allow(clientId)`.

**Why a map?**

A map provides average \(O(1)\) lookup for the endpoint's limiter.

**Concepts:** Encapsulation, orchestration, composition, separation of concerns.

### 3.2 `LimiterFactory` — Object Creation

**Purpose:** Creates the correct rate-limiting algorithm from heterogeneous configuration data.

**Methods**

```text
+ create(configData): Limiter
```

**Responsibilities**
- Reads the `algorithm` field.
- Extracts algorithm-specific values from `algoConfig`.
- Constructs the appropriate implementation.
- Rejects unknown algorithm names.

Example:

```text
create(config):
    algorithm = config["algorithm"]
    algoConfig = config["algoConfig"]

    switch algorithm:
        case "TokenBucket":
            return TokenBucketLimiter(
                algoConfig["capacity"],
                algoConfig["refillRatePerSecond"]
            )

        case "SlidingWindowLog":
            return SlidingWindowLogLimiter(
                algoConfig["maxRequests"],
                algoConfig["windowMs"]
            )

        default:
            throw UnknownAlgorithmException
```

**Why a factory?**

Without a factory, the algorithm-selection logic would be spread across the codebase. The factory centralizes construction in one place.

**Concepts:** Factory Pattern, encapsulation, separation of object creation from usage.

### 3.3 `Limiter` — Common Interface

**Purpose:** Defines a consistent contract for every rate-limiting algorithm.

```text
interface Limiter:
    + allow(key: String): RateLimitResult
```

Each implementation decides whether a request is allowed and manages its own per-client state.

**Why an interface instead of an abstract class?**

Different algorithms have fundamentally different state:

- Token Bucket uses token count and refill timestamp.
- Sliding Window Log uses a queue of request timestamps.
- Fixed Window Counter would use a counter and window start time.

There is no meaningful shared state or implementation that all algorithms need to inherit.

**Concepts:** Abstraction, polymorphism, Open/Closed Principle (OCP), Strategy Pattern.

### 3.4 `RateLimitResult` — Immutable Result

**Purpose:** Returns the rate-limit decision and associated metadata.

**State**

```text
- allowed: boolean
- remaining: int
- retryAfterMs: long | null
```

**Methods**

```text
+ RateLimitResult(allowed, remaining, retryAfterMs)
+ isAllowed(): boolean
+ getRemaining(): int
+ getRetryAfterMs(): long | null
```

**Responsibilities**
- Communicates whether the request is allowed.
- Reports remaining quota.
- Reports retry delay when denied.
- Remains immutable after construction.

`retryAfterMs` is `null` when a request is allowed and contains the retry delay in milliseconds when denied.

**Concepts:** Encapsulation, immutability, value object, explicit return type.

## 4. Final Class Design

```text
class RateLimiter:
    - limiters: Map<String, Limiter>
    - defaultLimiter: Limiter

    + RateLimiter(configs, defaultConfig)
    + allow(clientId, endpoint): RateLimitResult


class LimiterFactory:
    + create(configData): Limiter


interface Limiter:
    + allow(key): RateLimitResult


class RateLimitResult:
    - allowed: boolean
    - remaining: int
    - retryAfterMs: long | null

    + isAllowed(): boolean
    + getRemaining(): int
    + getRetryAfterMs(): long | null


class TokenBucketLimiter implements Limiter:
    - capacity: int
    - refillRatePerSecond: int
    - buckets: Map<String, TokenBucket>

    + allow(key): RateLimitResult


class TokenBucket:
    - tokens: double
    - lastRefillTime: long


class SlidingWindowLogLimiter implements Limiter:
    - maxRequests: int
    - windowMs: long
    - logs: Map<String, RequestLog>

    + allow(key): RateLimitResult


class RequestLog:
    - timestamps: Queue<long>
```

The design separates **orchestration (`RateLimiter`)**, **object creation (`LimiterFactory`)**, and **algorithm execution (`Limiter` implementations)**.

## 5. Core Workflow

### 5.1 Initialization

1. Receive endpoint configurations and a default configuration.
2. Create a `LimiterFactory`.
3. Iterate through endpoint configurations.
4. Create the correct limiter for each endpoint.
5. Store each limiter in `limiters`.
6. Create and store the default limiter.

The article's design uses eager initialization: all configured limiters are created at startup.

### 5.2 Process a Request

1. Receive `clientId` and `endpoint`.
2. Look up the endpoint's limiter.
3. If no limiter exists, select `defaultLimiter`.
4. Call `limiter.allow(clientId)`.
5. Return the resulting `RateLimitResult`.

The `RateLimiter` does not implement the rate-limiting algorithm itself.

## 6. Rate-Limiting Algorithms

Two algorithms are especially useful to understand for LLD interviews.

### 6.1 Token Bucket

**Idea:** Each client has a bucket containing tokens. Every request consumes one token, and tokens replenish over time.

<box gap={1}>
  <row align="center" gap={2}>
    <box background="surface-secondary" radius="lg" padding={3} flex="1">
      <text weight="medium">Capacity</text>
      <title size="lg">10 tokens</title>
      <text color="secondary" size="sm">Maximum burst</text>
    </box>
    <box background="surface-secondary" radius="lg" padding={3} flex="1">
      <text weight="medium">Refill rate</text>
      <title size="lg">1/sec</title>
      <text color="secondary" size="sm">Long-term rate</text>
    </box>
  </row>
</box>

**State**

```text
TokenBucketLimiter:
    - capacity: int
    - refillRatePerSecond: int
    - buckets: Map<ClientId, TokenBucket>

TokenBucket:
    - tokens: double
    - lastRefillTime: long
```

**Why these fields?**
- `capacity`: Maximum number of tokens.
- `refillRatePerSecond`: Number of tokens replenished per second.
- `buckets`: Maintains independent state for each client.
- `tokens`: Current available token balance.
- `lastRefillTime`: Allows refill to be calculated on demand.

No background refill thread is required. Tokens are recalculated when a request arrives.

**Algorithm**

```text
allow(clientId):
    bucket = getOrCreateBucket(clientId)

    now = currentTimeMillis()
    elapsed = now - bucket.lastRefillTime

    tokensToAdd = elapsed * refillRatePerSecond / 1000.0

    bucket.tokens = min(capacity, bucket.tokens + tokensToAdd)
    bucket.lastRefillTime = now

    if bucket.tokens >= 1:
        bucket.tokens -= 1

        return RateLimitResult(
            allowed = true,
            remaining = floor(bucket.tokens),
            retryAfterMs = null
        )

    tokensNeeded = 1 - bucket.tokens
    retryAfterMs = ceil(tokensNeeded * 1000 / refillRatePerSecond)

    return RateLimitResult(
        allowed = false,
        remaining = 0,
        retryAfterMs = retryAfterMs
    )
```

**Important details**
- A new client's bucket starts full.
- Tokens are capped at `capacity`.
- Fractional tokens support accurate refill calculations.
- A denied request does not consume a token.
- Retry delay is rounded up so the client is not told to retry too early.

**Advantages**
- Allows short bursts.
- Smoothly replenishes capacity.
- Stores only a small amount of state per client.

**Trade-off:** It does not enforce an exact maximum number of requests in every arbitrary rolling window.

### 6.2 Sliding Window Log

**Idea:** Store the timestamp of each accepted request. Remove timestamps outside the current window, then count the remaining requests.

**State**

```text
SlidingWindowLogLimiter:
    - maxRequests: int
    - windowMs: long
    - logs: Map<ClientId, RequestLog>

RequestLog:
    - timestamps: Queue<long>
```

**Why a queue?**

Request timestamps are ordered chronologically. Old timestamps are removed from the front and new timestamps are added to the back, making a queue a natural fit.

**Algorithm**

```text
allow(clientId):
    log = getOrCreateLog(clientId)

    now = currentTimeMillis()
    cutoff = now - windowMs

    while log.timestamps is not empty
          and log.timestamps.peek() < cutoff:
        log.timestamps.poll()

    if log.timestamps.size() < maxRequests:
        log.timestamps.add(now)

        return RateLimitResult(
            allowed = true,
            remaining = maxRequests - log.timestamps.size(),
            retryAfterMs = null
        )

    oldestTimestamp = log.timestamps.peek()
    retryAfterMs = oldestTimestamp + windowMs - now

    return RateLimitResult(
        allowed = false,
        remaining = 0,
        retryAfterMs = retryAfterMs
    )
```

**Important details**
- Remove stale timestamps before checking the limit.
- Count only requests inside the current window.
- Add the timestamp only when the request is allowed.
- When denied, the oldest timestamp determines when capacity becomes available.

**Advantages**
- Accurate rolling-window enforcement.
- No fixed-window boundary burst problem.

**Trade-off:** Stores timestamps for accepted requests, so memory usage grows with request volume.

### 6.3 Algorithm Comparison

| Algorithm | Per-client state | Advantage | Trade-off |
|---|---|---|---|
| Token Bucket | Token count, refill timestamp | Supports bursts with smooth refill | Does not impose an exact rolling-window count |
| Sliding Window Log | Queue of timestamps | Accurate rolling-window limit | Higher memory consumption |
| Fixed Window Counter | Counter, window start | Simple and memory-efficient | Boundary bursts are possible |
| Sliding Window Counter | Current and previous counts, window start | Balances accuracy and memory | Approximate rather than exact |

**Interview recommendation:** Implement one algorithm thoroughly first. Token Bucket is a good starting point; add Sliding Window Log if time allows.

## 7. OOP Principles and Design Patterns

### OOP Principles

| Principle | Application |
|---|---|
| **Encapsulation** | Each limiter owns its algorithm configuration and per-client state. |
| **Abstraction** | The `Limiter` interface exposes only `allow(key)`. |
| **Polymorphism** | `RateLimiter` can invoke `allow()` without knowing the concrete algorithm. |
| **Single Responsibility Principle (SRP)** | The orchestrator, factory, result type, and algorithm implementations have distinct responsibilities. |
| **Open/Closed Principle (OCP)** | New algorithms can implement `Limiter` without changing the orchestrator. |
| **Immutability** | `RateLimitResult` does not change after construction. |

### Design Patterns

**1. Strategy Pattern**

Each rate-limiting algorithm is a strategy behind the common `Limiter` interface. `RateLimiter` delegates the decision to the selected implementation.

**2. Factory Pattern**

`LimiterFactory` reads the algorithm type from configuration and creates the corresponding concrete limiter.

**How they work together:**

- Factory chooses which algorithm object to create.
- Strategy defines how the selected algorithm makes decisions.
- Orchestrator routes requests without embedding algorithm-specific logic.

A registry-based factory could replace the switch statement if algorithms needed to be registered dynamically, but a switch is simpler for a small fixed set of algorithms.

## 8. Concurrency and Thread Safety

The basic design assumes single-process, in-memory operation and leaves concurrency out of the initial implementation. If multiple threads call the same limiter, state updates must be made atomic.

### The Race Condition

Suppose a Token Bucket has one token remaining:

```text
Thread A reads tokens = 1
Thread B reads tokens = 1
Thread A allows request and decrements
Thread B allows request and decrements
```

Both requests may be allowed even though only one token was available.

### Solution: Per-Client Locking

Use a thread-safe map for bucket creation, then synchronize on the individual bucket while refilling, checking, and consuming tokens.

```text
allow(clientId):
    bucket = buckets.computeIfAbsent(
        clientId,
        createFullBucket
    )

    synchronized(bucket):
        refillTokens(bucket)

        if bucket.tokens >= 1:
            bucket.tokens -= 1
            return allowedResult()

        return deniedResult()
```

**Why lock per client?**

- Requests from the same client must coordinate.
- Different clients can be processed concurrently.
- A single global lock would unnecessarily serialize all requests.

The same principle applies to Sliding Window Log: removing stale timestamps, checking the count, and inserting a timestamp must be atomic for each client.

## 9. Edge Cases

- Unknown endpoint: use the default limiter.
- Unknown algorithm in configuration: fail fast with a clear error.
- Empty or invalid configuration: validate according to the agreed scope.
- Client with no previous state: initialize a full token bucket or an empty request log.
- Token bucket at capacity: never exceed the configured capacity.
- Token bucket with insufficient tokens: deny without consuming a token.
- Sliding window with stale timestamps: remove them before checking the limit.
- Sliding window at capacity: calculate retry time from the oldest timestamp.
- Very long elapsed time: cap refill at capacity.
- Invalid configuration such as zero or negative refill rate: reject it during configuration validation.
- Concurrent requests for the same client: protect state updates with a per-client lock.
- Many unique client IDs: prevent unbounded memory growth with eviction or TTL policies.

**Implementation detail:** For Token Bucket, use floating-point division for refill calculations. Integer division can discard fractional tokens and produce incorrect refill behavior.

## 10. Complexity Analysis

Let:
- \(E\) = number of configured endpoints.
- \(C\) = number of distinct clients tracked by a limiter.
- \(W\) = number of timestamps currently stored for one client.

| Operation | Complexity | Explanation |
|---|---|---|
| Initialize endpoint limiters | \(O(E)\) | Create one limiter per endpoint configuration |
| Find limiter for endpoint | Average \(O(1)\) | Hash-map lookup |
| Token Bucket request | Average \(O(1)\) | One client's bucket update |
| Sliding Window Log request | Amortized \(O(1)\) per timestamp processed | Each timestamp is inserted once and removed once |
| Store per-client state | \(O(C)\) for Token Bucket | One bucket per client |
| Sliding Window Log storage | \(O(W_{\text{total}})\) | Stores accepted request timestamps across clients |

Sliding Window Log cleanup can take \(O(W)\) in one call if many stale timestamps accumulate. Across the timestamps processed, each is added and removed at most once, giving amortized constant cleanup work per timestamp.

## 11. Extensions and Trade-offs

### 11.1 Adding a New Algorithm

For example, to add `FixedWindowCounterLimiter`:

1. Implement the `Limiter` interface.
2. Define the algorithm-specific configuration and state.
3. Implement `allow(key)`.
4. Add a factory case to construct it.

`RateLimiter` does not need to change.

### 11.2 Dynamic Configuration Updates

The initial design loads configuration once at startup. To support updates, the system needs a policy for replacing or updating limiter instances while requests are in progress.

Important questions:
- Should existing client state be preserved?
- What happens if the algorithm changes?
- How are concurrent requests coordinated with configuration updates?

The right choice depends on whether updates should preserve quota state or reset it.

### 11.3 Memory Management

The per-client maps can grow indefinitely as new clients arrive.

Possible solutions:
- Track last-access timestamps and evict inactive clients.
- Use a bounded LRU cache.
- Apply TTL-based expiration in a distributed implementation.

Eviction resets the client's tracked state; when that client returns, it may receive a fresh quota. This behavior should be an explicit trade-off.

### 11.4 Distributed Rate Limiting

A local in-memory limiter tracks requests only within one process. If traffic is spread across multiple servers, each server may independently allow requests and exceed the intended global limit.

A distributed design requires shared coordination or state, such as a centralized store and atomic updates. This is outside the scope of the current LLD.

## 12. Recommended Interview Flow

1. **Clarify requirements:** Inputs, return type, default configuration, algorithms, and deployment scope.
2. **Identify entities:** `RateLimiter`, `Limiter`, `LimiterFactory`, and `RateLimitResult`.
3. **Define the interface:** `allow(key)` is the common algorithm contract.
4. **Design the factory:** Convert heterogeneous configuration into concrete limiter instances.
5. **Implement orchestration:** Select endpoint-specific or default limiter.
6. **Implement one algorithm:** Prefer Token Bucket first.
7. **Explain state:** Configuration is shared by the limiter; quota state is per client.
8. **Test edge cases:** Exhausted quota, refill, stale timestamps, unknown endpoint, and invalid algorithm.
9. **Discuss concurrency:** Per-client locking and atomic state updates.
10. **Discuss extensions:** New algorithms, eviction, dynamic configuration, and distributed coordination.

## Key Takeaway

The central design decision is to separate **request routing, algorithm creation, and rate-limiting behavior**.

- `RateLimiter` routes requests.
- `LimiterFactory` creates the correct implementation.
- `Limiter` provides the common contract.
- Each concrete limiter manages its own per-client state.
- `RateLimitResult` returns a consistent decision and retry metadata.

The **Factory Pattern** handles object creation, while the **Strategy Pattern** makes rate-limiting algorithms interchangeable.
