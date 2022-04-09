from typing import NamedTuple, Tuple

from scraper.calendar import Semester, scrape_academic_schedule
from scraper.web import scrape_course_frequency, scrape_raw_staff_list
from scraper.spire import scrape_course_list


class RawCourse(NamedTuple):
    id: str


class RawStaff(NamedTuple):
    names: list[str]


def scrape_raw_info() -> Tuple[RawCourse, RawStaff, list[Semester]]:
    course_frequency = scrape_course_frequency()
    coruse_list = scrape_course_list()

    return (None, scrape_raw_staff_list(), scrape_academic_schedule())
