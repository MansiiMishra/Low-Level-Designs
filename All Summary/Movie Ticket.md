# Movie Ticket Booking System — Low-Level Design (LLD)

## 1. Requirements (5 minutes)

### Functional Requirements
1. Search movies by title using case-insensitive substring matching.
2. Browse upcoming showtimes at a specific theater.
3. Support multiple theaters, each containing multiple screens.
4. Display available seats for a showtime.
5. Allow users to book multiple specific seats in a single reservation.
6. Generate a unique confirmation ID for each successful reservation.
7. Allow users to cancel reservations using the confirmation ID and release the seats.
8. Handle concurrent booking attempts so that **only one user can book a particular seat**.
9. If any requested seat is unavailable, the entire multi-seat booking must fail without partial changes.

### Constraints
- Every screen has the same layout: rows A–Z and seats 0–20, giving 546 seats per showtime.
- All seats have identical pricing; pricing is out of scope.
- Payment processing is out of scope and assumed to succeed.
- Rescheduling is not supported; users cancel and rebook instead.
- UI and seat-map rendering are out of scope.

## 2. Core Entities and Relationships

| Entity | Responsibility | Representation |
|---|---|---|
| `BookingSystem` | Orchestrates search, browsing, booking, and cancellation | Class |
| `Theater` | Represents a theater and owns its showtimes | Class |
| `Movie` | Represents a searchable movie | Class |
| `Showtime` | Represents one screening and owns seat availability and reservation state | Class |
| `Reservation` | Stores confirmation ID, selected seats, and associated showtime | Class |
| `Seat` | Identifies a seat, such as `A5` | String |
| `Screen` | Identifies the screening room, such as `Screen 3` | String field |

### Key Relationships

```text
BookingSystem
    └── List<Theater>
            └── List<Showtime>
                    ├── Movie
                    ├── Theater
                    └── List<Reservation>
                            ├── Showtime
                            └── List<String> seatIds
```

**Important design decision:** `Seat` and `Screen` are not separate classes in this design. Seats are simple identifiers, and the screen only needs a label because every screen has the same layout.

`Showtime` stores reservations, which serve as the **single source of truth for booked seats**.

## 3. Class Design

### 3.1 `BookingSystem` — Orchestrator

**Purpose:** Provides the main entry point for search, browsing, booking, and cancellation. It routes requests to the correct showtime and maintains lookup indexes.

**State**

```text
- theaters: List<Theater>
- moviesById: Map<String, Movie>
- showtimesByMovieId: Map<String, List<Showtime>>
- showtimesById: Map<String, Showtime>
- reservationsById: Map<String, Reservation>
```

**Methods**

```text
+ searchMovies(title: String): List<Showtime>
+ getShowtimesAtTheater(theater: Theater): List<Showtime>
+ book(showtimeId: String, seatIds: List<String>): Reservation
+ cancelReservation(confirmationId: String): void
```

**Method responsibilities**
- `searchMovies()`: Finds movies matching a title and returns their future showtimes.
- `getShowtimesAtTheater()`: Returns future showtimes at a selected theater.
- `book()`: Validates the request, finds the showtime, creates a reservation, and delegates atomic booking to `Showtime`.
- `cancelReservation()`: Finds a reservation by confirmation ID, delegates cancellation to its showtime, and removes it from the reservation index.

**Why the lookup maps?**

Without indexes, the system would scan all theaters and showtimes to find a showtime or reservation. The maps allow average \(O(1)\) lookup by ID.

The movie-to-showtimes index also avoids repeatedly scanning every showtime when searching by movie title.

**Concepts:** Separation of concerns, orchestration, encapsulation, hash maps, precomputed indexes.

### 3.2 `Theater` — Showtime Container

**Purpose:** Represents a physical theater and its schedule.

**State**

```text
- id: String
- name: String
- showtimes: List<Showtime>
```

**Methods**

```text
+ getShowtimes(): List<Showtime>
+ getShowtimesForMovie(movie: Movie): List<Showtime>
```

**Responsibilities**
- Maintains the theater's showtimes.
- Filters showtimes by movie.
- Does not manage seat availability or booking logic.

**Concepts:** Single Responsibility Principle (SRP), composition, encapsulation.

### 3.3 `Movie` — Searchable Entity

**Purpose:** Represents a movie that may be shown at multiple theaters and times.

**State**

```text
- id: String
- title: String
```

**Methods**

```text
+ getId(): String
+ getTitle(): String
```

**Why both ID and title?**

Movie titles are not guaranteed to be unique. The ID distinguishes different movies with the same title, while the title supports search.

Movie data is effectively immutable after construction.

**Concepts:** Encapsulation, immutability, entity identity.

### 3.4 `Showtime` — Core Booking and Concurrency Owner

**Purpose:** Represents a particular movie screening at a specific theater, time, and screen. It owns the booking state and protects seat availability from concurrent modifications.

**State**

```text
- id: String
- theater: Theater
- movie: Movie
- datetime: DateTime
- screenLabel: String
- reservations: List<Reservation>
```

**Methods**

```text
+ getId(): String
+ getTheater(): Theater
+ getDatetime(): DateTime
+ getMovie(): Movie
+ isAvailable(seatId: String): boolean
+ getAvailableSeats(): List<String>
+ book(reservation: Reservation): void
+ cancel(reservation: Reservation): void
```

**Responsibilities**
- Determines whether a seat is available.
- Returns the list of available seats.
- Validates seat IDs and requested seat availability.
- Atomically books all requested seats.
- Cancels reservations and releases seats.

**Key design decision: one source of truth**

The `reservations` list already contains the seat IDs for every successful booking. Therefore, seat availability can be derived from the list instead of maintaining a separate mutable `bookedSeats` set.

For example:

```text
reservations = [
    Reservation("R1", ["A5", "A6"]),
    Reservation("R2", ["B3"])
]
```

Seats `A5`, `A6`, and `B3` are booked. Removing a reservation automatically makes its seats available again.

**Concepts:** Encapsulation, SRP, atomicity, thread safety, single source of truth.

### 3.5 `Reservation` — Booking Record

**Purpose:** Stores the details of a successful booking and provides the information required for cancellation.

**State**

```text
- confirmationId: String
- showtime: Showtime
- seatIds: List<String>
```

**Methods**

```text
+ getConfirmationId(): String
+ getShowtime(): Showtime
+ getSeatIds(): List<String>
```

**Responsibilities**
- Stores the unique confirmation ID.
- Stores the seats included in the booking.
- References the associated showtime so cancellation can be routed directly.
- Returns defensive copies of the seat list to prevent external modification.

`Reservation` does not cancel itself. `Showtime` owns the reservation list, so cancellation must be performed there to keep state changes controlled and synchronized.

**Concepts:** Encapsulation, defensive copying, separation of responsibilities, object relationships.

## 4. Final Class Design

```text
class BookingSystem:
    - theaters: List<Theater>
    - moviesById: Map<String, Movie>
    - showtimesByMovieId: Map<String, List<Showtime>>
    - showtimesById: Map<String, Showtime>
    - reservationsById: Map<String, Reservation>

    + searchMovies(title): List<Showtime>
    + getShowtimesAtTheater(theater): List<Showtime>
    + book(showtimeId, seatIds): Reservation
    + cancelReservation(confirmationId): void


class Theater:
    - id: String
    - name: String
    - showtimes: List<Showtime>

    + getShowtimes(): List<Showtime>
    + getShowtimesForMovie(movie): List<Showtime>


class Movie:
    - id: String
    - title: String

    + getId(): String
    + getTitle(): String


class Showtime:
    - id: String
    - theater: Theater
    - movie: Movie
    - datetime: DateTime
    - screenLabel: String
    - reservations: List<Reservation>

    + isAvailable(seatId): boolean
    + getAvailableSeats(): List<String>
    + book(reservation): void
    + cancel(reservation): void


class Reservation:
    - confirmationId: String
    - showtime: Showtime
    - seatIds: List<String>

    + getConfirmationId(): String
    + getShowtime(): Showtime
    + getSeatIds(): List<String>


Constants:
    SEAT_LAYOUT = rows A-Z, seats 0-20
```

## 5. Core Workflows

### 5.1 Search Movies

1. Receive the search title.
2. Find movies whose titles contain the search term, ignoring case.
3. Retrieve the showtimes associated with each matching movie.
4. Return only future showtimes.

**Optimization:** Use `moviesById` and `showtimesByMovieId` indexes rather than scanning every showtime on every search.

### 5.2 Book Seats

1. Validate the showtime ID and seat list.
2. Find the showtime using `showtimesById`.
3. Generate a unique confirmation ID.
4. Create a `Reservation`.
5. Call `Showtime.book(reservation)`.
6. Inside a synchronized critical section:
   - Validate every seat ID.
   - Check that every requested seat is available.
   - If any seat is unavailable, fail without changing state.
   - Otherwise, add the reservation to the list.
7. Register the reservation in `reservationsById`.
8. Return the reservation.

### 5.3 Cancel Reservation

1. Receive the confirmation ID.
2. Find the reservation using `reservationsById`.
3. Get its associated showtime.
4. Call `Showtime.cancel(reservation)`.
5. Under synchronization, remove the reservation from the showtime's reservation list.
6. Remove the reservation from `reservationsById`.

The seats become available automatically because availability is derived from the reservations list.

### 5.4 Get Available Seats

1. Collect all seat IDs present in the showtime's reservations into a set.
2. Generate the standard seat layout: rows A–Z and seats 0–20.
3. Return seats that do not appear in the booked set.

The layout contains 546 seats, so generating and filtering it is inexpensive at this scale.

## 6. Concurrency — Most Important Interview Topic

### The Problem: Race Condition

Suppose two users try to book seat `A5` at the same time.

Without synchronization:

```text
Thread A checks A5 → available
Thread B checks A5 → available
Thread A books A5
Thread B books A5
```

Both users could succeed, resulting in double booking.

### Solution: Per-Showtime Lock

Synchronize the **availability check and reservation insertion as one atomic operation**.

```text
book(reservation):
    synchronized(this):
        validate all seat IDs

        for each seatId:
            if not isAvailable(seatId):
                throw SeatUnavailableException

        reservations.add(reservation)
```

Because only one thread can enter the synchronized section for that showtime at a time, the second thread checks availability after the first booking has completed.

### Why Validate Every Seat Before Inserting?

Suppose a user requests `["A5", "A6", "A7"]`, but `A6` is already booked.

The system must reject the entire request. It must not reserve `A5` and `A7` while failing on `A6`.

This is **all-or-nothing booking**, achieved by validating all seats before inserting the reservation.

### Per-Showtime Lock vs. Per-Seat Lock

| Per-Showtime Lock | Per-Seat Lock |
|---|---|
| Simpler implementation | More complex implementation |
| Serializes booking operations for one showtime | Allows bookings of different seats to proceed in parallel |
| Easier to reason about; avoids multi-lock deadlocks | Requires careful lock ordering to avoid deadlocks |
| Good default for interview scope | Useful when high contention justifies the complexity |

**Recommended interview choice:** Start with a per-showtime lock. Discuss per-seat locking only if throughput requirements justify the extra complexity.

Cancellation must use the same showtime lock so booking and cancellation cannot modify the reservation list concurrently.

## 7. OOP Principles and Design Patterns

### Object-Oriented Design Principles

| Principle | Application |
|---|---|
| **Encapsulation** | `Showtime` controls access to booking state and owns the operations that modify it. |
| **Single Responsibility Principle (SRP)** | `BookingSystem` orchestrates; `Theater` manages showtimes; `Movie` stores movie identity; `Showtime` owns booking state; `Reservation` records booking details. |
| **Composition** | A theater contains showtimes; a showtime references a movie and contains reservations. |
| **Immutability** | Movie details are read-only; reservation seat lists use defensive copies. |
| **Single Source of Truth** | The reservations list determines which seats are booked. |
| **Atomicity** | Multi-seat booking either succeeds completely or makes no changes. |
| **Separation of Concerns** | Search and routing live in `BookingSystem`; seat-state changes live in `Showtime`. |

### Design Patterns

**1. No formal GoF pattern is required for the core design.**

The core design relies mainly on good object boundaries and encapsulation.

**2. Observer Pattern — Optional extension**

If a theater cancels a showtime, multiple listeners may need to notify customers through email, SMS, or push notifications. An observer/event-based design can decouple notifications from booking logic.

**3. State Pattern — Optional extension**

If the system introduces seat states such as available, held, booked, and refunded, the State pattern may help manage increasingly complex transitions. It is unnecessary for the basic requirements.

**4. Strategy Pattern — Optional extension**

If temporary seat-hold durations vary by demand or business policy, a strategy interface can encapsulate the hold-duration calculation.

## 8. Edge Cases to Handle

- Empty or null movie search.
- No matching movies or future showtimes.
- Null theater input.
- Unknown showtime ID.
- Empty seat list.
- Invalid seat IDs, such as row `AA` or seat number `21`.
- One or more requested seats already booked.
- Duplicate seat IDs within the same booking request.
- Concurrent attempts to book the same seat.
- Unknown, empty, or already-cancelled confirmation ID.
- Booking fails: no reservation is stored in either the showtime or the booking-system index.
- Cancellation frees all seats associated with the reservation.
- Duplicate confirmation IDs must be prevented.
- A showtime should not be removed while active reservations exist unless cancellation is handled first.

**Important implementation detail:** Reject invalid requests before mutating state. Keep the booking and cancellation paths consistent across the showtime's reservation list and the booking system's reservation index.

## 9. Complexity Analysis

Let:
- \(M\) = number of distinct movies.
- \(S\) = number of showtimes associated with matching movies.
- \(R\) = number of reservations for a showtime.
- \(B\) = total seats booked for a showtime.

| Operation | Complexity | Explanation |
|---|---|---|
| Find showtime by ID | Average \(O(1)\) | Hash-map lookup |
| Find reservation by ID | Average \(O(1)\) | Hash-map lookup |
| Search movies | \(O(M + S)\) | Scan movie index and matching showtimes |
| Browse a theater | \(O(S_t)\) | Scan showtimes for that theater |
| Check one seat | \(O(B)\) | Scan reserved seat lists |
| Get available seats | \(O(B + 546)\) | Build booked set and scan fixed layout |
| Book seats | Depends on booked seats and requested seats | Validate availability and insert reservation under lock |
| Cancel reservation | \(O(R + B_r)\) in a list-based implementation | Find/remove reservation and account for seat-list copying where applicable |

Here, \(S_t\) is the number of showtimes at the selected theater, and \(B_r\) is the number of seats in the reservation being cancelled. Hash-map lookups are average-case, not guaranteed worst-case \(O(1)\).

The per-showtime lock can make concurrent requests wait, but it keeps the core booking logic simple and correct.

## 10. Interview Discussion and Extensions

### Temporary Seat Holds

Real booking systems often need to hold seats while a user completes checkout.

Introduce a `SeatHold` entity:

```text
class SeatHold:
    - holdId: String
    - seatIds: List<String>
    - expiresAt: Timestamp
```

`Showtime` would then track both confirmed reservations and active holds.

Additional methods:

```text
+ holdSeats(seatIds, timeout): String
+ confirmHold(holdId, reservation): void
+ cleanupExpiredHolds(): void
```

The booking flow becomes:

1. User selects seats.
2. System atomically checks availability and creates a temporary hold.
3. User completes checkout.
4. A valid hold converts into a confirmed reservation.
5. Expired or abandoned holds release the seats.

All operations that change seat state must coordinate under the same showtime lock. Expired holds must not block seats indefinitely.

### Dynamic Showtimes

The current indexes are initialized from existing theaters and showtimes. If new showtimes can be added later, every affected index must be updated consistently.

Removing a showtime requires additional care: reject removal if active reservations exist, or explicitly handle cancellation and customer notification.

### Production Consideration

An in-memory synchronized implementation protects threads within one process. A real ticketing service running multiple application instances needs a shared, durable concurrency mechanism—such as database transactions with appropriate locking or uniqueness constraints—to prevent double booking across instances.

## 11. Recommended Interview Flow

1. **Clarify requirements:** Multiple theaters, fixed seat layout, multi-seat booking, cancellation, and concurrency.
2. **Identify entities:** `BookingSystem`, `Theater`, `Movie`, `Showtime`, and `Reservation`.
3. **Define ownership:** `BookingSystem` orchestrates; `Showtime` owns seat availability and reservation state.
4. **Draw class relationships:** Explain why `Seat` and `Screen` can remain simple identifiers.
5. **Implement the core path:** Focus on `Showtime.book()` and `Showtime.cancel()`.
6. **Explain atomicity:** Validate all seats before inserting the reservation.
7. **Explain concurrency:** Demonstrate the race condition and per-showtime synchronization.
8. **Add indexes:** Explain efficient lookup by showtime ID and confirmation ID.
9. **Discuss trade-offs:** Per-showtime vs. per-seat locks, and deriving availability vs. maintaining a separate booked-seat set.
10. **Mention extensions:** Temporary holds, notifications, dynamic showtimes, and distributed concurrency.

## Key Takeaway

The most important design decision is that **`Showtime` owns both the reservation list and the atomic booking/cancellation operations**. This keeps seat state in one place, makes multi-seat bookings all-or-nothing, and gives the system a clear place to enforce concurrency correctness.
