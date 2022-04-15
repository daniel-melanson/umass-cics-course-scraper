import re

from shared.util import clean_text

COURSE_ID_PATTERN = re.compile(r"^[A-Z]{2,10} \d{3}([A-Z]+)?")


def is_course_id(s: str) -> bool:
    return COURSE_ID_PATTERN.match(s) is not None


class CourseID:
    @staticmethod
    def from_text(text: str) -> "CourseID":
        course_id = clean_text(text).upper()

        assert is_course_id(course_id)

        [subject, number] = course_id.split(" ")

        return CourseID(subject, number)

    def __init__(self, subject: str, number: str) -> None:
        self._id = f"{subject.upper()} {number.upper()}"
        self._subject = subject
        self._number = number

    def __str__(self) -> str:
        return self._id

    @property
    def subject(self) -> str:
        return self._subject

    @property
    def number(self) -> str:
        return self._number

    @property
    def id(self) -> str:
        return self._id
