# Low-Level Design: Elevator System

## 1. Requirements (~5 minutes)

### Functional Requirements

1. Manage 3 elevators serving 10 floors, numbered 0–9.
2. Users can request an elevator using UP or DOWN hall calls.
3. Passengers can select multiple destination floors inside an elevator.
4. The system dispatches an appropriate elevator for each hall call.
5. Elevators move in discrete time steps using `step()`.
6. Hall calls specify a direction; destination requests do not.
7. Invalid floor requests return `false`.
8. Requests for the current floor are treated as no-ops.
9. Elevators continue in their current direction while servicing requests ahead, then reverse when necessary.
10. An elevator becomes IDLE when no requests remain.

### Out of Scope

- Passenger capacity and weight limits
- Door operations and emergency stops
- UI and rendering
- Dynamic floor/elevator configuration
- Real hardware and sensor integration
- Concurrent request processing in the initial simulation

### Clarifying Questions

- Are we designing a simulation or real hardware control system?  
  **Assumption:** A discrete-time simulation using `step()`.
- Are hall calls directional?  
  **Assumption:** Yes, UP and DOWN.
- Can passengers select multiple destinations?  
  **Assumption:** Yes.
- How should invalid requests be handled?  
  **Assumption:** Return `false`; current-floor requests are no-ops.

**Concepts:** Scope management and separation of concerns.

---

## 2. Entities and Relationships (~3 minutes)

| Entity | Responsibility |
|---|---|
| `ElevatorController` | Coordinates elevators, dispatches hall calls, and advances the simulation. |
| `Elevator` | Maintains position, direction, and pending requests; controls movement. |
| `Request` | Represents a requested stop, including its floor and type. |
| `Direction` | Represents movement state: UP, DOWN, or IDLE. |
| `RequestType` | Distinguishes UP pickup, DOWN pickup, and destination requests. |

### Relationships

- `ElevatorController` manages multiple `Elevator` objects.
- Each `Elevator` maintains a set of `Request` objects.
- `Request` uses `RequestType` to identify the purpose of a stop.
- `Direction` represents an elevator's current movement state.

A separate `Floor` class is unnecessary because floors are represented by integers and have no independent behavior in this design.

**Concepts and principles:**
- **Encapsulation:** Keep state and behavior together.
- **Single Responsibility Principle (SRP):** Separate coordination from movement.
- **Object modeling:** Create classes for entities with meaningful state or behavior.

### High-Level Flow

```text
User
 |
 v
ElevatorController
 |
 |-- Selects an elevator for a hall call
 |
 v
Elevator
 |
 |-- Stores Request objects
 |-- Moves using step()
 |-- Stops and changes direction when required
 |
 v
Requested Floor
```

---

## 3. Class Design (~10–15 minutes)

### 3.1. ElevatorController

**Purpose:** Coordinates elevators, dispatches hall calls, and advances the simulation.

**State:**

- `elevators: List<Elevator>` — stores all elevators managed by the controller.

The controller dispatches hall calls immediately, so it does not maintain a queue of unassigned requests.

**Methods:**

- `ElevatorController()` — initializes three elevators, each starting on floor 0.
- `requestElevator(floor, type): boolean` — validates a hall call, selects an elevator, and assigns the request.
- `step(): void` — advances every elevator by one simulation tick.

**Concepts and principles:**
- **SRP:** Coordinates system-wide operations without implementing elevator movement.
- **Encapsulation:** Keeps track of the managed elevators.
- **Separation of concerns:** Delegates movement to `Elevator`.

Hall calls use `RequestType`, rather than `Direction`, because a hall call cannot have type `IDLE` or `DESTINATION`.

### 3.2. Elevator

**Purpose:** Represents an individual elevator and manages its movement, direction, and pending stops.

**State:**

- `currentFloor: int` — tracks the elevator's current floor.
- `direction: Direction` — represents UP, DOWN, or IDLE.
- `requests: Set<Request>` — stores unique pending requests.

A `Set` prevents duplicate requests when `equals()` and `hashCode()` use both the floor and request type.

**Methods:**

- `Elevator()` — initializes floor 0, IDLE direction, and an empty request set.
- `addRequest(request): boolean` — validates and adds a request unless it is invalid, already served, or duplicated.
- `step(): void` — executes one movement tick: select direction, stop, reverse, or move.
- `getCurrentFloor(): int` — returns the current floor.
- `getDirection(): Direction` — returns the current movement direction.
- `hasRequestsAhead(direction): boolean` — checks whether any pending request lies ahead in the given direction.

**Concepts and principles:**
- **Encapsulation:** The elevator owns its movement and request state.
- **SRP:** Handles individual elevator behavior.
- **Tell, Don't Ask:** The controller delegates movement through `step()`.
- **State modeling:** Uses IDLE, UP, and DOWN to represent movement states.

### 3.3. Request

**Purpose:** Represents a stop and distinguishes its floor from the reason the elevator needs to stop there.

**State:**

- `floor: int` — identifies the requested floor.
- `type: RequestType` — identifies a pickup or destination request.

**Methods:**

- `Request(floor, type)` — initializes the request.
- `getFloor(): int` — returns the requested floor.
- `getType(): RequestType` — returns the request type.
- `equals(other): boolean` — considers requests equal when both floor and type match.
- `hashCode(): int` — generates a hash consistent with `equals()`.

**Concepts:**
- **Encapsulation:** Groups request-related data into one object.
- **Value Object:** Request equality is based on its values.
- **Type safety:** Uses an enum to represent request types explicitly.

### 3.4. Direction Enum

**Purpose:** Represents an elevator's current movement state.

```text
Direction:
    UP
    DOWN
    IDLE
```

- `UP` — moving upward.
- `DOWN` — moving downward.
- `IDLE` — no active movement direction.

**Concept:** Explicit state modeling makes movement transitions predictable and prevents movement when no requests exist.

### 3.5. RequestType Enum

**Purpose:** Distinguishes why an elevator needs to stop.

```text
RequestType:
    PICKUP_UP
    PICKUP_DOWN
    DESTINATION
```

- `PICKUP_UP` — a passenger wants to travel upward.
- `PICKUP_DOWN` — a passenger wants to travel downward.
- `DESTINATION` — a passenger inside the elevator selected a floor.

**Concept:** Type safety enables direction-aware stopping decisions.

---

## 4. Movement Algorithm and Design Patterns

### SCAN Algorithm

The elevator uses a SCAN-style algorithm: continue in the current direction while requests remain ahead, then reverse when no requests remain ahead.

### `step()` — Core Logic

1. If no requests exist, set direction to `IDLE` and return.
2. If the elevator is `IDLE`, select the nearest request to establish its direction.
3. If the current floor has an eligible pickup or destination request, remove the served request and return without moving during that tick.
4. If no requests remain ahead, reverse direction and return.
5. Otherwise, move one floor in the current direction.

### Important Rules

- Moving UP: stop for `PICKUP_UP` and `DESTINATION`.
- Moving DOWN: stop for `PICKUP_DOWN` and `DESTINATION`.
- Travel toward any pending request, even if its pickup direction does not match the current direction.
- Serve an opposite-direction pickup when returning in the requested direction.
- Do not move during the same tick in which the elevator stops or reverses.
- Let the movement logic handle floor boundaries instead of hardcoding reversals at floors 0 and 9.
- Use deterministic tie-breaking when choosing the nearest request because a `Set` has no guaranteed iteration order.

**Concepts and patterns:**
- **SCAN algorithm:** Services stops along a sweep before reversing direction.
- **State Machine:** Manages transitions between IDLE, UP, and DOWN.
- **Deterministic behavior:** Makes the simulation predictable and testable.

### Elevator Selection Strategy

Start with a nearest-elevator selection algorithm. More advanced selection can consider direction, distance, existing requests, and estimated waiting time.

The **Strategy Pattern** is optional if multiple dispatch algorithms need to be interchangeable.

```text
ElevatorSelectionStrategy
    + selectElevator(request, elevators): Elevator

NearestElevatorStrategy implements ElevatorSelectionStrategy
    + selectElevator(request, elevators): Elevator

ElevatorController
    - selectionStrategy: ElevatorSelectionStrategy
```

**Concepts and principles:**
- **Strategy Pattern:** Encapsulates interchangeable dispatch algorithms.
- **Open/Closed Principle (OCP):** Allows new strategies without rewriting the controller.
- **Dependency Inversion Principle (DIP):** Makes the controller depend on the strategy abstraction.

Do not introduce this abstraction unless it adds value to the requirements.

---

## 5. Final Class Design

This is the consolidated class design to present to the interviewer before implementation.

```text
class ElevatorController:
    - elevators: List<Elevator>

    + ElevatorController()
    + requestElevator(floor: int, type: RequestType): boolean
    + step(): void


class Elevator:
    - currentFloor: int
    - direction: Direction
    - requests: Set<Request>

    + Elevator()
    + addRequest(request: Request): boolean
    + step(): void
    + getCurrentFloor(): int
    + getDirection(): Direction
    - hasRequestsAhead(direction: Direction): boolean


class Request:
    - floor: int
    - type: RequestType

    + Request(floor: int, type: RequestType)
    + getFloor(): int
    + getType(): RequestType
    + equals(other: Request): boolean
    + hashCode(): int


enum Direction:
    UP
    DOWN
    IDLE


enum RequestType:
    PICKUP_UP
    PICKUP_DOWN
    DESTINATION
```

### Class Responsibilities and Concepts

| Class | Responsibility | Key concept |
|---|---|---|
| `ElevatorController` | Coordinates elevators and dispatches requests. | SRP |
| `Elevator` | Manages movement and pending stops. | Encapsulation, State Machine |
| `Request` | Represents a requested stop. | Value Object |
| `Direction` | Represents movement state. | Explicit state modeling |
| `RequestType` | Identifies the reason for a stop. | Type safety |

**Design takeaway:** `ElevatorController` handles system-wide coordination, while `Elevator` encapsulates movement and request processing. The SCAN algorithm manages stop ordering, and the optional Strategy Pattern supports interchangeable dispatch algorithms.

---

## 6. OOP Concepts, Design Principles, and Patterns

| Concept / Principle / Pattern | Application |
|---|---|
| Encapsulation | `Elevator` manages its position, direction, and requests. |
| Abstraction | Public methods expose operations without exposing movement internals. |
| Composition | The controller manages elevator objects; elevators maintain request objects. |
| Single Responsibility Principle (SRP) | The controller coordinates, the elevator moves, and the request represents a stop. |
| Tell, Don't Ask | The controller calls `step()` rather than manipulating movement state. |
| State Machine | The elevator transitions between IDLE, UP, and DOWN. |
| SCAN Algorithm | Services requests along a sweep before reversing direction. |
| Strategy Pattern (optional) | Makes dispatch algorithms interchangeable. |
| Open/Closed Principle (OCP) | New dispatch strategies can be added with minimal controller changes. |
| Dependency Inversion Principle (DIP) | With Strategy Pattern, the controller depends on a strategy interface. |
| Value Object | A request is identified by its floor and request type. |

---

## 7. Important Edge Cases

1. **Invalid floor:** Reject floors below 0 or above 9.
2. **Invalid hall-call type:** Reject `DESTINATION` in `requestElevator()`.
3. **Current-floor request:** Treat it as already served.
4. **Duplicate request:** Avoid adding an identical floor-and-type request twice.
5. **No pending requests:** Transition to IDLE.
6. **Idle elevator with requests:** Select a deterministic initial direction.
7. **No requests ahead:** Reverse without moving during that tick.
8. **Opposite-direction pickup:** Pass the floor without stopping until traveling in the requested direction.
9. **Building boundary:** Reverse naturally when no requests remain ahead.
10. **Stopping at a floor:** Remove eligible requests and do not move during that tick.

**Interview highlight:** Stopping, reversing, and moving must be separate decisions within `step()` to avoid moving during the same tick in which the elevator stops or reverses.

---

## 8. Interview Delivery Flow

1. **Requirements:** Clarify floors, elevators, hall calls, destinations, simulation, and error handling.
2. **Entities:** Identify `ElevatorController`, `Elevator`, and `Request`; use enums for direction and request type.
3. **Controller:** Design dispatch and simulation coordination — SRP.
4. **Elevator:** Encapsulate position, direction, and requests — Encapsulation and Tell, Don't Ask.
5. **Request:** Represent floor and stop type — Value Object and type safety.
6. **Movement:** Implement SCAN-style behavior and IDLE/UP/DOWN transitions.
7. **Final Class Design:** Summarize class state, methods, and relationships before coding.
8. **Edge cases:** Verify stopping, reversing, duplicate requests, invalid floors, and idle behavior.

---

## Key Interview Takeaway

The design separates **system-wide coordination (`ElevatorController`) from individual elevator behavior (`Elevator`)**. Each elevator encapsulates its movement and request state, while the SCAN-style algorithm services stops efficiently.

Prioritize **Encapsulation, SRP, Tell, Don't Ask, explicit state modeling, deterministic movement, and the final class design**. The Strategy Pattern is an optional extension for interchangeable dispatch algorithms.
