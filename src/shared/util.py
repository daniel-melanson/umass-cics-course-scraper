import re


def clean_text(s: str) -> str:
    s = s.strip()

    while (match := re.search(r"\s{2,}", s)) is not None:
        span = match.span(0)

        s = s[: span[0]] + " " + s[span[1] + 1 :]

    return s
