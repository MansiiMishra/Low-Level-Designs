# this handles the main part, the concurrent booking.
# this hsould be able to show avilable seats of this showtime.
# book seats, multiple seats in single reservation.
# cancel reservation and release the seats back to the showtime.

import threading
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Movie import Movie
    from Reservations import Reservation
    from Theater import Theater


class Showtime:
    def __init__(self, showtime_id: str, theater: "Theater", movie: "Movie", dt: datetime, screen_label: str):
        self._id = showtime_id
        self._theater = theater
        self._movie = movie
        self._datetime = dt
        self._screen_label = screen_label
        self._reservations: list["Reservation"] = []
        self._lock = threading.RLock()

    def get_id(self) -> str:
        return self._id

    def get_theater(self) -> "Theater":
        return self._theater

    def get_datetime(self) -> datetime:
        return self._datetime

    def get_movie(self) -> "Movie":
        return self._movie

    def is_available(self, seat_id: str) -> bool:
        for reservation in self._reservations:
            if seat_id in reservation.get_seat_ids():
                return False
        return True

    def get_available_seats(self) -> list[str]:
        booked: set[str] = set()
        for reservation in self._reservations:
            for seat in reservation.get_seat_ids():
                booked.add(seat)

        available: list[str] = []
        for row in range(ord("A"), ord("Z") + 1):
            for num in range(21):
                seat_id = chr(row) + str(num)
                if seat_id not in booked:
                    available.append(seat_id)
        return available

    def book(self, reservation: "Reservation") -> None:
        with self._lock:
            seat_ids = reservation.get_seat_ids()

            if not seat_ids:
                raise ValueError("Must select at least one seat")

            for seat_id in seat_ids:
                if not self._is_valid_seat_id(seat_id):
                    raise ValueError(f"Invalid seat: {seat_id}")

            for seat_id in seat_ids:
                if not self.is_available(seat_id):
                    raise ValueError(f"Seat {seat_id} is not available")

            self._reservations.append(reservation)

    def cancel(self, reservation: "Reservation") -> None:
        with self._lock:
            self._reservations.remove(reservation)

    @staticmethod
    def _is_valid_seat_id(seat_id: str) -> bool:
        if not seat_id or len(seat_id) < 2:
            return False
        row = seat_id[0]
        try:
            num = int(seat_id[1:])
            return "A" <= row <= "Z" and 0 <= num <= 20
        except ValueError:
            return False
