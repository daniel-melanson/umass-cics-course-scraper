import json
import logging
import sys
from datetime import datetime
from os import path
from typing import NamedTuple, Union

from requests import JSONDecodeError

from scraper.scraper import scrape

logging.basicConfig(
    filename="out.log",
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    level=logging.DEBUG,
    datefmt="%H:%M:%S",
    filemode="w",
)
log = logging.getLogger(__name__)


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
            elif flag == "verbose":
                verbose = True
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
        log.addFilter(lambda _: False)

    log.info("Starting...")
    if flags.json:
        log.info("--json supplied. Attempting to open %s.", flags.json)
        try:
            file = open(flags.json, "r", encoding="utf-8")
        except IOError as exception:
            log.exception("Failed to open JSON file: %s", exception)
            abort("Unable to open `.json` file.")

        log.info("File opened. Attempting to load.")
        try:
            data = json.load(file)
        except JSONDecodeError as exception:
            log.exception("Failed to load JSON: %s", exception)
            abort("Unable to load `.json` file.")

        file.close()
        log.info("Successfully loaded raw data.")
    else:
        log.info("Beginning scraping routine...")
        try:
            data = scrape(flags.headless)
        except Exception as exception:
            log.exception("Failed while scraping: %s", exception)
            abort("Failed scrape raw info.")

        log.info("Scraping routine successfully finished.")
        if flags.dump:
            log.info("Dumping scraped info..")
            file_name = f"scrape-results-{datetime.now().isoformat()}.json"
            try:
                file = open(file_name, "w", encoding="utf-8")

                json.dump(data, file)
                file.close()
            except Exception as exception:
                log.error("Unable to dump data: %s", exception)
                print("Unable to write JSON. Skipping.")

            log.info("Dumped raw info to %s.", file_name)

    log.info("Beginning normalizing routine...")
    try:
        pass
    except Exception as exception:
        log.exception("Failed while normalizing: %s", exception)
        abort("Unable to normalize staff and course information.")

    log.info("Normalizing routine successfully finished.")

    if flags.mongo:
        log.info("Beginning uploading routine.")
        try:
            pass
        except Exception as exception:
            log.exception("Failed pushing information: %s", exception)
            abort("Unable to upload information.")

        log.info("Uploading routine successfully finished.")
    else:
        log.info("--mongo not supplied. Skipping uploading routine.")

    log.info("Done.")


if __name__ == "__main__":
    main(sys.argv)
