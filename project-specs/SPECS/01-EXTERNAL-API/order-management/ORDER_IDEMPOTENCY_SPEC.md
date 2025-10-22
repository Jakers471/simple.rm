# Order Idempotency Specification

**doc_id:** ORDER-004
**version:** 1.0
**status:** DRAFT
**addresses:** GAP-API-SCENARIO-001 (CRITICAL) - Idempotency component
**created:** 2025-10-22
**category:** Order Management / Idempotency

---

## Overview

This specification defines the idempotency system for order operations to prevent duplicate orders during network failures, retries, and concurrent requests. The system generates unique idempotency keys, maintains an in-memory cache with TTL, and provides duplicate detection for order placement and modification operations.

**Problem Statement:**
- How to prevent duplicate orders during retry attempts?
- How to generate unique but reproducible idempotency keys?
- How long should idempotency keys be cached?
- What happens when cache expires?
- How to handle idempotency across multiple sessions?

**Solution:**
SHA-256 based idempotency key generation using order characteristics, in-memory cache with 1-hour TTL, distributed cache support for multi-instance deployments, and clear cache cleanup strategies.

---

## Requirements

### Functional Requirements

**FR-001: Idempotency Key Generation**
- MUST generate deterministic keys from order characteristics
- MUST use cryptographic hash (SHA-256) for uniqueness
- MUST include account, symbol, side, quantity, and timestamp
- MUST produce same key for identical order requests within time window
- MUST produce different keys for different orders

**FR-002: Duplicate Request Detection**
- MUST detect duplicate order placement requests
- MUST detect duplicate order modification requests
- MUST detect duplicate position close requests
- MUST return cached result for duplicate requests
- MUST prevent API call for confirmed duplicates

**FR-003: Idempotency Cache Management**
- MUST cache idempotency keys with associated order IDs
- MUST implement TTL (default 1 hour)
- MUST cleanup expired entries automatically
- MUST support distributed cache for multi-instance deployments
- MUST handle cache eviction gracefully

**FR-004: Cache Expiration Handling**
- MUST allow retry after cache expiration
- MUST log when expired keys are reused
- MUST distinguish between duplicate and retry-after-expiry
- MUST emit metrics for cache expiration events

**FR-005: Cross-Session Idempotency**
- MUST work across multiple user sessions
- MUST work across multiple application instances
- MUST coordinate via shared cache (Redis/distributed)
- MUST handle cache unavailability gracefully

### Non-Functional Requirements

**NFR-001: Performance**
- Key generation MUST be < 1ms
- Cache lookup MUST be < 1ms
- Cache write MUST be async (non-blocking)
- Cleanup MUST not impact request processing
- Distributed cache latency < 5ms

**NFR-002: Reliability**
- Zero duplicate orders when idempotency enabled
- Cache corruption MUST NOT break order placement
- Cache unavailability MUST NOT prevent orders
- Graceful degradation to stateless mode
- Automatic recovery after cache restoration

**NFR-003: Security**
- Idempotency keys MUST NOT expose sensitive data
- Keys MUST be cryptographically secure
- Cache MUST be isolated per account
- No key prediction possible by external parties

---

## Idempotency Key Generation

### Key Structure

```yaml
IdempotencyKey:
  algorithm: SHA256
  input: concatenated string of order characteristics
  output: 64-character hexadecimal string
  format: lowercase hex
  length: 64 characters (256 bits)

InputComponents:
  - accountId: string
  - symbol: string
  - side: "BUY" | "SELL"
  - quantity: float (8 decimal precision)
  - timestamp: floor(timestamp_ms / resolution_ms)  # Minute resolution by default
  - orderType: "MARKET" | "LIMIT" | "STOP" | "STOP_LIMIT"
  - limitPrice: float | null (optional, for LIMIT orders)
  - stopPrice: float | null (optional, for STOP orders)

TimestampResolution:
  default: 60000  # 1 minute = 60000 milliseconds
  rationale: Same order retried within same minute gets same key
```

### Generation Algorithm

```python
import hashlib
from typing import Optional

def generate_idempotency_key(
    account_id: str,
    symbol: str,
    side: str,  # "BUY" or "SELL"
    quantity: float,
    timestamp_ms: int,
    order_type: str = "MARKET",
    limit_price: Optional[float] = None,
    stop_price: Optional[float] = None,
    timestamp_resolution_ms: int = 60000
) -> str:
    """
    Generate idempotency key for order request.

    Args:
        account_id: Trading account identifier
        symbol: Trading symbol (e.g., "AAPL")
        side: Order side (BUY or SELL)
        quantity: Order quantity
        timestamp_ms: Request timestamp in milliseconds
        order_type: Order type (MARKET, LIMIT, STOP, STOP_LIMIT)
        limit_price: Limit price (for LIMIT orders)
        stop_price: Stop price (for STOP orders)
        timestamp_resolution_ms: Timestamp resolution (default 60000 = 1 minute)

    Returns:
        64-character hex string (SHA-256 hash)
    """
    # 1. Floor timestamp to resolution (minute-level by default)
    timestamp_bucket = timestamp_ms // timestamp_resolution_ms

    # 2. Round quantity to 8 decimals (prevent floating point issues)
    quantity_normalized = round(quantity, 8)

    # 3. Build raw string from components
    raw_components = [
        str(account_id),
        str(symbol).upper(),  # Normalize symbol to uppercase
        str(side).upper(),
        f"{quantity_normalized:.8f}",  # Fixed precision
        str(timestamp_bucket),
        str(order_type).upper()
    ]

    # 4. Add optional price components if present
    if limit_price is not None:
        raw_components.append(f"{round(limit_price, 8):.8f}")

    if stop_price is not None:
        raw_components.append(f"{round(stop_price, 8):.8f}")

    # 5. Concatenate with delimiter
    raw_string = "|".join(raw_components)

    # 6. Generate SHA-256 hash
    hash_object = hashlib.sha256(raw_string.encode('utf-8'))
    idempotency_key = hash_object.hexdigest()

    return idempotency_key


def validate_idempotency_key(key: str) -> bool:
    """
    Validate idempotency key format.

    Args:
        key: Idempotency key to validate

    Returns:
        True if valid format, False otherwise
    """
    # Must be 64 character lowercase hex string
    if len(key) != 64:
        return False

    try:
        int(key, 16)  # Valid hex string
        return True
    except ValueError:
        return False
```

### Generation Examples

**Example 1: Market Order**
```yaml
Input:
  accountId: "ACC123456"
  symbol: "AAPL"
  side: "BUY"
  quantity: 100.0
  timestamp: 1729636823456  # 2025-10-22 14:13:43.456
  orderType: "MARKET"

Calculation:
  timestampBucket: floor(1729636823456 / 60000) = 28827280
  quantityNormalized: 100.00000000
  rawString: "ACC123456|AAPL|BUY|100.00000000|28827280|MARKET"
  sha256: "a7f3c9d8e1b2f4a6c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1"

IdempotencyKey: "a7f3c9d8e1b2f4a6c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1"
```

**Example 2: Limit Order**
```yaml
Input:
  accountId: "ACC123456"
  symbol: "AAPL"
  side: "BUY"
  quantity: 100.0
  timestamp: 1729636823456
  orderType: "LIMIT"
  limitPrice: 178.50

Calculation:
  timestampBucket: 28827280
  quantityNormalized: 100.00000000
  limitPriceNormalized: 178.50000000
  rawString: "ACC123456|AAPL|BUY|100.00000000|28827280|LIMIT|178.50000000"
  sha256: "b8e4d9c0f3a5b7d9e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3"

IdempotencyKey: "b8e4d9c0f3a5b7d9e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3"
```

**Example 3: Stop-Limit Order**
```yaml
Input:
  accountId: "ACC123456"
  symbol: "AAPL"
  side: "SELL"
  quantity: 50.0
  timestamp: 1729636843789
  orderType: "STOP_LIMIT"
  stopPrice: 177.50
  limitPrice: 177.00

Calculation:
  timestampBucket: 28827280  # Same minute as previous examples
  quantityNormalized: 50.00000000
  stopPriceNormalized: 177.50000000
  limitPriceNormalized: 177.00000000
  rawString: "ACC123456|AAPL|SELL|50.00000000|28827280|STOP_LIMIT|177.00000000|177.50000000"
  sha256: "c9f5e0d1a4b6c8e0f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4"

IdempotencyKey: "c9f5e0d1a4b6c8e0f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4"
```

### Key Properties

**Determinism:**
- Same order characteristics → Same key
- Minute-level timestamp bucketing ensures retries within same minute get same key

**Uniqueness:**
- Different symbols → Different keys
- Different quantities → Different keys
- Different sides (BUY vs SELL) → Different keys
- Different accounts → Different keys
- Different minutes → Different keys

**Collision Resistance:**
- SHA-256 provides 2^256 possible keys
- Practical collision probability: negligible

---

## Idempotency Cache

### Cache Structure

```python
from dataclasses import dataclass
from typing import Optional, Dict
import time

@dataclass
class IdempotencyCacheEntry:
    """
    Cache entry for idempotency tracking.
    """
    idempotency_key: str
    order_id: Optional[str]  # Null if order placement failed
    order_details: dict       # Full order request details
    request_id: str          # Original request identifier
    created_time: int        # Milliseconds since epoch
    expiry_time: int         # Milliseconds since epoch
    last_accessed: int       # Milliseconds since epoch
    status: str              # "pending" | "submitted" | "completed" | "failed"
    error: Optional[str]     # Error message if failed
    access_count: int        # Number of cache hits


class IdempotencyCache:
    """
    In-memory idempotency cache with TTL and cleanup.
    """
    def __init__(self, ttl_ms: int = 3600000):  # Default 1 hour
        self.cache: Dict[str, IdempotencyCacheEntry] = {}
        self.ttl_ms = ttl_ms
        self.cleanup_interval_ms = 300000  # 5 minutes
        self.start_cleanup_timer()

    def put(
        self,
        idempotency_key: str,
        order_details: dict,
        request_id: str,
        order_id: Optional[str] = None,
        status: str = "pending"
    ) -> IdempotencyCacheEntry:
        """
        Add entry to idempotency cache.
        """
        current_time = self._current_time_ms()

        entry = IdempotencyCacheEntry(
            idempotency_key=idempotency_key,
            order_id=order_id,
            order_details=order_details,
            request_id=request_id,
            created_time=current_time,
            expiry_time=current_time + self.ttl_ms,
            last_accessed=current_time,
            status=status,
            error=None,
            access_count=0
        )

        self.cache[idempotency_key] = entry
        return entry

    def get(self, idempotency_key: str) -> Optional[IdempotencyCacheEntry]:
        """
        Retrieve entry from cache (if not expired).
        """
        if idempotency_key not in self.cache:
            return None

        entry = self.cache[idempotency_key]
        current_time = self._current_time_ms()

        # Check expiration
        if current_time > entry.expiry_time:
            # Expired - remove and return None
            del self.cache[idempotency_key]
            return None

        # Update access tracking
        entry.last_accessed = current_time
        entry.access_count += 1

        return entry

    def update_status(
        self,
        idempotency_key: str,
        status: str,
        order_id: Optional[str] = None,
        error: Optional[str] = None
    ):
        """
        Update status of cached entry.
        """
        if idempotency_key not in self.cache:
            return

        entry = self.cache[idempotency_key]
        entry.status = status

        if order_id:
            entry.order_id = order_id

        if error:
            entry.error = error

    def cleanup_expired(self):
        """
        Remove expired entries from cache.
        """
        current_time = self._current_time_ms()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time > entry.expiry_time
        ]

        for key in expired_keys:
            del self.cache[key]

        return len(expired_keys)

    def start_cleanup_timer(self):
        """
        Start periodic cleanup timer.
        """
        from threading import Timer

        def cleanup_task():
            expired_count = self.cleanup_expired()
            if expired_count > 0:
                log_info(f"Cleaned up {expired_count} expired idempotency entries")

            # Reschedule
            self.start_cleanup_timer()

        timer = Timer(self.cleanup_interval_ms / 1000, cleanup_task)
        timer.daemon = True
        timer.start()

    def _current_time_ms(self) -> int:
        """Get current time in milliseconds."""
        return int(time.time() * 1000)

    def get_stats(self) -> dict:
        """
        Get cache statistics.
        """
        current_time = self._current_time_ms()

        return {
            'total_entries': len(self.cache),
            'active_entries': sum(
                1 for e in self.cache.values()
                if current_time <= e.expiry_time
            ),
            'expired_entries': sum(
                1 for e in self.cache.values()
                if current_time > e.expiry_time
            ),
            'status_breakdown': self._count_by_status(),
            'oldest_entry_age_ms': self._oldest_entry_age(current_time),
            'hit_rate': self._calculate_hit_rate()
        }

    def _count_by_status(self) -> dict:
        """Count entries by status."""
        counts = {}
        for entry in self.cache.values():
            counts[entry.status] = counts.get(entry.status, 0) + 1
        return counts

    def _oldest_entry_age(self, current_time: int) -> Optional[int]:
        """Get age of oldest entry in milliseconds."""
        if not self.cache:
            return None
        oldest = min(self.cache.values(), key=lambda e: e.created_time)
        return current_time - oldest.created_time

    def _calculate_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        if not self.cache:
            return 0.0
        total_accesses = sum(e.access_count for e in self.cache.values())
        return total_accesses / len(self.cache) if self.cache else 0.0
```

---

## Duplicate Detection Workflow

### Order Placement with Idempotency

```python
async def place_order_with_idempotency(
    account_id: str,
    symbol: str,
    side: str,
    quantity: float,
    order_type: str = "MARKET",
    limit_price: Optional[float] = None,
    stop_price: Optional[float] = None
) -> OrderPlacementResult:
    """
    Place order with idempotency protection.
    """
    # 1. Generate idempotency key
    timestamp_ms = get_current_time_ms()
    idempotency_key = generate_idempotency_key(
        account_id=account_id,
        symbol=symbol,
        side=side,
        quantity=quantity,
        timestamp_ms=timestamp_ms,
        order_type=order_type,
        limit_price=limit_price,
        stop_price=stop_price
    )

    # 2. Check cache for duplicate
    cached_entry = idempotency_cache.get(idempotency_key)

    if cached_entry:
        # Duplicate request detected
        log_info(f"Duplicate order detected: {idempotency_key}")

        if cached_entry.status == "completed":
            # Order already placed successfully
            return OrderPlacementResult(
                success=True,
                orderId=cached_entry.order_id,
                status="duplicate_detected",
                message="Order already placed",
                fromCache=True,
                originalRequestId=cached_entry.request_id
            )

        elif cached_entry.status == "pending":
            # Order still being processed
            return OrderPlacementResult(
                success=False,
                status="processing",
                message="Order placement in progress",
                fromCache=True,
                originalRequestId=cached_entry.request_id
            )

        elif cached_entry.status == "failed":
            # Previous attempt failed - allow retry
            log_info("Previous order failed, allowing retry")
            # Fall through to place order

    # 3. Create cache entry (mark as pending)
    request_id = generate_request_id()
    order_details = {
        'account_id': account_id,
        'symbol': symbol,
        'side': side,
        'quantity': quantity,
        'order_type': order_type,
        'limit_price': limit_price,
        'stop_price': stop_price
    }

    idempotency_cache.put(
        idempotency_key=idempotency_key,
        order_details=order_details,
        request_id=request_id,
        status="pending"
    )

    try:
        # 4. Place order via API
        api_result = await api.place_order(
            account_id=account_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=order_type,
            limit_price=limit_price,
            stop_price=stop_price
        )

        # 5. Update cache with success
        idempotency_cache.update_status(
            idempotency_key=idempotency_key,
            status="completed",
            order_id=api_result.orderId
        )

        return OrderPlacementResult(
            success=True,
            orderId=api_result.orderId,
            status="placed",
            message="Order placed successfully",
            fromCache=False,
            requestId=request_id
        )

    except Exception as e:
        # 6. Update cache with failure
        idempotency_cache.update_status(
            idempotency_key=idempotency_key,
            status="failed",
            error=str(e)
        )

        return OrderPlacementResult(
            success=False,
            status="failed",
            message=f"Order placement failed: {e}",
            fromCache=False,
            requestId=request_id
        )
```

### Duplicate Detection Flow Diagram

```
Order Request
     |
     v
[Generate Idempotency Key]
     |
     v
[Check Cache]
     |
     +---> CACHE MISS ---------> [Create Pending Entry] --> [Place Order] --> [Update Cache: Completed]
     |
     +---> CACHE HIT
             |
             +---> Status: Completed --> [Return Cached Result] (NO API CALL)
             |
             +---> Status: Pending ----> [Return "Processing"] (NO API CALL)
             |
             +---> Status: Failed -----> [Create New Entry] --> [Retry Order] --> [Update Cache]
```

---

## Distributed Cache Support

### Redis Integration

```python
import redis
import json
from typing import Optional

class DistributedIdempotencyCache:
    """
    Redis-backed idempotency cache for multi-instance deployments.
    """
    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        ttl_seconds: int = 3600
    ):
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True
        )
        self.ttl_seconds = ttl_seconds
        self.key_prefix = "idempotency:"

    def _redis_key(self, idempotency_key: str) -> str:
        """Generate Redis key with prefix."""
        return f"{self.key_prefix}{idempotency_key}"

    def put(
        self,
        idempotency_key: str,
        order_details: dict,
        request_id: str,
        order_id: Optional[str] = None,
        status: str = "pending"
    ):
        """
        Store entry in Redis.
        """
        entry = {
            'idempotency_key': idempotency_key,
            'order_id': order_id,
            'order_details': order_details,
            'request_id': request_id,
            'created_time': int(time.time() * 1000),
            'status': status,
            'access_count': 0
        }

        redis_key = self._redis_key(idempotency_key)
        self.redis_client.setex(
            redis_key,
            self.ttl_seconds,
            json.dumps(entry)
        )

    def get(self, idempotency_key: str) -> Optional[dict]:
        """
        Retrieve entry from Redis.
        """
        redis_key = self._redis_key(idempotency_key)
        data = self.redis_client.get(redis_key)

        if not data:
            return None

        entry = json.loads(data)

        # Increment access count
        entry['access_count'] = entry.get('access_count', 0) + 1
        self.redis_client.setex(
            redis_key,
            self.ttl_seconds,
            json.dumps(entry)
        )

        return entry

    def update_status(
        self,
        idempotency_key: str,
        status: str,
        order_id: Optional[str] = None,
        error: Optional[str] = None
    ):
        """
        Update entry status in Redis.
        """
        redis_key = self._redis_key(idempotency_key)
        data = self.redis_client.get(redis_key)

        if not data:
            return

        entry = json.loads(data)
        entry['status'] = status

        if order_id:
            entry['order_id'] = order_id

        if error:
            entry['error'] = error

        self.redis_client.setex(
            redis_key,
            self.ttl_seconds,
            json.dumps(entry)
        )

    def delete(self, idempotency_key: str):
        """
        Remove entry from Redis.
        """
        redis_key = self._redis_key(idempotency_key)
        self.redis_client.delete(redis_key)

    def get_stats(self) -> dict:
        """
        Get cache statistics from Redis.
        """
        pattern = f"{self.key_prefix}*"
        keys = self.redis_client.keys(pattern)

        return {
            'total_entries': len(keys),
            'redis_info': self.redis_client.info('memory')
        }
```

---

## Configuration Schema

```yaml
idempotency:
  # Enable/disable idempotency
  enabled: true

  # Key generation
  keyGeneration:
    algorithm: "SHA256"
    timestampResolution: 60000    # 1 minute
    includeAccount: true
    includeSymbol: true
    includeSide: true
    includeQuantity: true
    includeOrderType: true
    includePrices: true           # Include limit/stop prices

  # Cache configuration
  cache:
    type: "in_memory"             # "in_memory" or "redis"
    ttl: 3600000                  # 1 hour (milliseconds)
    cleanupInterval: 300000       # 5 minutes

    # Redis configuration (if type: redis)
    redis:
      host: "localhost"
      port: 6379
      db: 0
      password: null
      ttlSeconds: 3600

  # Behavior
  behavior:
    returnCachedResult: true      # Return cached result for duplicates
    allowRetryAfterFailure: true  # Allow retry if previous attempt failed
    allowRetryAfterExpiry: true   # Allow retry after TTL expires
    logDuplicates: true

  # Monitoring
  monitoring:
    trackCacheHitRate: true
    trackKeyGeneration: true
    alertOnHighDuplicateRate: true
    duplicateRateThreshold: 0.05  # Alert if > 5% duplicates
```

---

## Error Scenarios & Recovery

### Scenario 1: Cache Unavailable

**Situation:**
- Redis cache down or unreachable
- Cannot check for duplicates

**Detection:**
```python
try:
    cached = idempotency_cache.get(key)
except CacheUnavailableError:
    # Cache unavailable
    log_warning("Idempotency cache unavailable")
```

**Recovery:**
- Fall back to stateless mode (no idempotency)
- Log cache unavailability
- Alert monitoring system
- Continue order placement (accept risk of duplicates)
- Emit metric for cache failures

**Expected Outcome:**
- Orders still placed (availability prioritized)
- Temporary duplicate risk accepted
- System remains operational

---

### Scenario 2: Key Collision (Extremely Rare)

**Situation:**
- Two different orders generate same idempotency key
- Collision probability: ~2^-256 (negligible but possible)

**Detection:**
```python
if cached_entry.order_details != current_order_details:
    log_critical("Idempotency key collision detected!")
    emit_alert("idempotency_collision")
```

**Recovery:**
- Log critical alert
- Compare full order details
- If details match → True duplicate
- If details differ → Collision, allow order
- Investigate root cause

---

## Implementation Checklist

- [ ] Implement SHA-256 key generation
- [ ] Add timestamp bucketing (minute resolution)
- [ ] Normalize order characteristics
- [ ] Build in-memory cache with TTL
- [ ] Implement cache cleanup timer
- [ ] Add duplicate detection in order placement
- [ ] Return cached results for duplicates
- [ ] Implement Redis distributed cache
- [ ] Add cache failover handling
- [ ] Implement cache statistics
- [ ] Add configuration loading
- [ ] Write unit tests for key generation
- [ ] Write integration tests for duplicate detection
- [ ] Test cache expiration
- [ ] Test distributed cache coordination

---

## Validation Criteria

### Zero Duplicate Orders
**Target:** 0% duplicate orders with idempotency enabled
- Same key generated for identical requests
- Cache prevents duplicate submissions
- API not called for confirmed duplicates

**Validation:**
- Submit 1000 duplicate order requests
- Verify 0 duplicate orders placed
- Verify cache hit rate = 999/1000

### Fast Key Generation
**Target:** <1ms average key generation time
- SHA-256 calculation fast
- Normalization overhead minimal

**Validation:**
- Generate 10,000 keys
- Measure p50, p95, p99 latencies
- Verify all < 1ms

---

## Metrics & Monitoring

```yaml
Metrics:
  - name: "idempotency_key_generation_duration_ms"
    type: histogram
    buckets: [0.1, 0.5, 1, 5, 10]

  - name: "idempotency_cache_hits"
    type: counter

  - name: "idempotency_cache_misses"
    type: counter

  - name: "idempotency_duplicate_orders_prevented"
    type: counter

  - name: "idempotency_cache_size"
    type: gauge

Alerts:
  - name: "HighDuplicateRate"
    condition: "rate(idempotency_duplicate_orders_prevented[5m]) / rate(orders_placed[5m]) > 0.05"
    severity: "MEDIUM"

  - name: "IdempotencyCacheUnavailable"
    condition: "idempotency_cache_errors > 0"
    severity: "HIGH"
```

---

## References

1. **ERRORS_AND_WARNINGS_CONSOLIDATED.md**
   - GAP-API-SCENARIO-001: Network interruption (CRITICAL)
   - Lines 182-191

2. **Related Specifications**
   - ORDER_STATUS_VERIFICATION_SPEC.md
   - ORDER_LIFECYCLE_SPEC.md

---

**Document Status:** DRAFT - Ready for Technical Review
