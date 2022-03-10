from typing import NamedTuple, Tuple


class Course(NamedTuple):
    id: str
    subject: str


class Staff(NamedTuple):
    names: str


def normalize_info(data) -> Tuple[Course, Staff]:
    pass
