import logging
from typing import Optional, TypedDict

from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.webdriver import WebDriver

log = logging.getLogger(__name__)


class SpireCourse(TypedDict):
    id: str
    title: str
    description: Optional[str]
    credits: Optional[str]
    enrollment_requirements: Optional[str]
    grading_basis: Optional[str]


def _create_driver(headless: bool) -> WebDriver:
    if headless:
        opts = Options()
        opts.headless = True

        return WebDriver(options=opts)

    return WebDriver()


def scrape_spire_courses(filter, headless: bool) -> dict[str, SpireCourse]:
    log.info("Scraping additional course information from spire...")
    driver = _create_driver(headless)

    log.info("Scraped additional course information.")
