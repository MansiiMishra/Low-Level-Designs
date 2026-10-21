# thsi is responsible for the user facing operations
# allows to search movies, find the showtimes at the theater allow to book and cancel the tickets
# search movies does a case insenitive search and returns movuie titles against the showtimes
# the getShowtimesAtTheater returns the showtimes for the given theater
# book creates a revervation for the given showtime and seats and returns a confirmation id --> This is atomic.
# lastly cancel reservvation cancels the reservation for the given confirmation id.


import uuid
from datetime import datetime
from Movie import Movie
from Reservations import Reservation
from Showtime import Showtime
from Theater import Theater


class BookingSystem:
    def __init__(self, theaters: list["Theater"]):
        self._theaters = theaters
        self._movies_by_id: dict[str, "Movie"] = {}
        self._showtimes_by_movie_id: dict[str, list["Showtime"]] = {}
        self._showtimes_by_id: dict[str, "Showtime"] = {}
        self._reservations_by_id: dict[str, "Reservation"] = {}

        for theater in theaters:
            for showtime in theater.get_showtimes():
                movie = showtime.get_movie()
                self._movies_by_id[movie.get_id()] = movie
                self._showtimes_by_id[showtime.get_id()] = showtime

                if movie.get_id() not in self._showtimes_by_movie_id:
                    self._showtimes_by_movie_id[movie.get_id()] = []
                self._showtimes_by_movie_id[movie.get_id()].append(showtime)

    def search_movies(self, title: str) -> list["Showtime"]:
        if not title:
            return []

        results: list["Showtime"] = []
        search_lower = title.lower()
        now = datetime.now()

        for movie in self._movies_by_id.values():
            if search_lower in movie.get_title().lower():
                movie_showtimes = self._showtimes_by_movie_id.get(movie.get_id(), [])
                for showtime in movie_showtimes:
                    if showtime.get_datetime() > now:
                        results.append(showtime)

        return results

    def get_showtimes_at_theater(self, theater: "Theater") -> list["Showtime"]:
        if theater is None:
            return []

        results: list["Showtime"] = []
        now = datetime.now()

        for showtime in theater.get_showtimes():
            if showtime.get_datetime() > now:
                results.append(showtime)

        return results

    def book(self, showtime_id: str, seat_ids: list[str]) -> "Reservation":
        if not showtime_id or not seat_ids:
            raise ValueError("Invalid booking request")

        showtime = self._showtimes_by_id.get(showtime_id)
        if showtime is None:
            raise ValueError(f"Showtime not found: {showtime_id}")

        reservation = Reservation(
            str(uuid.uuid4()),
            showtime,
            seat_ids,
        )

        showtime.book(reservation)

        self._reservations_by_id[reservation.get_confirmation_id()] = reservation

        return reservation

    def cancel_reservation(self, confirmation_id: str) -> None:
        if not confirmation_id:
            raise ValueError("Invalid confirmation ID")

        reservation = self._reservations_by_id.get(confirmation_id)
        if reservation is None:
            raise ValueError(f"Reservation not found: {confirmation_id}")

        showtime = reservation.get_showtime()
        showtime.cancel(reservation)

        del self._reservations_by_id[confirmation_id]
