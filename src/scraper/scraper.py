from typing import Tuple

from scraper.calendar import Semester, scrape_academic_schedule
from scraper.web import RawStaff, scrape_course_frequency, scrape_raw_staff_list
from scraper.spire import RawCourse, scrape_course_list


def scrape_raw_info() -> Tuple[RawCourse, RawStaff, list[Semester]]:
    course_frequency = scrape_course_frequency()
    course_list = scrape_course_list()

    for course in course_list:
        course_id = course["id"]

        if freq := course_frequency[course_id]:
            course["frequency"] = freq

    return (course_list, scrape_raw_staff_list(), scrape_academic_schedule())
