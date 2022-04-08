import logging
from time import sleep
from typing import Union

from unidecode import unidecode
import requests
from bs4 import BeautifulSoup, Tag

log = logging.getLogger(__name__)


def clean_text(s: str):
    for r in ["\xa0", "\n", "\t"]:
        s = s.replace(r, " ")

    while "  " in s:
        s = s.replace("  ", " ")

    return s.strip()


def fetch_soup(url: str) -> Union[BeautifulSoup, None]:
    log.info("Fetching %s...", url)
    attempts = 0
    while True:
        try:
            res = requests.get(url)
            log.info("Successfully fetched %s.", url)
            break
        except Exception as e:
            attempts += 1
            if attempts < 5:
                log.exception("Failed to fetch %s: %s.", url, e)
                log.info("Sleeping...")
                sleep(5)
            else:
                raise RuntimeError("Unable to fetch %s.", url)

    return BeautifulSoup(res.content, "html5lib")


def get_tag_text(tag: Tag, decode=False):
    text = clean_text(tag.text)

    return unidecode(text) if decode else text
