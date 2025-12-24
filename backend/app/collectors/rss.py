"""RSS feed collector for major news publications."""

import feedparser
import httpx
from typing import List, Optional
from datetime import datetime
from time import mktime

from app.collectors.base import BaseCollector, CollectedArticle
from app.utils.geo import get_country_from_source
from app.utils.logging import get_logger

logger = get_logger(__name__)


# Major RSS feeds from around the world
RSS_FEEDS = [
    # International
    {"name": "Reuters World", "url": "https://feeds.reuters.com/Reuters/worldNews", "country": None},
    {"name": "AP News", "url": "https://rsshub.app/apnews/topics/world-news", "country": None},
    
    # United States
    {"name": "NPR News", "url": "https://feeds.npr.org/1001/rss.xml", "country": "US"},
    {"name": "PBS NewsHour", "url": "https://www.pbs.org/newshour/feeds/rss/headlines", "country": "US"},
    
    # United Kingdom
    {"name": "BBC News", "url": "https://feeds.bbci.co.uk/news/rss.xml", "country": "GB"},
    {"name": "The Guardian", "url": "https://www.theguardian.com/world/rss", "country": "GB"},
    {"name": "Sky News", "url": "https://feeds.skynews.com/feeds/rss/world.xml", "country": "GB"},
    
    # Europe
    {"name": "Deutsche Welle", "url": "https://rss.dw.com/rdf/rss-en-all", "country": "DE"},
    {"name": "France 24", "url": "https://www.france24.com/en/rss", "country": "FR"},
    {"name": "Euronews", "url": "https://www.euronews.com/rss?level=theme&name=news", "country": None},
    
    # Asia
    {"name": "NHK World", "url": "https://www3.nhk.or.jp/rss/news/cat0.xml", "country": "JP"},
    {"name": "CNA", "url": "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml", "country": "SG"},
    {"name": "Times of India", "url": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms", "country": "IN"},
    
    # Middle East
    {"name": "Al Jazeera", "url": "https://www.aljazeera.com/xml/rss/all.xml", "country": "QA"},
    
    # Australia
    {"name": "ABC Australia", "url": "https://www.abc.net.au/news/feed/2942460/rss.xml", "country": "AU"},
    
    # Canada
    {"name": "CBC News", "url": "https://www.cbc.ca/cmlink/rss-topstories", "country": "CA"},
    
    # Africa
    {"name": "AllAfrica", "url": "https://allafrica.com/tools/headlines/rdf/latest/headlines.rdf", "country": None},
]


class RSSCollector(BaseCollector):
    """Collector for RSS news feeds."""
    
    source_type = "rss"
    
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout, follow_redirects=True)
    
    def is_configured(self) -> bool:
        """RSS feeds don't require configuration."""
        return True
    
    async def collect(self) -> List[CollectedArticle]:
        """Collect articles from all RSS feeds."""
        articles = []
        
        for feed_config in RSS_FEEDS:
            try:
                feed_articles = await self._fetch_feed(feed_config)
                articles.extend(feed_articles)
                logger.info(
                    "Fetched RSS feed",
                    feed=feed_config["name"],
                    count=len(feed_articles)
                )
            except Exception as e:
                logger.warning(
                    "Failed to fetch RSS feed",
                    feed=feed_config["name"],
                    error=str(e)
                )
        
        return articles
    
    async def _fetch_feed(self, feed_config: dict) -> List[CollectedArticle]:
        """Fetch and parse a single RSS feed."""
        articles = []
        
        try:
            response = await self.client.get(feed_config["url"])
            response.raise_for_status()
            
            feed = feedparser.parse(response.text)
            
            for entry in feed.entries[:50]:  # Limit per feed
                article = self._parse_entry(entry, feed_config)
                if article:
                    articles.append(article)
        
        except Exception as e:
            raise Exception(f"Failed to fetch {feed_config['url']}: {e}")
        
        return articles
    
    def _parse_entry(self, entry, feed_config: dict) -> Optional[CollectedArticle]:
        """Parse a feed entry into a CollectedArticle."""
        try:
            # Get URL
            url = getattr(entry, 'link', None)
            if not url:
                return None
            
            # Get title
            title = getattr(entry, 'title', None)
            if not title:
                return None
            
            # Get content/description
            content = None
            if hasattr(entry, 'summary'):
                content = entry.summary
            elif hasattr(entry, 'description'):
                content = entry.description
            
            # Parse published date
            published_at = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published_at = datetime.fromtimestamp(mktime(entry.published_parsed))
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published_at = datetime.fromtimestamp(mktime(entry.updated_parsed))
            
            # Get country
            country_code = feed_config.get("country")
            if not country_code:
                country_code = get_country_from_source(feed_config["name"])
            
            return CollectedArticle(
                source_type=self.source_type,
                source_name=feed_config["name"],
                title=title.strip(),
                url=url,
                content=content,
                country_code=country_code,
                published_at=published_at,
            )
        
        except Exception as e:
            logger.debug("Failed to parse RSS entry", error=str(e))
            return None
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

