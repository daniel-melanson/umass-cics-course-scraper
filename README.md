# UMass CICS Course/Staff Scraper

Information pertaining to UMass CICS courses is spread out. UMass Spire has a total list of courses, but some of those courses have not been scheduled in decades. The CICS website has a list of courses, but enrollment information is not always present or reliable. This program will scrape various UMass websites for CICS related course information.

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
    - Scrape staff information from [CICS website](https://www.cics.umass.edu/people/all-faculty-staff).
      - Store as a list of dictionaries
    - Scrape [CICS course offerings]() and [Math Department offerings]() from respective websites.
      - Capture:
        - Id (e.g. CS 121)
        - Frequency
        - Title
    - Scrape website published information from [CICS website](https://www.cics.umass.edu/content/spring-22-course-descriptions) and [Math department website]().
      - For each semester scraped, capture:
        - Id
        - Title
        - Description
        - Prerequisites (if present on website)
        - Instructor list
    - Scrape a select category of courses from spire
      - Capture
        - Id
        - Title
        - Credits
        - Enrollment requirements
        - Grading Basis
        - Components
- If should output
  - Output the raw data into a json, with relevant metadata.
- Pass raw data to normalizer
  - In charge of processing and aggregating relevant information
  - TODO: Figure out what default normalizer should do
- Push raw information to database.
