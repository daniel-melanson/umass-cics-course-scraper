import re

from shared.util import clean_text


SEASON_REGEXP = r"(Spring|Summer|Fall|Winter)"
YEAR_REGEXP = r"(20\d{2})$"
SEMESTER_REGEXP = f"^({SEASON_REGEXP} {YEAR_REGEXP})|({YEAR_REGEXP} {SEASON_REGEXP})$"


def match_semester(s: str):
    return re.match(SEMESTER_REGEXP, s)


def is_semester(s: str) -> bool:
    return match_semester(s) is not None


SEASON_LIST = ["Spring", "Summer", "Fall", "Winter"]


class Semester:
    @staticmethod
    def from_text(text: str) -> "Semester":
        semester_text = clean_text(text)

        match = match_semester(semester_text)
        assert match

        last_group = int(match.lastgroup)

        return Semester(match.group(last_group - 1), match.group(last_group))

    def __init__(self, season: str, year: str):
        assert re.match(r"^\d{4}$", year) is not None

        self._season = season
        self._year = year
        self._season_index = SEASON_LIST.index(season)

    def __eq__(self, __o: object) -> bool:
        assert isinstance(__o, Semester)
        return self.season == __o.season and self.year == __o.year

    def __ne__(self, __o: object) -> bool:
        assert isinstance(__o, Semester)
        return self.season != __o.season or self.year != __o.year

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
