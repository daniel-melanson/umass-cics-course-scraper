import re
from typing import NamedTuple, Union
from datetime import datetime

from scraper.shared import fetch_soup, get_tag_text


class Event(NamedTuple):
    date: datetime
    description: str


class Semester(NamedTuple):
    season: str
    year: int
    startDate: datetime
    endDate: datetime
    events: list[Event]


eastern = pytz.timezone('US/Eastern')
def scrape_academic_schedule() -> Union[list[Semester], None]:
    soup = fetch_soup('https://www.umass.edu/registrar/calendars/academic-calendar')

    if soup is None:
        return None

    semester_list = []
    for header in soup.select('.field-item h3'):
        semester_title = get_tag_text(header)

        match = re.match(
            r'^(university )?(spring|summer|fall|winter) (\d{4})',
            semester_title,
            re.I
        )
        if not match:
            continue

        year = match.group(3)
        season = match.group(2)
        semester = Semester(season, year, None, None, [])

        table = header.find_next('table')
        for event_element in table.select('tr'):
            event_desc = get_tag_text(event_element.select_one('td:first-child'))
            month_name = get_tag_text(event_element.select_one('td:nth-child(3)'))
            day_number = get_tag_text(event_element.select_one('td:last-child'))

            adjusted_year = year
            if season == 'winter' and month_name in ('January', 'February'):
                adjusted_year = str(int(year) + 1)

            native_time = datetime.strptime(f'{day_number} {month_name} {adjusted_year} 00:00:00', '%d %B %Y %H:%M:%S')
            utc_time = eastern.localize(native_time).astimezone(pytz.utc)

            if re.match(event_desc, 'First day of classes', re.IGNORECASE):
                semester.startDate = utc_time
            elif re.match(event_desc, 'Last day of classes', re.IGNORECASE):
                semester.endDate = utc_time

            semester.events.append({
                'date': utc_time,
                'description': event_desc,
            })

        semester_list.append(semester)

    return semester_list
