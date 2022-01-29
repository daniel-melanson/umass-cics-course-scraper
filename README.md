# UMass CICS Course/Staff Scraper

Information pertaining to UMass CICS courses is spread out. UMass Spire has a total list of courses, but some of those courses have not been scheduled in decades. The CICS website has a list of courses, but enrollment information is not always present or reliable. This program will scrapes various UMass websites for CICS related course information and aggregates it into a MongoDB.

## Usage

- `./src/main update` - Preforms an update routine on the database. Removes courses and staff that were not found during the scrape.

- `./src/main rebase` - Deletes all collections and indices. Pushes information to database, reestablishes indices.

### Flags

- `--headless` - Launch browser in headless mode.
