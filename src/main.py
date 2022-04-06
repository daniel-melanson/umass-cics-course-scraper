#! python3

import json
import logging
import sys
from datetime import datetime
from os import path
from typing import NamedTuple, Union

from mongo.mongo import push_info
from normalizer.normalizer import normalize_info
from scraper.scraper import scrape_raw_info

logger = logging.getLogger("log")


class Flags(NamedTuple):
    headless: bool
    verbose: bool
    dump: bool
    json: Union[str, None]
    mongo: str


def abort(msg: str):
    sys.exit(msg + " Aborting.")


def parse_args(args: list[str]) -> Flags:
    headless = False
    verbose = False
    dump = False
    json = None
    mongo = None

    for i in range(1, len(args)):
        arg = args[i].lower()

        if arg.startswith("--"):
            flag = arg[2:]
            if flag == "headless":
                headless = True
            elif flag == "dump":
                if json is not None:
                    abort("`--dump` is mutually exclusive with `--json`.")

                dump = True
            elif flag.startswith("dataJson="):
                if dump:
                    abort("`--json` is mutually exclusive with `--dump`.")

                filePath = flag[9:].strip()
                if not path.isfile(filePath):
                    abort(f"Invalid json file path: {filePath}.")

                json = filePath
        else:
            abort(f"Unrecognized flag: {arg}")

    return Flags(headless, verbose, dump, json, mongo)


def main(args: list[str]):
    flags = parse_args(args)

    if not flags.verbose:
        logger.addFilter()

    logger.info("Starting...")
    if flags.json:
        logger.info("--json supplied. Attempting to open %s", flags.json)
        try:
            file = open(flags.json, "r")
        except IOError as e:
            logger.error("Failed to open JSON file.", e)
            abort("Unable to open `.json` file.")

        logger.info("File opened. Attempting to load.")
        try:
            data = json.load(file)
        except RuntimeError as e:
            logger.error("Failed to load JSON. %s", e)
            abort("Unable to load `.json` file.")

        file.close()
        logger.info("Successfully loaded raw data.")
    else:
        logger.info("Beginning scraping routine...")
        try:
            data = scrape_raw_info()
        except RuntimeError as e:
            logger.error("Failed while scraping. %s", e)
            abort(f"Failed scrape raw info.{e}")

        logger.info("Scraping routine successfully finished.")
        if flags.dump:
            logger.info("Dumping scraped info..")
            file_name = f"scrape-results-{datetime.now().isoformat()}.json"
            try:
                file = open(file_name, "w")

                json.dump(data, file)
                file.close()
            except IOError as e:
                logger.error("Unable to dump data. %s", e)
                print("Unable to write JSON. Skipping.")

            logger.info("Dumped raw info to %s.", file_name)

    logger.info("Beginning normalizing routine...")
    try:
        (course, staff) = normalize_info(data[:2])
    except RuntimeError as e:
        logger.error("Filed while normalizing. %s", e)
        abort("Unable to normalize staff and course information.")

    logger.info("Normalizing routine successfully finished.")

    if flags.mongo:
        logger.info("Beginning uploading routine.")
        try:
            push_info(flags.mongo, (course, staff, data[2]))
        except RuntimeError as e:
            logger.error("Failed pushing information. %s", e)
            abort("Unable to upload information.")

        logger.info("Uploading routine successfully finished.")
    else:
        logger.info("--mongo not supplied. Skipping uploading routine.")

    logger.info("Done.")


if __name__ == "__main__":
    main(sys.argv)
