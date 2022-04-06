from typing import NamedTuple, Optional


class RawStaff(NamedTuple):
    names: list[str]
    title: Optional[str]
    email: Optional[str]
    website: Optional[str]
    photo: Optional[str]
    phone: Optional[str]
    office: Optional[str]
    courses: Optional[list[str]]


class CourseFrequency(NamedTuple):
    id: str
    frequency: str
