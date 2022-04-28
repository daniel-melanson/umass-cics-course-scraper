from scraper.scraper import ScrapeResult, SCRAPE_VERSION


def normalize_info(data: ScrapeResult):
    assert data.version == SCRAPE_VERSION
