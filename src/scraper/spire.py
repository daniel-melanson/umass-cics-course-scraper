import logging
from typing import NamedTuple, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

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

class SearchCriteriaInput(NamedTuple):
    course_subject: str
    course_number: Tuple[Union[""]]

class SpireSearchCriteriaPage():
    def __str__(self) -> str:
        return "Search Criteria Page"

    def set_input(self):
        pass

    def scrape(self):
        pass

    def back(self):
        return self

class SpireDriver():
    def __init__(self, headless) -> None:
        options = Options()
        if headless:
            options.headless = True

        self._driver = WebDriver()
        self._wait = WebDriverWait(self._driver, 60)

        self._driver.get("https://www.spire.umass.edu")

        self._wait.until(EC.element_to_be_clickable((By.NAME, "CourseCatalogLink"))).click()

        frame = self.wait_for_presence(By.ID, "ptifrmtgtframe")
        self._driver.switch_to.frame(frame)

        self._state = SpireSearchCriteriaPage()

    def wait_for_presence(self, by: By, selector: str):
        log.debug("Wating for presence of element by locator %s:%s", by, selector)
        return self._wait.until(EC.presence_of_element_located((by, selector)))

    def wait_for_spire(self) -> None:
        log.debug("Waiting for spire...")
        self._wait.until_not(EC.visibility_of_any_elements_located((By.ID, "processing")))

    def navagate_back(self) -> None:
        log.debug("Navagating back from %s...", self._state)
        state = self._state.navagate_back()
        self.wait_for_spire()
        log.debug("Transitioned from %s to %s", self._state, state)
        self._state = state

    def close(self) -> None:
        self._driver.close()


def scrape_spire(headless: bool) -> SpireData:
    log.info("Scraping course information from spire...")

    data = SpireData({}, {})

    driver = SpireDriver(headless)

    # navagate to course search page
    # for i in range 16
    #   select that semester in da list
    #   for each topic (MATH, CICS, CS)
    #       search for each held section of that topic

    # navagate to the course catalog

    driver.close()

    log.info("Scraped course information.")
    return data
