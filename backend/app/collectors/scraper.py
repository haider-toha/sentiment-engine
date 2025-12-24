"""Generic web scraper for additional news sources."""

import httpx
from bs4 import BeautifulSoup
from typing import List, Optional
from datetime import datetime
import asyncio
import re

from app.collectors.base import BaseCollector, CollectedArticle
from app.utils.geo import get_country_from_source, detect_country_from_text
from app.utils.logging import get_logger

logger = get_logger(__name__)


# Additional news sites to scrape (respecting robots.txt)
SCRAPE_TARGETS = [
    {
        "name": "TechCrunch",
        "url": "https://techcrunch.com/",
        "article_selector": "article.post-block",
        "title_selector": "h2 a",
        "link_selector": "h2 a",
        "country": "US",
    },
    {
        "name": "The Verge",
        "url": "https://www.theverge.com/",
        "article_selector": "div.duet--content-cards--content-card",
        "title_selector": "a h2",
        "link_selector": "a",
        "country": "US",
    },
    {
        "name": "Ars Technica",
        "url": "https://arstechnica.com/",
        "article_selector": "article",
        "title_selector": "h2 a",
        "link_selector": "h2 a",
        "country": "US",
    },
]


class WebScraper(BaseCollector):
    """Web scraper for additional news sources."""
    
    source_type = "scraper"
    
    def __init__(self, timeout: float = 30.0, delay: float = 1.0):
        self.timeout = timeout
        self.delay = delay  # Polite delay between requests
        self.client = httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "SentimentEngine/1.0 (Educational Project)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
        )
    
    def is_configured(self) -> bool:
        """Web scraper doesn't require configuration."""
        return True
    
    async def collect(self) -> List[CollectedArticle]:
        """Scrape articles from configured sources."""
        articles = []
        
        for target in SCRAPE_TARGETS:
            try:
                target_articles = await self._scrape_site(target)
                articles.extend(target_articles)
                logger.info(
                    "Scraped site",
                    site=target["name"],
                    count=len(target_articles)
                )
                
                # Polite delay between sites
                await asyncio.sleep(self.delay)
            
            except Exception as e:
                logger.warning(
                    "Failed to scrape site",
                    site=target["name"],
                    error=str(e)
                )
        
        return articles
    
    async def _scrape_site(self, target: dict) -> List[CollectedArticle]:
        """Scrape a single site."""
        articles = []
        
        try:
            response = await self.client.get(target["url"])
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "lxml")
            
            # Find article elements
            article_elements = soup.select(target["article_selector"])[:20]  # Limit
            
            for element in article_elements:
                article = self._parse_article(element, target)
                if article:
                    articles.append(article)
        
        except Exception as e:
            raise Exception(f"Failed to scrape {target['url']}: {e}")
        
        return articles
    
    def _parse_article(self, element, target: dict) -> Optional[CollectedArticle]:
        """Parse an article element into a CollectedArticle."""
        try:
            # Get title
            title_elem = element.select_one(target["title_selector"])
            if not title_elem:
                return None
            title = title_elem.get_text().strip()
            if not title or len(title) < 10:
                return None
            
            # Get link
            link_elem = element.select_one(target["link_selector"])
            if not link_elem:
                return None
            
            url = link_elem.get("href", "")
            if not url:
                return None
            
            # Make absolute URL if relative
            if url.startswith("/"):
                base = target["url"].rstrip("/")
                url = f"{base}{url}"
            elif not url.startswith("http"):
                return None
            
            # Get summary/description if available
            content = None
            desc_elem = element.select_one("p, .excerpt, .summary, .description")
            if desc_elem:
                content = desc_elem.get_text().strip()
            
            return CollectedArticle(
                source_type=self.source_type,
                source_name=target["name"],
                title=title,
                url=url,
                content=content,
                country_code=target.get("country"),
                published_at=None,  # Hard to reliably parse from scraped content
            )
        
        except Exception as e:
            logger.debug("Failed to parse scraped article", error=str(e))
            return None
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

