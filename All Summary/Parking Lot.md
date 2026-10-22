# Low-Level Design: Parking Lot System

## 1. Requirements (~5 minutes)

### Functional Requirements

1. Support three vehicle types: Motorcycle, Car, and Large Vehicle.
2. Automatically assign an available parking spot compatible with the vehicle type.
3. Generate a unique ticket when a vehicle enters.
4. Validate the ticket when a vehicle exits.
5. Calculate parking fees using an hourly rate, rounding up to the nearest hour.
6. Free the assigned spot after a successful exit.
7. Reject entry when no compatible spot is available.
8. Reject invalid or already-used tickets.

### Out of Scope

- Payment processing
- Physical gate hardware
- Security cameras and monitoring
- UI and display systems
- Reservations and pre-booking

### Clarifying Questions

- Are parking spots assigned automatically? **Yes.**
- Which vehicle types are supported? **Motorcycle, Car, and Large Vehicle.**
- How are fees calculated? **A common hourly rate, rounded up to the next hour.**
- What happens when the lot is full? **Reject entry if no compatible spot exists.**
- What happens when a ticket is invalid or reused? **Reject the exit.**

**Concepts:** Scope management and separation of concerns. Define the system's responsibilities before designing classes.

---

## 2. Entities and Relationships (~3 minutes)

| Entity | Responsibility |
|---|---|
| `ParkingLot` | Coordinates spot allocation, ticket management, and fee calculation. |
| `ParkingSpot` | Represents a physical parking space and its properties. |
| `Ticket` | Records the details of a parking session. |
| `VehicleType` | Classifies the entering vehicle. |
| `SpotType` | Classifies the type of parking spot. |

A separate `Vehicle` class is unnecessary because the system only needs the vehicle's type, not its independent state or behavior.

### Relationships

- `ParkingLot` owns a collection of `ParkingSpot` objects.
- `ParkingLot` creates and tracks active `Ticket` objects.
- Each `Ticket` stores the ID of its assigned spot.
- `VehicleType` and `SpotType` are separate enums representing semantically different concepts.

### High-Level Flow

```text
Vehicle enters
      |
      v
  ParkingLot
      |
      |-- Find compatible available spot
      |-- Mark spot as occupied
      |-- Generate ticket
      |-- Store active ticket
      |
      v
  Return Ticket

Vehicle exits using ticket ID
      |
      v
  ParkingLot
      |
      |-- Validate ticket
      |-- Calculate fee
      |-- Free parking spot
      |-- Remove active ticket
      |
      v
  Return Fee
```

**Concepts and principles:**

- **Encapsulation:** Keep parking operations within `ParkingLot`.
- **Single Responsibility Principle (SRP):** Separate system coordination from data representation.
- **Object modeling:** Create classes for entities with meaningful state or responsibility; use enums for simple classifications.

---

## 3. Class Design (~10–15 minutes)

### 3.1. ParkingLot

**Purpose:** Acts as the orchestrator for vehicle entry, spot allocation, ticket validation, fee calculation, and exit.

#### State

- `spots: List<ParkingSpot>` — stores all parking spots available in the lot.
- `occupiedSpotIds: Set<String>` — tracks spot IDs currently assigned to active parking sessions.
- `activeTickets: Map<String, Ticket>` — maps ticket IDs to active tickets for efficient lookup.
- `hourlyRateCents: long` — stores the hourly rate in the smallest currency unit to avoid floating-point precision errors.

**Why track occupancy in ParkingLot?**

In this design, occupancy represents an assignment managed by the system. The controller tracks assigned spot IDs rather than storing an occupied flag on each spot.

This is a design choice, not a universal rule.

**Concepts:**
- **Encapsulation:** Centralizes parking operations and assignment state.
- **SRP:** Coordinates the parking workflow.
- **Data structure choice:** A `Set` provides efficient occupancy membership checks; a `Map` provides efficient ticket lookup.
- **Money representation:** Integer-based currency avoids floating-point rounding errors.

#### Methods

- `ParkingLot(spots, hourlyRateCents)` — initializes the lot with its configured spots and hourly rate.
- `enter(vehicleType): Ticket` — finds a compatible available spot, marks it occupied, creates a ticket, stores it, and returns it.
- `exit(ticketId): long` — validates the ticket, calculates the fee, frees the spot, removes the active ticket, and returns the fee.
- `findAvailableSpot(vehicleType): ParkingSpot?` — finds the first compatible spot not currently assigned.
- `mapVehicleTypeToSpotType(vehicleType): SpotType` — maps a vehicle classification to its required spot classification.
- `computeFee(entryTime, exitTime): long` — calculates the parking duration in rounded-up hours and multiplies it by the hourly rate.

**Concepts and principles:**
- **SRP:** The lot coordinates operations, while `ParkingSpot` and `Ticket` represent data.
- **Tell, Don't Ask:** Callers request entry or exit rather than manipulating occupancy and tickets directly.
- **Encapsulation:** Pricing configuration remains internal to the lot.

### 3.2. ParkingSpot

**Purpose:** Represents a physical parking space and stores its intrinsic properties.

#### State

- `id: String` — uniquely identifies the parking spot.
- `spotType: SpotType` — specifies which category of vehicle the spot accommodates.

#### Methods

- `ParkingSpot(id, spotType)` — initializes the spot's identity and type.
- `getId(): String` — returns the spot ID for allocation and ticket creation.
- `getSpotType(): SpotType` — returns the spot type for compatibility checks.

**Design decision:** `ParkingSpot` does not manage occupancy, tickets, or pricing. Those responsibilities belong to `ParkingLot` in this design.

**Concepts and principles:**
- **Encapsulation:** Keeps the spot's properties together.
- **SRP:** Represents spot data without managing the parking workflow.
- **Separation of concerns:** Distinguishes physical spot properties from system-managed assignment state.

### 3.3. Ticket

**Purpose:** Represents a parking session and stores the information needed to validate an exit and calculate the fee.

#### State

- `id: String` — uniquely identifies the ticket.
- `spotId: String` — identifies the assigned parking spot.
- `vehicleType: VehicleType` — records the entering vehicle's classification.
- `entryTimeMs: long` — records the entry timestamp in milliseconds.

The ticket stores `spotId` instead of a `ParkingSpot` reference, keeping the ticket independent of the spot's behavior.

All fields are read-only after construction.

#### Methods

- `Ticket(id, spotId, vehicleType, entryTimeMs)` — creates a ticket for a parking session.
- `getId(): String` — returns the ticket ID.
- `getSpotId(): String` — returns the assigned spot ID.
- `getVehicleType(): VehicleType` — returns the vehicle type recorded at entry.
- `getEntryTimeMs(): long` — returns the entry timestamp for fee calculation.

**Concepts and principles:**
- **Encapsulation:** Groups parking-session data into one object.
- **Immutability:** Ticket fields do not change after creation.
- **Law of Demeter:** The ticket stores a spot identifier instead of navigating through a `ParkingSpot` object.
- **Separation of concerns:** The ticket stores data; `ParkingLot` validates it and calculates fees.

### 3.4. SpotType Enum

**Purpose:** Represents the category of parking space.

```text
SpotType:
    MOTORCYCLE
    CAR
    LARGE
```

- `MOTORCYCLE` — accommodates motorcycles.
- `CAR` — accommodates regular cars.
- `LARGE` — accommodates large vehicles.

**Concept:** Type safety makes spot compatibility explicit.

### 3.5. VehicleType Enum

**Purpose:** Represents the category of the vehicle entering the lot.

```text
VehicleType:
    MOTORCYCLE
    CAR
    LARGE
```

- `MOTORCYCLE` — a motorcycle is entering.
- `CAR` — a regular car is entering.
- `LARGE` — a large vehicle is entering.

**Why use separate enums?**

`VehicleType` and `SpotType` represent different concepts even though they currently have the same values. Keeping them separate makes future compatibility rules easier to express.

**Concept:** Semantic modeling and type safety.

---

## 4. Core Logic and Important Decisions

### A. Vehicle Entry — `enter(vehicleType)`

**Purpose:** Assigns an available compatible spot and creates an active parking session.

1. Find an available spot matching the vehicle type.
2. If no compatible spot exists, reject entry without changing state.
3. Add the spot ID to `occupiedSpotIds`.
4. Generate a unique ticket ID.
5. Create a ticket containing the spot ID, vehicle type, and entry timestamp.
6. Store the ticket in `activeTickets`.
7. Return the ticket.

**Concepts:**
- **Encapsulation:** All entry operations are coordinated by `ParkingLot`.
- **State consistency:** Do not mark a spot occupied if allocation fails.
- **Separation of concerns:** Spot matching, ticket creation, and occupancy tracking have distinct responsibilities.

### B. Vehicle Exit — `exit(ticketId)`

**Purpose:** Validates the parking session, calculates the fee, and releases the assigned spot.

1. Reject a null or empty ticket ID.
2. Look up the ticket in `activeTickets`.
3. Reject the exit if the ticket does not exist or has already been used.
4. Get the current exit timestamp.
5. Calculate the parking fee.
6. Remove the spot ID from `occupiedSpotIds`.
7. Remove the ticket from `activeTickets`.
8. Return the fee.

Removing the ticket prevents a second exit using the same ticket.

**Concepts:**
- **Encapsulation:** The caller cannot directly alter occupancy.
- **State management:** A successful exit releases the spot and invalidates the ticket.
- **Idempotency consideration:** Repeated exit attempts are rejected rather than processing the same ticket again.

### C. Spot Allocation — `findAvailableSpot(vehicleType)`

**Purpose:** Finds the first available spot compatible with the entering vehicle.

1. Map `VehicleType` to the required `SpotType`.
2. Iterate through the spots.
3. Return the first spot whose type matches and whose ID is absent from `occupiedSpotIds`.
4. Return `null` if no matching spot exists.

**Concepts:**
- **Separation of concerns:** Allocation logic is separate from ticket validation.
- **Data structure choice:** The set supports efficient occupancy checks.
- **Algorithm:** Linear scan, with \(O(n)\) worst-case time for \(n\) spots.

### D. Fee Calculation — `computeFee(entryTime, exitTime)`

**Purpose:** Calculates the fee using the parking duration, rounding up every partial hour.

```text
computeFee(entryTime, exitTime)
    durationMillis = exitTime - entryTime
    hourMillis = 1000 * 60 * 60

    durationHours = durationMillis / hourMillis

    if durationMillis % hourMillis > 0
        durationHours++

    return durationHours * hourlyRateCents
```

**Example:** If the hourly rate is 500 cents and the vehicle stays for 2.5 hours, the fee is 1,500 cents.

A stay of even a few minutes is charged as one hour under the specified rule.

**Concepts:**
- **SRP:** Fee calculation is isolated in a dedicated method.
- **Integer arithmetic:** Avoids floating-point errors in currency calculations.
- **Boundary handling:** Partial hours are rounded up.

### E. Ticket Lookup — `activeTickets`

**Purpose:** Finds an active parking session using its ticket ID.

A `Map<String, Ticket>` is preferable to a list because the system looks up tickets by ID during exit.

**Concept:** Appropriate data structure selection; average \(O(1)\) lookup with a hash map.

---

## 5. Final Class Design

This is the consolidated class design to present before implementation.

```text
class ParkingLot:
    - spots: List<ParkingSpot>
    - occupiedSpotIds: Set<String>
    - activeTickets: Map<String, Ticket>
    - hourlyRateCents: long

    + ParkingLot(spots, hourlyRateCents)
    + enter(vehicleType: VehicleType): Ticket
    + exit(ticketId: String): long
    - findAvailableSpot(vehicleType: VehicleType): ParkingSpot?
    - mapVehicleTypeToSpotType(vehicleType: VehicleType): SpotType
    - computeFee(entryTimeMs: long, exitTimeMs: long): long


class ParkingSpot:
    - id: String
    - spotType: SpotType

    + ParkingSpot(id, spotType)
    + getId(): String
    + getSpotType(): SpotType


class Ticket:
    - id: String
    - spotId: String
    - vehicleType: VehicleType
    - entryTimeMs: long

    + Ticket(id, spotId, vehicleType, entryTimeMs)
    + getId(): String
    + getSpotId(): String
    + getVehicleType(): VehicleType
    + getEntryTimeMs(): long


enum SpotType:
    MOTORCYCLE
    CAR
    LARGE


enum VehicleType:
    MOTORCYCLE
    CAR
    LARGE
```

### Class Responsibilities and Concepts

| Class | Responsibility | Key concept |
|---|---|---|
| `ParkingLot` | Allocates spots, manages tickets, and calculates fees. | SRP, Encapsulation |
| `ParkingSpot` | Stores spot identity and type. | Separation of concerns |
| `Ticket` | Stores immutable parking-session data. | Immutability, Value-oriented modeling |
| `SpotType` | Classifies parking spots. | Type safety |
| `VehicleType` | Classifies entering vehicles. | Type safety |

**Design takeaway:** `ParkingLot` owns the workflow and relational assignment state, `ParkingSpot` represents intrinsic spot properties, and `Ticket` records the parking session.

---

## 6. OOP Concepts and Design Principles

| Concept / Principle | Application |
|---|---|
| Encapsulation | `ParkingLot` controls entry, exit, occupancy, and ticket state. |
| Single Responsibility Principle (SRP) | Each class has a distinct responsibility. |
| Tell, Don't Ask | Callers use `enter()` and `exit()` instead of modifying internal collections. |
| Immutability | Ticket data is read-only after construction. |
| Law of Demeter | `Ticket` stores `spotId` rather than a direct `ParkingSpot` reference. |
| Semantic modeling | Separate `VehicleType` and `SpotType` enums represent distinct concepts. |
| Appropriate data structures | A `Set` tracks occupied IDs and a `Map` indexes active tickets. |
| Separation of concerns | Allocation, fee calculation, ticket data, and spot properties are kept distinct. |

**Pattern note:** The core design does not require a formal GoF design pattern. Do not force a pattern where straightforward classes and clear responsibilities are sufficient.

---

## 7. Important Edge Cases

1. **No compatible spot:** Reject entry without modifying occupancy or tickets.
2. **Invalid vehicle type:** Reject invalid input; an enum prevents many invalid values.
3. **Null or empty ticket ID:** Reject the exit.
4. **Unknown ticket:** Return an error.
5. **Previously used ticket:** Reject the second exit.
6. **Partial hour:** Round up to the next hour.
7. **Very short stay:** Charge for one hour under the stated pricing rule.
8. **Spot release:** Remove the spot ID and active ticket after a successful exit.
9. **Duplicate ticket IDs:** Ensure ticket IDs are unique.
10. **Invalid timestamps:** Prevent negative parking durations if timestamps can be supplied or manipulated externally.

**Interview highlight:** Validate before mutating state. Entry should not occupy a spot when allocation fails, and exit should not free a spot until the ticket has been validated and the fee has been calculated successfully.

---

## 8. Interview Delivery Flow

1. **Requirements:** Clarify vehicle types, spot assignment, tickets, pricing, and failure handling.
2. **Entities:** Identify `ParkingLot`, `ParkingSpot`, and `Ticket`; use enums for vehicle and spot types.
3. **ParkingLot:** Design entry and exit workflows — SRP and Encapsulation.
4. **ParkingSpot:** Model intrinsic spot properties — separation of concerns.
5. **Ticket:** Store immutable parking-session information — Immutability and Law of Demeter.
6. **Core logic:** Explain allocation, fee calculation, and ticket validation.
7. **Final Class Design:** Summarize state, methods, and relationships before coding.
8. **Edge cases:** Verify full-lot behavior, invalid tickets, double exits, and fee rounding.

---

## Key Interview Takeaway

The Parking Lot design separates **workflow orchestration (`ParkingLot`), physical spot properties (`ParkingSpot`), and parking-session records (`Ticket`)**.

Prioritize **Encapsulation, SRP, Tell Don't Ask, immutability, semantic enums, and appropriate data structures**. The most important methods to explain are `enter()`, `exit()`, `findAvailableSpot()`, and `computeFee()`.
