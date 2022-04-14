import logging
import re
from datetime import datetime
from typing import NamedTuple, Optional, TypedDict, TypeVar, Union

from scraper.shared import fetch, fetch_soup, get_soup, get_tag_text

log = logging.getLogger(__name__)


class CICSCourse(NamedTuple):
    id: str
    subject: str
    number: str
    title: str
    offerings: list[str]
    description: str
    semester_staff: dict[str, str]
    semester_websites: dict[str, str]


class MATHCourse(NamedTuple):
    id: str
    subject: str
    number: str
    title: str
    offerings: list[str]
    description: str
    semester_staff: dict[str, str]
    prerequisites: Optional[str]
    chair: Optional[str]
    semester_websites: dict[str, str]


T = TypeVar("T", MATHCourse, CICSCourse)


class DescriptionsPosting(NamedTuple):
    most_recent_semester: str
    courses: dict[str, Union[CICSCourse, MATHCourse]]


class CourseDescriptions(NamedTuple):
    math: DescriptionsPosting
    cics: DescriptionsPosting


def scrape_course_descriptions() -> CourseDescriptions:
    return CourseDescriptions(None, _scrape_math_courses())


def _scrape_cics_courses() -> DescriptionsPosting[CICSCourse]:
    log.info("Scraping CICS courses...")

    most_recent_semester = None
    courses: dict[str, CICSCourse] = {}

    current_year = int(datetime.now().year) % 2000 + 1
    for year in range(current_year, 17, -1):
        for query_id in [7, 3]:
            season = "Fall" if query_id == 7 else "Spring"
            semester = f"{season} {2000 + year}"
            log.debug("Scraping CICS courses for %s...", semester)

            res = fetch(f"https://web.cs.umass.edu/csinfo/autogen/cicsdesc1{year}{query_id}.html")

            if res.status_code != 200:
                log.debug("Descriptions not avaliable, skipping semester.")
                continue

            if most_recent_semester is None:
                most_recent_semester = semester

            soup = get_soup(res)
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
                    log.debug("Found past entry, reusing tuple.")
                    course = courses[course_id]
                else:
                    log.debug("Initalizing new course dictionary...")
                    paragraph = header.find_next_sibling("p")
                    assert paragraph

                    course_description = get_tag_text(paragraph)

                    course = CICSCourse(
                        id=course_id,
                        subject=course_subject,
                        number=course_number,
                        title=title_match.group(4),
                        description=course_description,
                        offerings=[],
                        semester_staff={},
                        semester_websites={},
                    )

                    courses[course_id] = course

                course.offerings.append(semester)

                course_website = header.select_one("a")
                if course_website:
                    course.semester_websites[semester] = course_website.attrs["href"]

                next_sibling = header.next_sibling.next_sibling
                if next_sibling.name == "h3":
                    raw_instructors = get_tag_text(next_sibling)
                    log.debug("Matching instructor header: %s", raw_instructors)

                    instructor_match = re.match(r"^(Instructor\(s\): )(.+)", raw_instructors, re.I)
                    assert instructor_match

                    instructors_text = instructor_match.group(2).strip()
                    log.debug("Matched, got: %s", instructors_text)
                    course.semester_staff[semester] = instructors_text

                log.debug("Finished updating: %s", course)

            log.debug("Scraped CICS courses for %s", semester)

    log.info("Scraped CICS courses.")
    return DescriptionsPosting(most_recent_semester, courses)


def _scrape_math_courses() -> DescriptionsPosting[MATHCourse]:
    log.info("Scraping mathematics courses...")

    log.info("Scraping supplementary information...")

    supplementary_info = {}

    soup = fetch_soup("https://www.math.umass.edu/course-webpages")
    page_title = soup.select_one("#page-title")
    assert page_title

    title_text = get_tag_text(page_title)
    log.debug("Matching title: %s", title_text)
    title_match = re.search(r"(Spring|Fall)\s+(\d{4})$", title_text)
    assert title_match

    info_semester = f"{title_match.group(1)} {title_match.group(2)}"

    for section_group in soup.select("div.view-content > div.views-row"):
        section_entry = section_group.select_one("div.course-section")
        assert section_entry

        section_text = get_tag_text(section_entry)
        log.debug("Matching header: %s", section_text)
        section_match = re.match(r"^(.+)(?=\.)", section_text)
        assert section_match

        course_id = section_match.group(1)

        log.debug("Scraping supplementary info for: %s", course_id)
        if course_id in supplementary_info:
            info = supplementary_info[course_id]
        else:
            info = {}
            supplementary_info[course_id] = info

        course_chair = section_group.select_one("div.course-chair")
        if course_chair:
            chair_text = get_tag_text(course_chair)
            log.debug("Matching course chair: %s", chair_text)
            chair_match = re.match(r"\(Course chair: (.+)\)", chair_text)
            assert chair_match

            info["chair"] = chair_match.group(1)
            log.debug("Got course chair: %s", info["chair"])

        course_website = section_group.select_one("div.course-webpage")
        if course_website:
            a_tag = course_website.select_one("a")
            assert a_tag

            info["website"] = a_tag.attrs["href"]
            log.debug("Got website: %s", info["website"])

        instructor = section_group.select_one("div.instructor")
        if instructor:
            instructor_text = get_tag_text(instructor)
            log.debug("Got instructor: %s", instructor_text)

            if "staff" in info:
                info["staff"].add(instructor_text)
            else:
                info["staff"] = set([instructor_text])

    log.debug("Scraped supplementary information.")

    most_recent_semester = None
    courses = {}

    soup = fetch_soup("https://www.math.umass.edu/course-descriptions")
    first_option = soup.select_one("#edit-semester-tid > option[selected='selected']")

    start = int(first_option.attrs["value"])
    log.debug("Starting descriptions from semester id: %s", start)

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
        if most_recent_semester is None:
            most_recent_semester = semester

        log.debug("Scraping mathematics courses for %s...", semester)
        for article in articles:
            title_tag = article.select_one("div[class^='field-title']")
            assert title_tag

            raw_title = get_tag_text(title_tag)

            log.debug("Matching title: %s", raw_title)
            title_match = re.match(r"^(MATH|STAT|HONORS)\s+(\w+)(\.\d*)?:\s*([\w -:]+)", raw_title, re.I)
            assert title_match
            log.debug("Matched: %s", title_match)

            if title_match.group(1) == "HONORS":
                log.debug("Skipping due to HONORS subject.")
                continue

            course_subject = title_match.group(1).upper()
            if course_subject == "STAT":
                course_subject = "STATISTIC"

            course_number = title_match.group(2).upper()
            course_id = course_subject + " " + course_number

            log.debug("Scraping course: %s", course_id)
            if course_id in courses:
                log.debug("Found past entry, reusing tuple.")
                course = courses[course_id]
            else:
                log.debug("No past entry found. Aggregating information...")
                course_title = title_match.group(4)
                description_tag = article.select_one("div[class^='field-course-descr-description']")
                assert description_tag

                info = {}
                if course_id in supplementary_info:
                    info = supplementary_info[course_id]

                course_description = get_tag_text(description_tag)
                course_prereqs = article.select_one("div[class^='field-course-descr-prereq']")
                course = MATHCourse(
                    subject=course_subject,
                    id=course_id,
                    number=course_number,
                    title=course_title,
                    description=course_description,
                    offerings=[],
                    prerequisites=get_tag_text(course_prereqs) if course_prereqs else None,
                    semester_staff={info_semester: ", ".join(info["staff"])} if "staff" in info else {},
                    chair=info["chair"] if "chair" in info else None,
                    semester_websites={info_semester: info["website"]} if "website" in info else None,
                )

                courses[course_id] = course

            course.offerings.append(semester)
            log.debug("Finished updating: %s", course)

        log.debug("Scraped mathematics courses for %s.", semester)

    log.debug("Scraped descriptions.")

    log.info("Scraped mathematics courses.")
    return DescriptionsPosting(most_recent_semester, courses)
