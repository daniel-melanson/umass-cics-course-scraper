from typing import Tuple

from scraper.calendar import Semester, scrape_academic_schedule
from scraper.web import RawStaff, scrape_raw_staff_list, scrape_courses
from scraper.spire import RawCourse, scrape_supplemental_info


def scrape_raw_info() -> Tuple[RawCourse, RawStaff, list[Semester]]:
    courses = scrape_courses()

    scrape_supplemental_info(courses)

    return (courses, scrape_raw_staff_list(), scrape_academic_schedule())
