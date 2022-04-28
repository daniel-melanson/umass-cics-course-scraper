from datetime import datetime
from typing import NamedTuple

from scraper.calendar import SemesterSchedule, scrape_academic_schedule
from scraper.descriptions import CourseDescriptions, scrape_course_descriptions
from scraper.frequency import scrape_course_frequency
from scraper.spire import SpireCourse, scrape_spire
from scraper.staff import Staff, scrape_staff

SCRAPE_VERSION = 1


class ScrapeData(NamedTuple):
    semester_schedule: list[SemesterSchedule]
    course_frequency: dict[str, str]
    staff: list[Staff]
    descriptions: CourseDescriptions
    spire_courses: dict[str, SpireCourse]


class ScrapeResult(NamedTuple):
    version: int
    date: datetime
    data: ScrapeData


def scrape(headless: bool) -> ScrapeResult:
    return ScrapeResult(
        version=SCRAPE_VERSION,
        date=datetime.now(),
        data=ScrapeData(
            semesters=scrape_academic_schedule(),
            course_frequency=scrape_course_frequency(),
            staff=scrape_staff(),
            descriptions=scrape_course_descriptions(),
            spire=scrape_spire(headless),
        ),
    )
