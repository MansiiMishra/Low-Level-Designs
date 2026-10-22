# Inventory Management System — Low-Level Design (LLD)

## 1. Requirements (5 minutes)

### Functional Requirements

1. Track product inventory across multiple warehouses.
2. Add stock to a specific warehouse.
3. Remove stock from a specific warehouse.
4. Check which warehouses can fulfill a requested quantity.
5. Transfer stock between warehouses.
6. Configure low-stock alerts per product per warehouse.
7. Reject operations that would result in negative inventory.
8. Support concurrent operations safely.

### Out of Scope

- Product catalog management.
- Order processing and payments.
- Persistent storage.
- Dynamic warehouse creation and deletion.

**Assumptions**
- Warehouses are configured at startup.
- Product IDs identify products; product details are managed externally.
- Multiple alert configurations can exist for a product.
- Alerts fire when stock crosses a threshold downward.
- Transfers are atomic and instantaneous for this interview design.

## 2. Core Entities and Relationships

| Entity | Responsibility | Representation |
|---|---|---|
| `InventoryManager` | Public API; coordinates operations across warehouses | Class |
| `Warehouse` | Tracks stock, enforces inventory rules, manages alerts | Class |
| `AlertConfig` | Pairs an alert threshold with a listener | Value object |
| `AlertListener` | Defines the callback for low-stock notifications | Interface |
| `Product` | Identified by `productId`; catalog is external | No class needed |

### Relationships

```text
InventoryManager
    └── Map<WarehouseId, Warehouse>
             ├── inventory: Map<ProductId, Quantity>
             └── alertConfigs: Map<ProductId, List<AlertConfig>>

AlertConfig
    ├── threshold: int
    └── listener: AlertListener

AlertListener (interface)
    ├── EmailAlertListener
    ├── WebhookAlertListener
    └── LoggingAlertListener
```

**Why no `Product` class?**

The system only needs a product identifier and its quantity. Product names, descriptions, and catalog behavior are outside scope, so a `productId` is sufficient.

## 3. Class Design

### 3.1 `InventoryManager` — Orchestrator

**Purpose:** Exposes the system's public API and coordinates operations across warehouses.

**State**

```text
- warehouses: Map<String, Warehouse>
```

**Methods**

```text
+ InventoryManager(warehouseIds)
+ addStock(warehouseId, productId, quantity): void
+ removeStock(warehouseId, productId, quantity): boolean
+ transfer(productId, fromWarehouseId, toWarehouseId, quantity): boolean
+ getWarehousesWithAvailability(productId, quantity): List<String>
+ setLowStockAlert(warehouseId, productId, threshold, listener): void
```

**Responsibilities**
- Creates warehouses during initialization.
- Routes stock operations to the appropriate warehouse.
- Coordinates transfers between two warehouses.
- Aggregates availability across all warehouses.
- Delegates alert configuration to the selected warehouse.

**Why a map?**

Warehouse IDs map directly to warehouse objects, providing average \(O(1)\) lookup.

**Concepts:** Encapsulation, composition, orchestration, separation of concerns.

### 3.2 `Warehouse` — Inventory Owner

**Purpose:** Manages stock for one warehouse and enforces the no-negative-inventory invariant.

**State**

```text
- id: String
- inventory: Map<String, Integer>
- alertConfigs: Map<String, List<AlertConfig>>
```

**Methods**

```text
+ Warehouse(id)
+ addStock(productId, quantity): void
+ removeStock(productId, quantity): boolean
+ getStock(productId): int
+ checkAvailability(productId, quantity): boolean
+ setLowStockAlert(productId, threshold, listener): void
- getAlertsToFire(productId, previousQty, newQty): List<AlertEvent>
```

`AlertEvent` represents the listener and the stock details to notify. It can be a small internal data structure.

**Responsibilities**
- Tracks quantities for each product.
- Treats an unknown product as having zero stock.
- Rejects invalid quantities and removals exceeding available stock.
- Maintains per-product alert configurations.
- Detects when a stock decrease crosses an alert threshold.
- Synchronizes access to shared state.

**Why keep inventory inside `Warehouse`?**

Each warehouse owns its stock and rules. It does not need to know about other warehouses; cross-warehouse coordination belongs to `InventoryManager`.

**Concepts:** Encapsulation, SRP, invariant enforcement, data hiding.

### 3.3 `AlertConfig` — Value Object

**Purpose:** Keeps a threshold and its associated listener together.

**State**

```text
- threshold: int
- listener: AlertListener
```

**Methods**

```text
+ AlertConfig(threshold, listener)
+ getThreshold(): int
+ getListener(): AlertListener
```

Both fields are immutable after construction.

A product can have multiple alert configurations—for example, a warning threshold of 20 units and a critical threshold of 5 units.

**Concepts:** Immutability, value object, explicit modeling.

### 3.4 `AlertListener` — Notification Contract

**Purpose:** Defines what the warehouse calls when stock crosses a low-stock threshold.

```text
interface AlertListener:
    + onLowStock(warehouseId, productId, currentQuantity): void
```

Possible implementations:

```text
class EmailAlertListener implements AlertListener
class WebhookAlertListener implements AlertListener
class LoggingAlertListener implements AlertListener
```

The warehouse only invokes the interface. It does not know whether the listener sends an email, calls a webhook, or writes a log.

**Concepts:** Abstraction, polymorphism, Dependency Inversion Principle (DIP), Observer Pattern.

## 4. Final Class Design

```text
class InventoryManager:
    - warehouses: Map<String, Warehouse>

    + InventoryManager(warehouseIds)
    + addStock(warehouseId, productId, quantity): void
    + removeStock(warehouseId, productId, quantity): boolean
    + transfer(productId, fromWarehouseId, toWarehouseId, quantity): boolean
    + getWarehousesWithAvailability(productId, quantity): List<String>
    + setLowStockAlert(warehouseId, productId, threshold, listener): void


class Warehouse:
    - id: String
    - inventory: Map<String, Integer>
    - alertConfigs: Map<String, List<AlertConfig>>

    + Warehouse(id)
    + addStock(productId, quantity): void
    + removeStock(productId, quantity): boolean
    + getStock(productId): int
    + checkAvailability(productId, quantity): boolean
    + setLowStockAlert(productId, threshold, listener): void
    - getAlertsToFire(productId, previousQty, newQty): List<AlertEvent>


class AlertConfig:
    - threshold: int
    - listener: AlertListener

    + AlertConfig(threshold, listener)
    + getThreshold(): int
    + getListener(): AlertListener


interface AlertListener:
    + onLowStock(warehouseId, productId, currentQuantity): void
```

## 5. Core Workflows

### 5.1 Add Stock

1. Look up the warehouse.
2. Reject an unknown warehouse ID.
3. Validate that quantity is positive.
4. Lock the warehouse.
5. Read the current quantity, defaulting to zero.
6. Update the quantity by adding the new stock.
7. Release the lock.

Adding stock cannot cause a downward crossing of a low-stock threshold, so the source design does not check alerts here.

### 5.2 Remove Stock

1. Look up the warehouse.
2. Reject an invalid or non-positive quantity.
3. Lock the warehouse.
4. Read the current stock.
5. If stock is insufficient, return `false` without changing state.
6. Calculate and store the new quantity.
7. Identify alert thresholds crossed by the decrease.
8. Release the lock.
9. Invoke the collected listeners outside the lock.
10. Return `true`.

**Important:** Do not invoke external callbacks while holding the warehouse lock. A callback may perform slow network I/O or call back into the warehouse, blocking other operations or risking deadlock.

### 5.3 Check Availability

For a requested quantity \(q\), a warehouse can fulfill it when:

\[
\text{stock}(productId) \geq q
\]

The manager checks every warehouse and returns the IDs of those with sufficient stock.

If there are \(W\) warehouses, this operation takes \(O(W)\) time.

### 5.4 Transfer Stock

A transfer must be **atomic**: either the entire transfer succeeds, or neither warehouse's inventory changes.

The source design requires:
- Positive transfer quantity.
- Valid source and destination warehouses.
- Different source and destination warehouses.
- Sufficient stock at the source.
- Synchronization across both warehouses.

#### Lock ordering

Always acquire locks in a consistent order, such as ascending warehouse ID.

```text
transfer(productId, fromId, toId, quantity):
    if quantity <= 0 or fromId == toId:
        return false

    source = warehouses[fromId]
    destination = warehouses[toId]

    if source == null or destination == null:
        return false

    first = warehouse with smaller ID
    second = warehouse with larger ID

    lock(first)
        lock(second)
            if source stock < quantity:
                return false

            remove quantity from source
            add quantity to destination

    return true
```

The inventory validation and both stock updates must occur while both locks are held. Use internal operations that do not reacquire locks, or a reentrant locking strategy if public warehouse methods are reused.

**Why consistent lock ordering?**

Without it, two concurrent transfers in opposite directions could each hold one warehouse lock and wait indefinitely for the other, causing a deadlock.

**Why isn't checking stock first enough?**

A check followed by a separate removal creates a time-of-check-to-time-of-use (TOCTOU) race: another thread could change the stock between those operations. The check and update must be part of the same atomic critical section.

## 6. Low-Stock Alert Logic

An alert fires when stock crosses a threshold downward—not every time stock remains below the threshold.

For threshold \(T\), previous quantity \(P\), and new quantity \(N\):

\[
P \geq T \quad \text{and} \quad N < T
\]

Example with threshold 10:

| Operation | Stock change | Alert? |
|---|---:|---|
| Initial stock | 15 | No |
| Remove 6 | 15 → 9 | Yes |
| Remove 2 | 9 → 7 | No |
| Add 15 | 7 → 22 | No |
| Remove 13 | 22 → 9 | Yes |

This approach prevents duplicate alerts while stock remains below a threshold and naturally permits another alert after stock recovers and falls below the threshold again.

### Alert Processing

```text
getAlertsToFire(productId, previousQty, newQty):
    configs = alertConfigs[productId]
    alerts = []

    for config in configs:
        if previousQty >= config.threshold
           and newQty < config.threshold:
            alerts.add(AlertEvent(
                config.listener,
                productId,
                newQty
            ))

    return alerts
```

The helper only collects events. `removeStock()` dispatches them after releasing the lock.

## 7. OOP Principles and Design Patterns

### OOP Principles

| Principle | Application |
|---|---|
| **Encapsulation** | `Warehouse` owns and protects its inventory and alert state. |
| **Single Responsibility Principle (SRP)** | The manager coordinates; each warehouse manages its own stock; listeners handle notification delivery. |
| **Abstraction** | `AlertListener` hides notification implementation details. |
| **Polymorphism** | Email, webhook, and logging listeners implement the same contract. |
| **Dependency Inversion Principle (DIP)** | Warehouse logic depends on `AlertListener`, not a concrete email or webhook service. |
| **Composition** | `InventoryManager` contains warehouse objects; warehouses contain alert configurations. |
| **Immutability** | `AlertConfig` does not change after construction. |

### Design Patterns

**1. Observer Pattern**

The warehouse detects a low-stock event and notifies registered listeners. Each listener independently decides how to handle the notification.

**2. Dependency Inversion**

The warehouse depends on the `AlertListener` abstraction rather than concrete notification services. New notification mechanisms can be added without modifying inventory logic.

**3. Facade-style orchestration**

`InventoryManager` provides a single entry point for clients and hides the details of locating and coordinating warehouses.

## 8. Concurrency and Correctness

Concurrency is a central part of this design, not an optional afterthought.

### 8.1 Warehouse-Level Locking

Use the same lock for every public operation that reads or modifies shared warehouse state:

- `addStock()`
- `removeStock()`
- `getStock()`
- `checkAvailability()`
- `setLowStockAlert()`

This prevents race conditions involving shared maps and read-modify-write operations.

**Trade-off:** A single warehouse-level lock is simple and safe for interview scope, but unrelated products in the same warehouse cannot be modified concurrently.

### 8.2 Cross-Warehouse Atomicity

A transfer requires coordinated locks on both warehouses. Both the stock check and the updates must happen while both locks are held.

For a production implementation, alternatives include:
- Fine-grained per-product locking.
- Transactional persistence with atomic updates.
- Explicit transfer records and states for real shipments.

### 8.3 Dispatch Alerts Outside Locks

Collect the alerts while synchronized, then invoke callbacks after releasing the lock. This keeps the critical section short and avoids holding locks during slow external work.

**Production caveat:** If notifications must never be lost, dispatching in-memory callbacks after unlocking is not sufficient on its own. A durable event/outbox mechanism and retry policy may be needed.

## 9. Edge Cases

- Unknown warehouse ID.
- Unknown product ID: stock defaults to zero.
- Zero or negative quantities.
- Attempting to remove more stock than available.
- Transfer between the same warehouse.
- Transfer with invalid source or destination.
- Concurrent removals that would otherwise oversell stock.
- Concurrent transfers in opposite directions.
- Multiple thresholds configured for the same product.
- Stock remaining below a threshold should not repeatedly trigger the same alert.
- Stock recovering and later crossing the threshold downward should trigger another alert.
- Listener failures should not corrupt inventory state.
- Duplicate warehouse IDs during initialization should be handled explicitly.

Validate inputs before mutating state. Failed operations must leave inventory unchanged.

## 10. Complexity Analysis

Let:
- \(W\) = number of warehouses.
- \(A\) = number of alert configurations for one product.

| Operation | Time complexity | Explanation |
|---|---|---|
| Look up warehouse | Average \(O(1)\) | Hash-map lookup |
| Add stock | Average \(O(1)\) | One product quantity update |
| Remove stock without alerts | Average \(O(1)\) | Read, validate, and update quantity |
| Check availability in one warehouse | Average \(O(1)\) | Product map lookup |
| Find warehouses with availability | \(O(W)\) | Check every warehouse |
| Configure an alert | Average \(O(1)\) | Map lookup plus list append |
| Check alerts after removal | \(O(A)\) | Inspect configurations for that product |
| Transfer | Average \(O(1)\) work, excluding lock contention | Two warehouse lookups and two quantity updates |

Lock contention can increase actual latency, and callback execution time depends on the listener implementation.

## 11. Extensions and Trade-offs

### 11.1 Inventory Reservations

For an e-commerce checkout, stock should sometimes be reserved before payment finishes. Otherwise, multiple customers might see the same last item as available.

Add:

```text
class Warehouse:
    - inventory: Map<ProductId, Quantity>
    - reserved: Map<ProductId, Quantity>
    - reservations: Map<ReservationId, Reservation>

    + reserveStock(productId, quantity, reservationId, timeoutMs): boolean
    + confirmReservation(reservationId): boolean
    + releaseReservation(reservationId): void


class Reservation:
    - productId: String
    - quantity: int
    - expiresAt: timestamp
```

Available stock becomes:

\[
\text{available} = \text{inventory} - \text{reserved}
\]

A reservation holds stock for a limited time. Confirmation deducts physical inventory; cancellation or expiration releases the reserved quantity.

### 11.2 In-Transit Inventory

The basic transfer model assumes stock moves instantaneously. Real shipments may take days.

Introduce a `Transfer` entity to represent inventory while it is in transit:

```text
class Transfer:
    - id: String
    - productId: String
    - quantity: int
    - fromWarehouseId: String
    - toWarehouseId: String
    - createdAt: timestamp
```

The source warehouse deducts stock when the shipment starts. The transfer record tracks the stock until arrival, when the destination warehouse receives it.

This keeps stock accounted for without making in-transit inventory available for new orders.

### 11.3 Fine-Grained Locking

A warehouse-wide lock serializes operations on different products. Per-product locks can increase concurrency, but transfers then require carefully ordered locks for both warehouse/product pairs.

Use the simpler warehouse lock first in an interview; explain the optimization only if asked.

## 12. Recommended Interview Flow

1. **Clarify requirements:** Warehouses, inventory operations, alerts, concurrency, and out-of-scope concerns.
2. **Identify entities:** `InventoryManager`, `Warehouse`, `AlertConfig`, and `AlertListener`.
3. **Design the public API:** Define methods and return types.
4. **Choose data structures:** Warehouse map, product quantity map, and alert configuration lists.
5. **Implement stock operations:** Validate quantities and prevent negative inventory.
6. **Handle alerts:** Detect downward threshold crossings and invoke callbacks outside locks.
7. **Implement transfers:** Lock both warehouses in a consistent order and update atomically.
8. **Test edge cases:** Insufficient stock, invalid IDs, repeated alerts, and concurrent transfers.
9. **Discuss extensions:** Reservations and in-transit stock.

### Expected Interview Depth

- **Junior:** Correct stock tracking, basic validation, and no negative inventory.
- **Mid-level:** Clear separation of responsibilities, thread safety, and a pluggable alert interface.
- **Senior:** Atomic multi-warehouse transfers, deadlock prevention, TOCTOU races, and locking trade-offs.

## Key Takeaway

The central design decision is to separate **cross-warehouse coordination from per-warehouse inventory management**.

- `InventoryManager` orchestrates operations across warehouses.
- `Warehouse` owns stock, enforces invariants, and manages alerts.
- `AlertConfig` pairs thresholds with listeners.
- `AlertListener` decouples low-stock detection from notification delivery.
- Atomic transfers require both warehouse locks to be held during validation and updates.
- The Observer Pattern and Dependency Inversion make alerts pluggable.

For interviews, prioritize **correct inventory invariants, atomic transfers, deadlock prevention, and alert threshold-crossing behavior** before discussing reservations or distributed storage.