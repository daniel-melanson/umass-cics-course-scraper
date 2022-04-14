from datetime import datetime
from typing import NamedTuple

from scraper.calendar import Semester, scrape_academic_schedule
from scraper.descriptions import CourseDescriptions, scrape_course_descriptions
from scraper.frequency import scrape_course_frequency
from scraper.spire import SpireCourse, scrape_spire_courses
from scraper.staff import Staff, scrape_staff


class ScrapeData(NamedTuple):
    semesters: list[Semester]
    course_frequency: dict[str, str]
    staff: list[Staff]
    descriptions: CourseDescriptions
    spire_courses: dict[str, SpireCourse]


class ScrapeResult(NamedTuple):
    version: int
    date: datetime
    data: ScrapeData


def scrape() -> ScrapeResult:
    course_descriptions = scrape_course_descriptions()
    return ScrapeResult(
        version=1,
        date=datetime.now(),
        data=ScrapeData(
            semesters=scrape_academic_schedule(),
            course_frequency=scrape_course_frequency(),
            staff=scrape_staff(),
            descriptions=course_descriptions,
            spire_courses=scrape_spire_courses(
                lambda x: x in course_descriptions.cics.courses or x in course_descriptions.math.courses
            ),
        ),
    )
