# captures what the users have booked. and reads when we need to cancel later.
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Showtime import Showtime

class Reservation:
    def __init__(self, confirmation_id: str, showtime: "Showtime", seat_ids: list[str]):
        self._confirmation_id = confirmation_id
        self._showtime = showtime
        self._seat_ids = list(seat_ids)

    def get_confirmation_id(self) -> str:
        return self._confirmation_id

    def get_showtime(self) -> "Showtime":
        return self._showtime

    def get_seat_ids(self) -> list[str]:
        return list(self._seat_ids)
