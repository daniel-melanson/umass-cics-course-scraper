import logging

from bs4 import Tag

from scraper.shared import fetch_soup, get_tag_text

log = logging.getLogger(__name__)


def scrape_course_frequency() -> dict[str, str]:
    log.info("Scraping course frequency...")
    soup = fetch_soup("https://web.cs.umass.edu/csinfo/autogen/cmpscicoursesfull.html")

    def cics_course_frequency(tag: Tag):
        course_subject = get_tag_text(tag.select_one("td:first-child"))
        course_id = get_tag_text(tag.select_one("td:nth-child(2)"))
        return (f"{course_subject} {course_id}".upper(), get_tag_text(tag.select_one("td:last-child")))

    def math_course_frequency(elem: Tag):
        freq = get_tag_text(elem.select_one("td:last-child"))
        if freq == "Fall/Spring/Summer":
            freq = "Fall, Spring, and Summer"
        else:
            freq = freq.replace("/", " and ").replace("  ", " ")

        return (get_tag_text(elem.select_one("td:first-child")).upper(), freq)

    course_frequency = {}
    for (url, selector, scraper) in [
        (
            "https://web.cs.umass.edu/csinfo/autogen/cmpscicoursesfull.html",
            "tbody > tr:not(:first-child)",
            cics_course_frequency,
        ),
        ("https://www.math.umass.edu/course-offerings", "tbody > tr", math_course_frequency),
    ]:
        soup = fetch_soup(url)
        tag_list = soup.select(selector)

        for tag in tag_list:
            (course_id, course_freq) = scraper(tag)
            log.debug("Scraped course frequency: %s - %s", course_id, course_freq)
            course_frequency[course_id] = course_freq

    log.info("Scraped course frequency.")
    return course_frequency
