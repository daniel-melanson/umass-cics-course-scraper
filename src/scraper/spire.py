from typing import TypedDict
import logging

from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.webdriver import WebDriver

from scraper.web import RawCourse

log = logging.getLogger(__name__)

CATEGORY_LIST = [
    "CICS",
    "COMPSCI",
    "INFO",
    "MATH",
    "STATISTC",
]


def _create_driver(headless: bool) -> WebDriver:
    if headless:
        opts = Options()
        opts.headless = True

        return WebDriver(options=opts)

    return WebDriver()


def scrape_supplemental_info(courses: dict[str, RawCourse], headless: bool):
    log.info("Scraping additional course information from spire...")
    driver = _create_driver(headless)

    log.info("Scraped additional course information.")
