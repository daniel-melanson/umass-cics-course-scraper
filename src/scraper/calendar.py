import re
from datetime import datetime
from typing import NamedTuple

import logging
import pytz

from scraper.shared import fetch_soup, get_tag_text


log = logging.getLogger(__name__)


class Event(NamedTuple):
    date: datetime
    description: str


class Semester(NamedTuple):
    season: str
    year: int
    startDate: datetime
    endDate: datetime
    events: list[Event]


local_tz = pytz.timezone("America/New_York")


def scrape_academic_schedule() -> list[Semester]:
    log.info("Scraping academic schedule...")
    soup = fetch_soup("https://www.umass.edu/registrar/calendars/academic-calendar")

    semester_list = []
    for header in soup.select(".field-item h3"):
        semester_title = get_tag_text(header)

        log.info("Scraping semester %s.", semester_title)
        match = re.match(r"^(university )?(spring|summer|fall|winter) (\d{4})", semester_title, re.I)
        if not match:
            log.info("Header '%s' does not match, skipping.")
            continue

        year = match.group(3)
        season = match.group(2)
        semester = Semester(season, year, None, None, [])

        log.info("Initalized semester: %s", semester)
        log.info("Scraping events...")

        table = header.find_next("table")
        for event_element in table.select("tr"):
            event_desc = get_tag_text(event_element.select_one("td:first-child"))
            month_name = get_tag_text(event_element.select_one("td:nth-child(3)"))
            day_number = get_tag_text(event_element.select_one("td:last-child"))

            log.info("Got event desc: %s, month: %s, day: %s", event_desc, month_name, day_number)

            adjusted_year = year
            if season == "winter" and month_name in ("January", "February"):
                adjusted_year = str(int(year) + 1)
                log.info("Adjusted year to %s", adjusted_year)

            utc_time = local_tz.localize(
                datetime.strptime(f"{day_number} {month_name} {adjusted_year} 00:00:00", "%d %B %Y %H:%M:%S")
            ).astimezone(pytz.utc)

            if re.match(event_desc, "First day of classes", re.I):
                log.info("Selecting event as start date.")
                semester.startDate = utc_time
            elif re.match(event_desc, "Last day of classes", re.I):
                log.info("Selecting event as end date.")
                semester.endDate = utc_time

            event = {
                "date": utc_time,
                "description": event_desc,
            }

            log.info("Adding event %s to %s %s", event, semester.season, semester.year)
            semester.events.append(event)

        log.info("Events scraped.")
        log.info("Adding semesters %s", semester)
        semester_list.append(semester)

    log.info("Semesters scraped.")
    return semester_list
