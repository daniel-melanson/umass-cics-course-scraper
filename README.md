# UMass CICS Course/Staff Scraper

Information pertaining to UMass CICS courses is spread out. UMass Spire has a total list of courses, but some of those courses have not been scheduled in decades. The CICS website has a list of courses, but enrollment information is not always present or reliable. This program will scrape various UMass websites for CICS related course information. From there, the data is normalized, matched, and analyzed using NLTK. After which, the data is pushed to a MongoDB.

## Flags

- `--headless` - Optional. Launch browser in headless mode.

- `--dump` - Optional. Output scraping results to `.json` in the current working directory.

- `--json=PATH_TO_JSON` - Optional. Mutually exclusive with `--dump`. Skip the scraping routine, use the data contained in the `.json` instead. (File should be created from `--dump`.)

- `--verbose` - Optional. Run the process in verbose mode. Produces a `.log` file.

- `--mongo=MONGO_CONN_STR` - Optional. If provided, the process will attempt to push all scraped and normalized data into a MongoDB.

## Outline

- Parse arguments
- If no data json
  - Scrape raw information from spire + umass websites (scraper)
  - Do rudimentary matching between courses and course frequency
- If should output
  - Output the raw data into a json
- Pass raw data to text processor
- TO DO
