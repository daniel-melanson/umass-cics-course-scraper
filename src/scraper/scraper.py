from typing import NamedTuple, Tuple, Union

from scraper.calendar import Semester

class RawCourse(NamedTuple):
    id: str


class RawStaff(NamedTuple):
    names: list[str]


def scrape_raw_info() -> Union[Tuple[RawCourse, RawStaff, Semester], None]:
    return None
