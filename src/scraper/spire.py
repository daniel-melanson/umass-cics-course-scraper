from typing import TypedDict


class RawCourse(TypedDict):
    id: str


def scrape_course_list() -> list[RawCourse]:
    return None
