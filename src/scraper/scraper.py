from typing import NamedTuple, Tuple, Union

from scraper.calendar import Semester, scrape_academic_schedule
from scraper.cics import scrape_raw_staff_list


class RawCourse(NamedTuple):
    id: str


class RawStaff(NamedTuple):
    names: list[str]


def scrape_raw_info() -> Tuple[RawCourse, RawStaff, list[Semester]]:
    return (None, scrape_raw_staff_list(), None)
