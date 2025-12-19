from core.connectors.base import BaseConnector
from core.schemas.messages import ScrapeResult
from selenium.webdriver.common.by import By
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class GenericScraperConnector(BaseConnector):
    @property
    def name(self):
        return "generic_scraper"

    async def scrape(self, driver, params: Dict[str, Any]) -> ScrapeResult:
        logger.info(f"Starting Generic Scraper with params: {params}")
        url = params.get("url")
        selector = params.get("selector")
        
        run_id = params.get("run_id")

        if not url:
            return ScrapeResult(run_id=run_id, success=False, error="URL not provided")

        try:
            driver.get(url)
            data = {}
            if selector:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                data["count"] = len(elements)
                data["texts"] = [el.text for el in elements[:5]]
            
            return ScrapeResult(
                run_id=run_id,
                success=True,
                data={"title": driver.title, "scraped_data": data}
            )
        except Exception as e:
            return ScrapeResult(run_id=run_id, success=False, error=str(e))
