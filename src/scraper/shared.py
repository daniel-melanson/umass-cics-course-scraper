from time import sleep
from typing import Union

import logging
import requests
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger()


def clean_text(s: str):
    for r in ["\xa0", "\n", "\t"]:
        s = s.replace(r, " ")

    while "  " in s:
        s = s.replace("  ", " ")

    return s.strip()


def fetch_soup(url: str) -> Union[BeautifulSoup, None]:
    logger.info("Fetching %s...", url)
    attempts = 0
    while True:
        try:
            res = requests.get(url)
            logger.info("Successfully fetched %s.", url)
            break
        except Exception as e:
            attempts += 1
            if attempts < 5:
                logger.exception("Failed to fetch: %s.", e)
                logger.info("Sleeping...")
                sleep(5)
            else:
                raise RuntimeError("Unable to fetch %s.", url)

    return BeautifulSoup(res.content, "html5lib")


def get_tag_text(tag: Tag):
    return clean_text(tag.text)
