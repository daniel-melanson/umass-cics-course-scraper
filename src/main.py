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
    json: bool
    dataJson: Union[str, None]
    mongo: str


def abort(msg: str):
    sys.exit(msg)


def parse_args(args: list[str]) -> Flags:
    headless = False
    verbose = False
    json = False
    dataJson = None
    mongo = None

    for i in range(1, len(args)):
        arg = args[i].lower()

        if arg.startswith('--'):
            flag = arg[2:]
            if flag == 'headless':
                headless = True
            elif flag == 'json':
                if dataJson is not None:
                    abort('`--dataJson` is mutually exclusive with `--json`.')

                json = True
            elif flag.startswith('dataJson='):
                if json:
                    abort('`--json` is mutually exclusive with `--dataJson`.')

                filePath = flag[9:].strip()
                if not filePath.endswith('.json') or not path.isfile(filePath):
                    abort('Invalid dataJson path.')
        else:
            abort(f'Unrecognized flag: {arg}')

    return Flags(headless, verbose, json, dataJson, mongo)


def main(args: list[str]):
    flags = parse_args(args)

    if not flags.verbose:
        logger.addFilter()

    if flags.dataJson:
        try:
            file = open(flags.dataJson, 'r')
        except IOError as e:
            abort(f'Unable to open `.json` file.\n{e}')

        data = json.load(file)
    else:
        try:
            data = scrape_raw_info()
        except RuntimeError as e:
            abort(f'Failed scrape raw info.{e}')

        if flags.json:
            try:
                file = open(f'scrape-results-{datetime.now().isoformat()}', 'w')

                json.dump(data, file)
                file.close()
            except IOError as e:
                abort(f'Unable to write JSON.\n{e}')

    (course, staff) = normalize_info(data[:2])

    push_info(course, staff, data[2])


if __name__ == '__main__':
    main(sys.argv)
