import re
from typing import NamedTuple, Optional
import logging

from scraper.shared import fetch_soup, get_tag_text


REGEXP_NAME_GROUP = "[a-zA-ZàáâäãåąčćęèéêëėįìíîïłńòóôöõøùúûüųūÿýżźñçčšžÀÁÂÄÃÅĄĆČĖĘÈÉÊËÌÍÎÏĮŁŃÒÓÔÖÕØÙÚÛÜŲŪŸÝŻŹÑßÇŒÆČŠŽ∂ð ,.'-]+"
logger = logging.getLogger()


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


def supplemental_information():
    return None


def scrape_raw_staff_list() -> list[RawStaff]:
    logger.info("Scraping staff list...")
    soup = fetch_soup("https://www.cics.umass.edu/people/all-faculty-staff")

    staff_list = []
    for staff_div in soup.select("div.view-faculty-directory > div.view-content > div > div.views-row"):
        name_link = staff_div.select_one("div.views-field-title > span > a")
        assert name_link

        raw_name = get_tag_text(name_link)
        name_match = re.match(r"^(%s),\s*(%s)" % (REGEXP_NAME_GROUP, REGEXP_NAME_GROUP), raw_name)
        assert name_match

        staff = RawStaff(
            names=[f"{name_match.group(2)} {name_match.group(1)}"]
        )

        logger.info("Scraping staff member %s.", staff.names[0])
        attributes = [
            ("title", "field-position"),
            ("email", "field-email"),
            ("phone", "field-phone"),
            ("office", "field-location")
        ]

        for (attribute, selector) in attributes:
            logger.info("Scraping attribute %s.", attribute)
            tag = staff_div.select_one(selector)

            if tag:
                staff[attribute] = get_tag_text(tag)
                logger.info("Scraped %s for staff %s.", staff[attribute], attribute)
            else:
                logger.info("No tag found, skipping.")

        if (href := name_link.attrs["href"]).startswith("/"):
            logger.info("Scraping supplemental information from %s.", href)

        else:
            logger.info("Offsite url, skipping supplemental scrape process.")
        
        logger.info("Adding staff member %s.", staff)
        staff_list.append(staff)

    return staff_list


if __name__ == '__main__':
    scrape_raw_staff_list()
