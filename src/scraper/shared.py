import logging
from time import sleep

import requests
from bs4 import BeautifulSoup, Tag
from requests.exceptions import RequestException
from unidecode import unidecode

log = logging.getLogger(__name__)


def clean_text(s: str):
    for r in ["\xa0", "\n", "\t"]:
        s = s.replace(r, " ")

    while "  " in s:
        s = s.replace("  ", " ")

    return s.strip()


def fetch_soup(url: str, retry=True) -> BeautifulSoup:
    log.debug("Fetching %s...", url)
    attempts = 0
    while True:
        try:
            res = requests.get(url)
            res.raise_for_status()
            log.debug("Successfully fetched %s.", url)
            break
        except RequestException as exception:
            attempts += 1
            if retry and attempts < 5:
                log.exception("Failed to fetch %s: %s.", url, exception)
                log.info("Sleeping...")
                sleep(5)
            else:
                raise exception

    return BeautifulSoup(res.content, "html5lib")


def get_tag_text(tag: Tag, decode=False):
    text = clean_text(tag.text)

    return unidecode(text) if decode else text
