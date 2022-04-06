from time import sleep
from typing import Union

import requests
from bs4 import BeautifulSoup, Tag


def clean_text(s: str):
    for r in ["\xa0", "\n", "\t"]:
        s = s.replace(r, " ")

    while "  " in s:
        s = s.replace("  ", " ")

    return s.strip()


def fetch_soup(url: str) -> Union[BeautifulSoup, None]:
    attempts = 0
    while attempts <= 5:
        try:
            res = requests.get(url)
            return BeautifulSoup(res.content, "html5lib")
        except requests.ConnectionError:
            attempts += 1
            sleep(5)

    return None


def get_tag_text(tag: Tag):
    return clean_text(tag.text)
