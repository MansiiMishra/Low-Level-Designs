# this is just a container for all the shows. 
# getshowtimesformovie returns the showtimes for the given movie title.
# getshowtimes returns the showtimes for the given movie title and theater.

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Movie import Movie
    from Showtime import Showtime

class Theater:
    def __init__(self, theater_id: str, name: str):
        self._id = theater_id
        self._name = name
        self._showtimes: list["Showtime"] = []

    def get_id(self) -> str:
        return self._id

    def get_name(self) -> str:
        return self._name

    def get_showtimes(self) -> list["Showtime"]:
        return self._showtimes

    def get_showtimes_for_movie(self, movie: "Movie") -> list["Showtime"]:
        results = []
        for showtime in self._showtimes:
            if showtime.get_movie().get_id() == movie.get_id():
                results.append(showtime)
        return results
