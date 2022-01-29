#! python3

from email.policy import default
from enum import Enum
import sys
from typing import Tuple


class Mode(Enum):
    REBASE = 1
    UPDATE = 2


def parse_args(args: list[str]) -> Tuple[Mode, bool]:
    is_headless = False
    mode = None
    for i in range(1, len(args)):
        arg = args[i].lower()

        if arg.startswith("--"):
            match arg[2:]:
                case "headless":
                    is_headless = True
        else:
            if mode is not None:
                sys.exit("Mode is already defined.")

            match arg:
                case "rebase":
                    mode = Mode.REBASE
                case "update":
                    mode = Mode.UPDATE
                case _:
                    sys.exit(f"Unrecognized mode: {arg}")

    return (mode, is_headless)


def main(args: list[str]):
    (mode, is_headless) = parse_args(args)
    

if __name__ == '__main__':
    main(sys.argv)
