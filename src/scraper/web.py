from datetime import datetime
import logging
import re
from typing import NamedTuple, Optional, TypedDict
from requests.exceptions import HTTPError

from bs4 import Tag

from scraper.shared import fetch_soup, get_tag_text

log = logging.getLogger(__name__)

REGEXP_NAME_GROUP = (
    "[a-zA-ZàáâäãåąčćęèéêëėįìíîïłńòóôöõøùúûüųūÿýżźñçčšžÀÁÂÄÃÅĄĆČĖĘÈÉÊËÌÍÎÏĮŁŃÒÓÔÖÕØÙÚÛÜŲŪŸÝŻŹÑßÇŒÆČŠŽ∂ð ,.'-]+"
)


class RawStaff(TypedDict):
    names: set[str]
    title: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    office: Optional[str]
    website: Optional[str]
    photo: Optional[str]


class CourseFrequency(NamedTuple):
    id: str
    frequency: str


class RawCourse(TypedDict):
    id: str
    subject: str
    number: str
    title: str
    most_recent_offering: str
    past_offerings: list[str]
    description: str
    semester_staff: dict[str, str]
    frequency: Optional[str]
    credits: Optional[str]
    prerequisites: Optional[str]


def scrape_courses() -> dict[str, RawCourse]:
    log.info("Scraping initial course data...")
    courses: dict[str, RawCourse] = {}

    _scrape_cics_courses(courses)
    _scrape_math_courses(courses)

    for (course_id, frequency) in _scrape_course_frequency():
        if course_id in courses:
            course = courses[course_id]
            course["frequency"] = frequency

    log.info("Scraped initial course data.")
    return courses


def _scrape_cics_courses(courses: dict[str, RawCourse]):
    log.info("Scraping CICS courses...")

    current_year = int(datetime.now().year) % 2000 + 1
    for year in range(current_year, 17, -1):
        for query_id in [7, 3]:
            season = "Fall" if query_id == 7 else "Spring"
            semester = f"{season} {2000 + year}"
            log.debug("Scraping CICS courses for %s...", semester)

            try:
                soup = fetch_soup(
                    f"https://web.cs.umass.edu/csinfo/autogen/cicsdesc1{year}{query_id}.html", retry=False
                )
            except HTTPError:
                log.debug("Descriptions not available, skipping semester.")
                continue

            for header in soup.select("h2:not(:first-child)"):
                raw_title = get_tag_text(header.select_one(":first-child"))
                assert raw_title

                log.debug("Matching course header: %s", raw_title)
                title_match = re.match(r"^(CICS|COMPSCI|INFO(SEC)?)\s*(\w+):\s*([\w -:]+)", raw_title, re.I)
                assert title_match
                log.debug("Matched: %s", title_match)

                course_subject = title_match.group(1).upper()
                if course_subject == "INFOSEC":
                    log.debug("Skipping due to INFOSEC subject.")
                    continue

                course_number = title_match.group(3).upper()
                course_id = course_subject + " " + course_number
                log.debug("Scraping course: %s", course_id)

                if course_id in courses:
                    log.debug("Found past entry.")
                    course = courses[course_id]

                    course["past_offerings"].append(semester)
                else:
                    log.debug("Initalizing new course dictionary...")
                    paragraph = header.find_next_sibling("p")
                    assert paragraph

                    course_description = get_tag_text(paragraph)

                    course = RawCourse(
                        id=course_id,
                        subject=course_subject,
                        number=course_number,
                        title=title_match.group(4),
                        description=course_description,
                        most_recent_offering=semester,
                        past_offerings=[],
                        semester_staff={},
                    )

                    course_website = header.select_one("a")
                    if course_website:
                        course["website"] = course_website.attrs["href"]

                    courses[course_id] = course

                next_sibling = header.next_sibling.next_sibling
                if next_sibling.name == "h3":
                    instructor_text = get_tag_text(next_sibling)
                    log.debug("Matching instructor header: %s", instructor_text)

                    instructor_match = re.match(r"^(Instructor\(s\): )(.+)", instructor_text, re.I)
                    assert instructor_match

                    raw_instructors = instructor_match.group(2).strip()
                    log.debug("Matched, got: %s", raw_instructors)
                    course["semester_staff"] |= {semester: raw_instructors}

                log.debug("Finished updating: %s", course)

            log.debug("Scraped CICS courses for %s", semester)

    log.info("Scraped CICS courses.")


def _scrape_math_courses(courses: dict[str, RawCourse]):
    log.info("Scraping mathematics courses...")

    soup = fetch_soup("https://www.math.umass.edu/course-descriptions")
    first_option = soup.select_one("#edit-semester-tid > option[selected='selected']")

    start = int(first_option.attrs['value'])
    log.debug("Starting from semester id: %s", start)

    for i in range(start + 1, start - 10, -1):
        log.debug("Found semester id: %s", i)
        soup = fetch_soup(f"https://www.math.umass.edu/course-descriptions?semester_tid={i}")

        articles = soup.select("div.views-row > article")
        if len(articles) == 0:
            log.debug("No articles found, skipping.")
            continue

        selected_option = soup.select_one("#edit-semester-tid > option[selected='selected']")
        assert selected_option

        semester = get_tag_text(selected_option)

        log.debug("Scraping mathematics courses for %s...", semester)
        for article in articles:
            title_tag = article.select_one("div[class^='field-title']")
            assert title_tag

            raw_title = get_tag_text(title_tag)

            log.debug("Matching title: %s", raw_title)
            title_match = re.match(
                r'^(MATH|STAT|HONORS)\s*(\w+)(\.\d*)?:\s*([\w -:]+)',
                raw_title,
                re.I
            )
            assert title_match
            log.debug("Matched: %s", title_match)

            if title_match.group(1) == 'HONORS':
                log.debug("Skipping due to HONORS subject.")
                continue

            course_subject = title_match.group(1).upper()
            if course_subject == 'STAT':
                course_subject = 'STATISTIC'

            course_number = title_match.group(2).upper()
            course_id = course_subject + ' ' + course_number

            log.debug("Scraping course: %s", course_id)
            if course_id in courses:
                log.debug("Found past entry.")
                course = courses[course_id]

                if semester != course["most_recent_offering"]:
                    log.debug("Adding %s to past offerings.", semester)
                    course["past_offerings"].append(semester)
            else:
                log.debug("No past entry found. Aggregating information...")
                course_title = title_match.group(4)
                description_tag = article.select_one("div[class^='field-course-descr-description']")
                assert description_tag

                course_description = get_tag_text(description_tag)

                course = RawCourse(
                    subject=course_subject,
                    id=course_id,
                    number=course_number,
                    title=course_title,
                    description=course_description,
                    most_recent_offering=semester,
                    past_offerings=[],
                    semester_staff={},
                )

                course_prereqs = article.select_one(
                    "div[class^='field-course-descr-prereq']"
                )
                if course_prereqs:
                    course["prerequisites"] = get_tag_text(course_prereqs)
                    log.debug("Found prerequisites tag: %s", course["prerequisites"])

                log.debug("Initalized course: %s", course)
                courses[course_id] = course

        log.debug("Scraped mathematics courses for %s.", semester)

    log.info("Scraped mathematics courses.")


def _scrape_course_frequency() -> list[CourseFrequency]:
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

    course_frequency = []
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
            course_frequency.append((course_id, course_freq))

    log.info("Scraped course frequency.")
    return course_frequency


def scrape_raw_staff_list() -> list[RawStaff]:
    log.info("Scraping staff list...")
    soup = fetch_soup("https://www.cics.umass.edu/people/all-faculty-staff")

    staff_list = []
    for staff_div in soup.select("div.view-faculty-directory > div.view-content > div > div.views-row"):
        name_link = staff_div.select_one("div.views-field-title > span > a")
        assert name_link

        raw_name = get_tag_text(name_link)
        log.debug("Matching staff name: %s", raw_name)
        name_match = re.match(f"^({REGEXP_NAME_GROUP}),\s*({REGEXP_NAME_GROUP})", raw_name)
        assert name_match

        staff = RawStaff(names=set([f"{name_match.group(2)} {name_match.group(1)}"]))

        log.debug("Initalized staff member %s.", staff)
        attributes = [
            ("title", "position", 0),
            ("email", "email", 3),
            ("phone", "phone", 3),
            ("office", "location", 3),
        ]

        for (attribute, selector, offset) in attributes:
            tag = staff_div.select_one(f"div.views-field-field-{selector}")

            if tag:
                raw_text = get_tag_text(tag)
                staff[attribute] = raw_text[offset:]
                log.debug("Scraped '%s' for staff %s.", staff[attribute], attribute)
            else:
                log.debug("No tag found for %s, skipping.", attribute)

        if (href := name_link.attrs["href"]).startswith("/"):
            log.debug("Scraping supplemental information from %s.", href)
            staff["website"] = "https://www.cics.umass.edu" + href

            staff_website_soup = fetch_soup(staff["website"])
            header = staff_website_soup.select_one("#page-title")
            staff["names"].add(get_tag_text(header))

            img_tag = staff_website_soup.select_one("div.headshot-wrapper > img")
            if img_tag and img_tag.attrs["src"]:
                staff["photo"] = img_tag.attrs["src"]
        else:
            log.debug("Offsite url, skipping supplemental scrape process.")

        log.debug("Adding staff member %s.", staff)
        staff_list.append(staff)

    log.info("Scraped staff information.")
    return staff_list
