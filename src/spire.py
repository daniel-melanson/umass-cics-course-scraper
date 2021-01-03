from selenium import webdriver
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.errorhandler import NoSuchElementException

from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.webdriver import WebDriver

from time import sleep

import re

# SETTINGS

debug = True
headless = True
wait_time = 2

# END OF SETTINGS
# CONSTANTS

category_list = [
    'CICS',
    'COMPSCI',
    'INFO',
    'MATH',
    'STATISTC',
]

# END OF CONSTANTS


def find(f, list):
    for e in list:
        if f(e):
            return e


def text_of(elem: WebElement):
    s = elem.text

    for r in ['\n', '\t', '  ']:
        s = s.replace(r, ' ')

    return s.strip()


def create_driver() -> WebDriver:
    if headless:
        opts = Options()
        opts.headless = True

        return WebDriver(options=opts)
    else:
        return WebDriver()


def wait_for_element(driver: WebDriver, attrib: str, value: str) -> WebElement:
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((attrib, value))
        )
    except e:
        print(e)
        driver.quit()

    return driver.find_element(attrib, value)


def click_element(driver: WebDriver, attrib: str, value: str) -> None:
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((attrib, value))
        )
    except e:
        print(e)
        driver.quit()

    driver.find_element(attrib, value).click()
    if debug:
        sleep(wait_time)


def navigate_to_catalog(driver: WebDriver):
    driver.get('https://www.spire.umass.edu/')
    click_element(
        driver,
        By.NAME,
        'CourseCatalogLink'
    )
    click_element(driver, By.ID, 'pthnavbca_UM_COURSE_GUIDES')
    click_element(
        driver,
        By.CSS_SELECTOR,
        "#crefli_HC_SSS_BROWSE_CATLG_GBL4 > a"
    )


def find_all_with_id(driver: WebDriver, base_id):
    found = []

    i = 0
    while True:
        try:
            found.append(text_of(driver.find_element_by_id(base_id + str(i))))
        except NoSuchElementException:
            break
        i = i + 1

    return ', '.join(found)


def scrape_course_page(driver: WebDriver, course):
    wait_for_element(driver, By.ID, 'ACE_DERIVED_SAA_CRS_GROUP1')
    attribs = [
        ('career', 'SSR_CRSE_OFF_VW_ACAD_CAREER$'),
        ('units', 'DERIVED_CRSECAT_UNITS_RANGE$'),
        ('gradingBasis', 'SSR_CRSE_OFF_VW_GRADING_BASIS$'),
        ('components', 'DERIVED_CRSECAT_DESCR$'),
        ('enrollmentRequirement', 'DERIVED_CRSECAT_DESCR254A$'),
    ]
    for (attrib, id) in attribs:
        text = find_all_with_id(driver, id)
        if attrib == 'gradingBasis':
            course[attrib] = text.replace(
                'Grad Ltr Grading',
                'Graduate Letter Grading'
            )
        elif len(text) > 0:
            course[attrib] = text


def scrape_additional_course_information(course_map):
    driver = create_driver()
    navigate_to_catalog(driver)

    frame = wait_for_element(driver, By.ID, 'ptifrmtgtframe')
    driver.switch_to.frame(frame)

    current_letter = ''
    for category in category_list:
        category_letter = category[0]
        if current_letter != category_letter:
            click_element(
                driver,
                By.ID,
                'DERIVED_SSS_BCC_SSR_ALPHANUM_' + category_letter
            )
            current_letter = category_letter

        category_link_list = driver.find_elements_by_css_selector(
            'a.SSSHYPERLINKBOLD'
        )
        category_link = find(
            lambda elem: re.match(f'^{category} - .+$', elem.text),
            category_link_list
        )
        category_link_id = category_link.get_attribute('id')

        click_element(driver, By.ID, category_link_id)

        course_table = wait_for_element(driver, By.CLASS_NAME, 'PSLEVEL2GRID')

        def id_map(link_element):
            return (category + ' ' + text_of(link_element).upper(),
                    link_element.get_attribute('id'))

        course_link_id_list = list(map(
            id_map,
            course_table.find_elements_by_css_selector(
                'td[align=center] > div > span > a'
            )
        ))
        course_link_id_list = list(filter(
            lambda ids: ids[0] in course_map,
            course_link_id_list
        ))

        for (course_id, link_id) in course_link_id_list:
            click_element(driver, By.ID, link_id)
            scrape_course_page(driver, course_map[course_id])
            click_element(driver, By.ID, 'DERIVED_SAA_CRS_RETURN_PB')

        click_element(driver, By.ID, category_link_id)

    driver.close()
