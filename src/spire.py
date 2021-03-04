import os

from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.errorhandler import NoSuchElementException, WebDriverException

from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.webdriver import WebDriver

import re

# SETTINGS

wait_time = 2

# CONSTANTS

category_list = [
    "CICS",
    "COMPSCI",
    "INFO",
    "MATH",
    "STATISTC",
]


def find(f, lst):
    for e in lst:
        if f(e):
            return e


def text_of(elem: WebElement):
    s = elem.text

    for r in ["\n", "\t", "  "]:
        s = s.replace(r, " ")

    return s.strip()


def create_driver() -> WebDriver:
    if os.environ.get('HEADLESS'):
        opts = Options()
        opts.headless = True

        return WebDriver(options=opts)

    return WebDriver()


def wait_until_not_processing(driver: WebDriver):
    while True:
        try:
            WebDriverWait(driver, 60 * 2).until_not(
                EC.visibility_of_any_elements_located((By.ID, "processing"))
            )
            break
        except WebDriverException:
            print("Spire seems to be a little slow, you should try again later.")
            if os.environ.get("RETRY") != "TRUE":
                exit(-1)


def wait_for_element(driver: WebDriver, attrib: str, value: str) -> WebElement:
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((attrib, value))
        )
    except WebDriverException:
        print("Unable to wait for", attrib, value)
        exit(-1)

    return driver.find_element(attrib, value)


def wait_for_elements(driver: WebDriver, attrib: str, value: str) -> WebElement:
    found = None
    try:
        found = WebDriverWait(driver, 10).until(
            EC.visibility_of_all_elements_located((attrib, value))
        )
    except WebDriverException:
        print("Unable to wait for", attrib, value)
        exit(-1)

    return found


def click_element(driver: WebDriver, attrib: str, value: str) -> None:
    wait_for_element(driver, attrib, value)
    
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((attrib, value))
        ).click()
    except WebDriverException:
        print("Unable to click", attrib, value)

    driver.implicitly_wait(wait_time)


def click_spire_element(driver: WebDriver, attrib: str, value: str) -> None:
    click_element(driver, attrib, value)
    wait_until_not_processing(driver)


def navigate_to_catalog(driver: WebDriver):
    driver.get("https://www.spire.umass.edu/")
    click_element(driver, By.NAME, "CourseCatalogLink")
    click_element(driver, By.ID, "pthnavbca_UM_COURSE_GUIDES")
    click_element(driver, By.CSS_SELECTOR, "#crefli_HC_SSS_BROWSE_CATLG_GBL4 > a")


def find_all_with_id(driver: WebDriver, base_id):
    found = []

    i = 0
    while True:
        try:
            found.append(text_of(driver.find_element_by_id(base_id + str(i))))
        except NoSuchElementException:
            break
        i = i + 1

    return ", ".join(found)


def scrape_course_page(driver: WebDriver, course):
    wait_for_element(driver, By.ID, "ACE_DERIVED_SAA_CRS_GROUP1")
    attribs = [
        ("career", "SSR_CRSE_OFF_VW_ACAD_CAREER$"),
        ("units", "DERIVED_CRSECAT_UNITS_RANGE$"),
        ("gradingBasis", "SSR_CRSE_OFF_VW_GRADING_BASIS$"),
        ("components", "DERIVED_CRSECAT_DESCR$"),
        ("enrollmentRequirement", "DERIVED_CRSECAT_DESCR254A$"),
    ]
    for (attrib, elem_id) in attribs:
        text = find_all_with_id(driver, elem_id)
        if attrib == "gradingBasis":
            course[attrib] = text.replace("Grad Ltr Grading", "Graduate Letter Grading")
        elif len(text) > 0:
            course[attrib] = text


def scrape_additional_course_information(course_map):
    driver = create_driver()
    navigate_to_catalog(driver)

    frame = wait_for_element(driver, By.ID, "ptifrmtgtframe")
    driver.switch_to.frame(frame)

    current_letter = ""
    for category in category_list:
        category_letter = category[0]
        if current_letter != category_letter:
            click_spire_element(driver, By.ID, "DERIVED_SSS_BCC_SSR_ALPHANUM_" + category_letter)
            current_letter = category_letter

        category_link = find(
            lambda elem, cat=category: re.match(f"^{cat} - .+$", elem.text),
            wait_for_elements(driver, By.CSS_SELECTOR, "a.SSSHYPERLINKBOLD")
        )
        category_link_id = category_link.get_attribute("id")

        click_spire_element(driver, By.ID, category_link_id)

        course_table = wait_for_element(driver, By.CSS_SELECTOR, "table.PSLEVEL2GRID")

        def id_map(link_element, cat=category):
            return (cat + " " + text_of(link_element).upper(),
                    link_element.get_attribute("id"))

        course_link_id_list = list(map(
            id_map,
            course_table.find_elements_by_css_selector("td[align=center] > div > span > a")
        ))
        course_link_id_list = list(filter(
            lambda ids: ids[0] in course_map,
            course_link_id_list
        ))

        for (course_id, link_id) in course_link_id_list:
            click_spire_element(driver, By.ID, link_id)
            scrape_course_page(driver, course_map[course_id])
            click_spire_element(driver, By.ID, "DERIVED_SAA_CRS_RETURN_PB")

    driver.quit()
