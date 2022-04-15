import logging
import re
from datetime import datetime
from typing import NamedTuple

import pytz

from scraper.shared import fetch_soup, get_tag_text
from shared.semester import Semester

log = logging.getLogger(__name__)


class Event(NamedTuple):
    date: datetime
    description: str


class SemesterSchedule(NamedTuple):
    semester: Semester
    start_date: datetime
    end_date: datetime
    events: list[Event]


local_tz = pytz.timezone("America/New_York")


def scrape_academic_schedule() -> list[Semester]:
    log.info("Scraping academic schedule...")
    soup = fetch_soup("https://www.umass.edu/registrar/calendars/academic-calendar")

    semester_list = []
    for header in soup.select(".field-item h3"):
        semester_title = get_tag_text(header, decode=True)

        log.debug("Scraping semester: %s", semester_title)
        match = re.match(r"^(University )?(Spring|Summer|Fall|Winter) (\d{4})", semester_title)
        if not match:
            log.debug("Header '%s' does not match, skipping.", semester_title)
            continue

        year = match.group(3)
        season = match.group(2)
        event_list = []

        start_date = None
        end_date = None
        semester = Semester(season, year)
        log.debug("Scraping events for: %s", str(semester))

        table = header.find_next("table")
        for event_element in table.select("tr"):
            event_text = get_tag_text(event_element, decode=True)

            log.debug("Got event: %s", event_text)
            event_match = re.match(
                r"^(.+) (Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday) (January|February|March|April|May|June|July|August|September|October|November|December) (\d{1,2})$",
                event_text,
                re.I,
            )
            assert event_match

            event_desc = event_match.group(1)
            event_month = event_match.group(3)
            event_day = event_match.group(4)

            log.debug("Scraped event: %s %s - %s", event_month, event_day, event_desc)

            adjusted_year = year
            if season == "winter" and event_month in ("January", "February"):
                adjusted_year = str(int(year) + 1)
                log.info("Adjusted year to %s", adjusted_year)

            utc_time = local_tz.localize(
                datetime.strptime(f"{event_day} {event_month} {adjusted_year} 00:00:00", "%d %B %Y %H:%M:%S")
            ).astimezone(pytz.utc)

            if re.match(event_desc, "First day of classes", re.I):
                log.debug("Selecting event as start date.")
                start_date = utc_time
            elif re.match(event_desc, "Last day of classes", re.I):
                log.debug("Selecting event as end date.")
                end_date = utc_time

            event = Event(utc_time, event_desc)

            log.debug("Adding event: %s", event)
            event_list.append(event)

        semester_list.append(SemesterSchedule(semester, start_date, end_date, event_list))
        log.debug("Added semester schedule: %s", semester_list[-1])

    log.info("Scraped academic schedule.")
    return semester_list
