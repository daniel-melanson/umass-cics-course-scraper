import html
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

    staff_list = []

    _scrape_cics_staff(staff_list)
    _scrape_math_staff(staff_list)

    log.info("Scraped staff list.")
    return staff_list


def _scrape_cics_staff(staff_list: list[Staff]):
    log.info("Scraping CICS staff...")
    soup = fetch_soup("https://www.cics.umass.edu/people/all-faculty-staff")

    for staff_div in soup.select("div.view-faculty-directory > div.view-content > div > div.views-row"):
        name_link = staff_div.select_one("div.views-field-title > span > a")
        assert name_link

        raw_name = get_tag_text(name_link)
        log.debug("Matching staff name: %s", raw_name)
        name_match = re.match(f"^({REGEXP_NAME_GROUP}),\s*({REGEXP_NAME_GROUP})", raw_name)
        assert name_match

        staff = Staff(names=set([f"{name_match.group(2)} {name_match.group(1)}"]), department="CICS")

        log.debug("Initalized staff member: %s", staff)
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
            staff["website"] = href

        log.debug("Adding staff member %s.", staff)
        staff_list.append(staff)

    log.info("Scraped CICS staff.")


def _scrape_math_staff(staff_list: list[Staff]):
    log.info("Scraping Mathematics department staff...")

    soup = fetch_soup("https://www.math.umass.edu/directory/faculty")

    for tr in soup.select("div.view-content > table > tbody > tr"):
        link_tag = tr.select_one("td.views-field-title > a")
        assert link_tag

        staff_info = {}
        name = get_tag_text(link_tag)
        log.debug("Scraping mathematics staff member: %s", name)
        staff_info["names"] = [name]
        website = link_tag.attrs["href"]
        if website.startswith("/"):
            staff_info["website"] = "https://www.math.umass.edu" + link_tag.attrs["href"]

            log.debug("Scraping supplementary staff information...")
            staff_soup = fetch_soup(staff_info["website"])

            img = staff_soup.select_one("div.field-dir-photo > img")
            if img:
                log.debug("Found photo, scraping.")

                staff_info["photo"] = img.attrs["src"]

            personal_website = staff_soup.select_one("div.field-dir-personal-webpage > a")
            if personal_website:
                log.debug("Found personal website, scraping.")

                staff_info["website"] = personal_website.attrs["href"]

        else:
            staff_info["website"] = website

        staff_email_script = tr.select_one("div.field-dir-email > script")
        assert staff_email_script

        script_text = staff_email_script.next_element
        log.debug("Matching: %s", script_text)
        script_match = re.search(r"<a href=\"(.+)\"", script_text)
        assert script_match

        encoded_email = script_match.group(1)
        email = html.unescape(encoded_email)[7:]
        staff_info["email"] = email
        log.debug("Got staff email: %s", email)

        for (selector, attr) in [
            ("div.field-dir-office1", "office"),
            ("div.field-dir-phone1", "phone"),
            ("div.field-dir-position", "title"),
        ]:
            tag = tr.select_one(selector)
            if tag:
                staff_info[attr] = get_tag_text(tag)
                log.debug("Found attribute: %s, scraped: %s", attr, staff_info[attr])
            else:
                log.debug("No tag found for attribute %s, skipping.", attr)

        staff = Staff(
            names=staff_info["names"],
            department="Mathematics",
            email=staff_info["email"] if "email" in staff_info else None,
            office=staff_info["office"] if "office" in staff_info else None,
            phone=staff_info["phone"] if "phone" in staff_info else None,
            photo=staff_info["photo"] if "photo" in staff_info else None,
            title=staff_info["title"] if "title" in staff_info else None,
            website=staff_info["website"],
        )

        log.debug("Scraped staff member: %s", staff)
        staff_list.append(staff)

    log.info("Scraped Mathematics department staff.")
