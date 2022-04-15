import re

from shared.util import clean_text

SEMESTER_PATTERN = re.compile(r"^(Spring|Summer|Fall|Winter) 20\d{2}$")


def is_semester(s: str) -> bool:
    return SEMESTER_PATTERN.match(s) is not None


SEASON_LIST = ["Spring", "Summer", "Fall", "Winter"]


class Semester:
    @staticmethod
    def from_text(text: str) -> "Semester":
        semester_text = clean_text(text)

        assert is_semester(semester_text)

        [season, year] = semester_text.split(" ")
        return Semester(season, year)

    def __init__(self, season: str, year: int):
        assert 2000 < year < 2100
        assert season in SEASON_LIST

        self._season = season
        self._year = year
        self._season_index = SEASON_LIST.index(season)

    def __eq__(self, __o: object) -> bool:
        assert isinstance(__o, Semester)
        return self.season == __o.season and self.year == __o.year

    def __hash__(self) -> int:
        return hash(str(self))

    def __str__(self) -> str:
        return f"{self.season} {self.year}"

    def __lt__(self, __o: object) -> bool:
        assert isinstance(__o, Semester)
        return self.year < __o.year and self._season_index < __o._season_index

    def __gt__(self, __o: object) -> bool:
        assert isinstance(__o, Semester)
        return self.year > __o.year and self._season_index > __o._season_index

    def __le__(self, __o: object) -> bool:
        assert isinstance(__o, Semester)
        return self.__lt__(__o) or self.__eq__(__o)

    def __ge__(self, __o: object) -> bool:
        assert isinstance(__o, Semester)
        return self.__gt__(__o) or self.__eq__(__o)

    @property
    def season(self) -> str:
        return self._season

    @property
    def year(self) -> int:
        return self._year

    def next(self) -> "Semester":
        next_season_index = self._season_index + 1
        if next_season_index > len(SEASON_LIST):
            next_year = self._year + 1
        else:
            next_year = self._year

        return Semester(SEASON_LIST[next_season_index % len(SEASON_LIST)], next_year)

    def previous(self) -> "Semester":
        next_season_index = self._season_index - 1
        if next_season_index < 0:
            next_year = self._year - 1
        else:
            next_year = self._year

        return Semester(SEASON_LIST[next_season_index], next_year)

    def swapped_str(self) -> str:
        return f"{self.year} {self.season}"
