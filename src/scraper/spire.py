import logging
from enum import Enum
from tokenize import Name
from typing import NamedTuple, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from shared.courses import CourseID
from shared.semester import Semester

log = logging.getLogger(__name__)
driver: WebDriver = None


class SpireCourse(NamedTuple):
    id: CourseID
    title: str
    description: Optional[str]
    credits: Optional[str]
    enrollment_requirements: Optional[str]
    grading_basis: Optional[str]


class SpireInstructor(NamedTuple):
    name: str
    email: str


class SpireSection(NamedTuple):
    course_id: CourseID
    status: str
    section_id: str
    session: str
    enrolled: int
    enrollment_cap: int
    schedule: str
    location: str
    instructor: SpireInstructor


class SpireData(NamedTuple):
    courses: dict[CourseID, SpireCourse]
    sections: dict[Semester, dict[CourseID, SpireSection]]




def scrape_spire(headless: bool) -> SpireData:
    log.info("Scraping course information from spire...")

    data = SpireData({}, {})

    driver = WebDriver() if not headless else WebDriver(Options(headless=True))
    driver.get("https://www.spire.umass.edu")

    # navagate to course search page
    # for i in range 16
    #   select that semester in da list
    #   for each topic (MATH, CICS, CS)
    #       search for each held section of that topic

    # navagate to the course catalog

    log.info("Scraped course information.")
    return data
