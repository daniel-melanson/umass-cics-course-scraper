import logging
import re
from typing import Optional, TypedDict

from scraper.shared import fetch_soup, get_tag_text

log = logging.getLogger(__name__)

REGEXP_NAME_GROUP = (
    "[a-zA-ZàáâäãåąčćęèéêëėįìíîïłńòóôöõøùúûüųūÿýżźñçčšžÀÁÂÄÃÅĄĆČĖĘÈÉÊËÌÍÎÏĮŁŃÒÓÔÖÕØÙÚÛÜŲŪŸÝŻŹÑßÇŒÆČŠŽ∂ð ,.'-]+"
)


class Staff(TypedDict):
    names: set[str]
    department: str
    title: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    office: Optional[str]
    website: Optional[str]
    photo: Optional[str]


def scrape_staff() -> list[Staff]:
    log.info("Scraping staff list...")
    soup = fetch_soup("https://www.cics.umass.edu/people/all-faculty-staff")

    staff_list = []
    for staff_div in soup.select("div.view-faculty-directory > div.view-content > div > div.views-row"):
        name_link = staff_div.select_one("div.views-field-title > span > a")
        assert name_link

        raw_name = get_tag_text(name_link)
        log.debug("Matching staff name: %s", raw_name)
        name_match = re.match(f"^({REGEXP_NAME_GROUP}),\s*({REGEXP_NAME_GROUP})", raw_name)
        assert name_match

        staff = Staff(names=set([f"{name_match.group(2)} {name_match.group(1)}"]), department="CICS")

        log.debug("Initalized staff member %s.", staff)
        attributes = [
            ("title", "position", 0),
            ("email", "email", 3),
            ("phone", "phone", 3),
            ("office", "location", 3),
        ]

        for (attribute, selector, offset) in attributes:
            tag = staff_div.select_one(f"div.views-field-field-{selector}")

            if tag:
                raw_text = get_tag_text(tag)
                staff[attribute] = raw_text[offset:]
                log.debug("Scraped '%s' for staff %s.", staff[attribute], attribute)
            else:
                log.debug("No tag found for %s, skipping.", attribute)

        if (href := name_link.attrs["href"]).startswith("/"):
            log.debug("Scraping supplemental information from %s.", href)
            staff["website"] = "https://www.cics.umass.edu" + href

            staff_website_soup = fetch_soup(staff["website"])
            header = staff_website_soup.select_one("#page-title")
            staff["names"].add(get_tag_text(header))

            img_tag = staff_website_soup.select_one("div.headshot-wrapper > img")
            if img_tag and img_tag.attrs["src"]:
                staff["photo"] = img_tag.attrs["src"]
        else:
            log.debug("Offsite url, skipping supplemental scrape process.")

        log.debug("Adding staff member %s.", staff)
        staff_list.append(staff)

    log.info("Scraped staff information.")
    return staff_list
