import logging
from typing import NamedTuple, Optional

from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.webdriver import WebDriver

from shared.courses import CourseID
from shared.semester import Semester

log = logging.getLogger(__name__)


class SpireCourse(NamedTuple):
    id: CourseID
    title: str
    description: Optional[str]
    credits: Optional[str]
    enrollment_requirements: Optional[str]
    grading_basis: Optional[str]


class SpireSection(NamedTuple):
    course_id: CourseID
    section_id: str
    session: str
    enrolled: int
    enrollment_cap: int
    schedule: str
    location: str
    instructor: str


class SpireData(NamedTuple):
    courses: dict[CourseID, SpireCourse]
    sections: dict[Semester, dict[CourseID, SpireSection]]


def _navigate_to_catalog(driver: WebDriver):
    pass


def scrape_spire(course_ids: set[str], section_semesters: list[str], headless: bool) -> dict[str, SpireCourse]:
    log.info("Scraping course information from spire...")
    opts = Options()
    if headless:
        opts.headless = True

    driver = WebDriver(options=opts)

    log.info("")
    _navigate_to_catalog(driver)

    log.info("Scraped course information.")
