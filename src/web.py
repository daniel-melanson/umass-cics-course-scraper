import re

from datetime import datetime
import pytz

from unidecode import unidecode

import requests
from bs4 import BeautifulSoup, Tag

aliases = {
    'Andrew Lan': 'Shiting Lan',
    'Ivan Lee': 'Sunghoon Lee',
    'Joe Chiu': 'Meng-Chieh Chiu'
}
local_zone = pytz.timezone("America/New_York")
REGEXP_NAME_GROUP = "[a-zA-ZàáâäãåąčćęèéêëėįìíîïłńòóôöõøùúûüųūÿýżźñçčšžÀÁÂÄÃÅĄĆČĖĘÈÉÊËÌÍÎÏĮŁŃÒÓÔÖÕØÙÚÛÜŲŪŸÝŻŹÑßÇŒÆČŠŽ∂ð ,.'-]+"


def clean_text(s: str):
    for r in ['\xa0', '\n', '\t']:
        s = s.replace(r, ' ')

    while '  ' in s:
        s = s.replace("  ", ' ')

    return s.strip()


def unicode_text_of(elem: Tag):
    return clean_text(unidecode(elem.text))


def text_of(elem: Tag) -> str:
    return clean_text(elem.text)


def scrape(url: str):
    try:
        res = requests.get(url)
        return BeautifulSoup(res.content, "html5lib")
    except requests.ConnectionError:
        return None


def get_course_frequency():
    # cics course frequency
    soup = scrape("https://web.cs.umass.edu/csinfo/autogen/cmpscicoursesfull.html")
    course_tr_list = soup.select("tr:not(:first-child)")

    def cics_course_frequency(elem: Tag):
        return (
            '%s %s' % (
                text_of(elem.select_one("td:first-child")),
                text_of(elem.select_one("td:nth-child(2)"))
            ),
            text_of(elem.select_one("td:last-child"))
        )

    course_frequency = list(map(cics_course_frequency, course_tr_list))

    # math course frequency
    soup = scrape("https://www.math.umass.edu/course-offerings")
    course_tr_list = soup.select("tr:not(:only-child)")

    def math_course_frequency(elem: Tag):
        freq = text_of(elem.select_one("td:last-child"))
        if freq == "Fall/Spring/Summer":
            freq = "Fall, Spring, and Summer"
        else:
            freq = freq.replace('/', " and ").replace("  ", ' ')

        return (text_of(elem.select_one("td:first-child")).upper(), freq)

    course_frequency.extend(map(math_course_frequency, course_tr_list))

    return course_frequency


def scrape_courses():
    course_map = {}

    # CICS Courses
    current_year = int(datetime.now().year) % 2000 + 1

    for year in range(current_year, 17, -1):
        for query_id in [7, 3]:
            soup = scrape(f"https://web.cs.umass.edu/csinfo/autogen/cicsdesc1{year}{query_id}.html")
            if not soup or (soup.title and soup.title.text == "404 Not Found"):
                continue

            for header in soup.select("h2:not(:first-child)"):
                raw_title = text_of(header.select_one(":first-child"))
                title_match = re.match(
                    r'^(CICS|COMPSCI|INFO|INFOSEC)\s*(\w+):\s*([\w -:]+)',
                    raw_title, re.IGNORECASE)
                if not title_match or title_match.group(1) == 'INFOSEC':
                    continue

                course_subject = title_match.group(1)
                course_id = (
                    course_subject + ' ' + title_match.group(2)
                ).upper()

                session_staff = set()
                next_sibling = list(header.next_siblings)[1]
                if next_sibling.name == 'h3':
                    if instructor_match := re.match(
                        r'^(Instructor\(s\): )(.+)',
                        text_of(next_sibling), re.IGNORECASE
                    ):
                        name_list = instructor_match.group(2).split(", ")

                        for name in name_list:
                            if not re.match(r'Staff', name, re.IGNORECASE):
                                session_staff.add(unidecode(name.strip()))

                if course_id in course_map:
                    course_staff = course_map[course_id]['staff']

                    for name in session_staff:
                        course_staff.add(name)
                else:
                    course_title = title_match.group(3)
                    course_description = text_of(header.find_next_sibling("p"))

                    course = {
                        'subject': course_subject,
                        'id': course_id,
                        'number': course_id.split()[1],
                        'title': course_title,
                        'description': course_description,
                        'staff': session_staff,
                    }

                    course_website = header.select_one("a")['href']
                    if len(course_website) > 0:
                        course['website'] = course_website

                    course_map[course_id] = course

    for course in course_map.values():
        course['staff'] = list(course['staff'])

    # MATH Courses
    soup = scrape("https://www.math.umass.edu/course-descriptions")
    first_option = soup.select_one("#edit-semester-tid > option:first-child")

    start = int(first_option['value'])
    for i in range(start - 10, start + 1):
        soup = scrape(f"https://www.math.umass.edu/course-descriptions?semester_tid={i}")

        for article in soup.select("div > article"):
            raw_title = text_of(
                article.select_one("div[class^='field-title']")
            )

            title_match = re.match(
                r'^(MATH|STAT|HONORS)\s*(\w+)(\.\d*)?:\s*([\w -:]+)',
                raw_title,
                re.IGNORECASE
            )

            if not title_match or title_match.group(1) == 'HONORS':
                continue

            course_subject = title_match.group(1)
            if course_subject == 'STAT':
                course_subject = 'STATISTIC'

            course_id = (course_subject + ' ' + title_match.group(2)).upper()
            if course_id in course_map:
                continue

            course_title = title_match.group(4)
            course_description = text_of(article.select_one(
                "div[class^='field-course-descr-description']"
            ))

            course = {
                'subject': course_subject,
                'id': course_id,
                'number': course_id.split()[1],
                'title': course_title,
                'description': course_description,
            }

            course_prereqs = article.select_one(
                "div[class^='field-course-descr-prereq']"
            )
            if course_prereqs:
                course['enrollmentRequirement'] = "Prerequisites: " + re.sub(
                    r"\s*prereq(uisite)?(s)?(:)?",
                    "",
                    text_of(course_prereqs),
                    flags=re.I
                ).strip()

            course_map[course_id] = course

    for (course_id, freq) in get_course_frequency():
        if course_id in course_map:
            course_map[course_id]['frequency'] = freq

    return course_map


def div_get(div_element, class_name: str, selector=None):
    sel = f"div[class='views-field views-field-{class_name}']" + (f" > {selector}" if selector else "")
    return div_element.select_one(sel)


def retrieve_staff_information():
    staff_list = []

    soup = scrape("https://www.cics.umass.edu/people/all-faculty-staff")
    for div_element in soup.select("div.view-content > div.clearfix > div"):
        name_element = div_get(div_element, "title", "span > a")
        raw_name = unicode_text_of(name_element)
        name_match = re.match(r"^(%s),\s*(%s)" % (REGEXP_NAME_GROUP, REGEXP_NAME_GROUP), raw_name)
        if not name_match: 
            raise RuntimeError(raw_name)

        staff = {
            'names': [f'{name_match.group(2)} {name_match.group(1)}'],
            'title': text_of(div_get(div_element, "field-position")),
            'email': text_of(div_get(div_element, "field-email", "a")),
        }

        phone_element = div_get(div_element, "field-phone")
        if phone_element:
            staff['phone'] = text_of(phone_element)[3:]

        location_element= div_get(div_element, "field-location", "span.field-content")
        if location_element:
            staff['office'] = text_of(location_element)

        website = name_element['href']
        if website[0] == '/':
            staff['website'] = "https://www.cics.umass.edu" + website

            staff_soup = scrape(staff['website'])
            additional_name = unicode_text_of(staff_soup.select_one("#page-title"))
            names = staff['names']
            if additional_name not in names:
                names.append(additional_name)

            img_element = staff_soup.select_one("div.content > div > div > img")
            if img_element:
                staff['photo'] = img_element['src']

        else:
            staff['website'] = website

        cics_name = staff['names'][0]
        if cics_name in aliases and (alias := aliases[cics_name]) not in staff['names']:
            staff['names'].append(alias)

        staff_list.append(staff)

    return staff_list


def get_academic_schedule():
    soup = scrape(
        'https://www.umass.edu/registrar/calendars/academic-calendar'
    )

    semester_list = []
    for header in soup.select(".field-item h3"):
        semester_title = text_of(header)

        match = re.match(
            r'^(university )?(spring|summer|fall|winter) (\d{4})',
            semester_title,
            re.IGNORECASE
        )
        if not match:
            continue

        year = match.group(3)
        season = match.group(2)
        semester = {
            'season': season,
            'year': year,
            'events': [],
        }

        table = header.find_next("table")
        for event_element in table.select("tr"):
            content_children = list(filter(lambda child: child and len(text_of(child)) > 0 , event_element.children))
            event_desc = text_of(content_children[0])
            month_name = text_of(content_children[2])
            day_number = text_of(content_children[3])

            adjusted_year = year
            if season == 'winter' and (month_name == "January" or month_name == "February"):
                adjusted_year = str(int(year) + 1)

            native_time = datetime.strptime(f'{day_number} {month_name} {adjusted_year} 00:00:00', "%d %B %Y %H:%M:%S")
            utc_time = local_zone.localize(native_time).astimezone(pytz.utc)

            if re.match(event_desc, 'First day of classes', re.IGNORECASE):
                semester['startDate'] = utc_time
            elif re.match(event_desc, 'Last day of classes', re.IGNORECASE):
                semester['endDate'] = utc_time

            semester['events'].append({
                'date': utc_time,
                'description': event_desc,
            })

        semester_list.append(semester)

    return semester_list
