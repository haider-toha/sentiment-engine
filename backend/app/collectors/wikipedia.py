"""Wikipedia Current Events collector.

Wikipedia maintains a Portal:Current events page that is updated multiple
times daily with major world events. This is an excellent source for
understanding what's happening globally.
"""

import httpx
import re
from typing import List, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

from app.collectors.base import BaseCollector, CollectedArticle
from app.utils.geo import detect_country_from_text
from app.utils.logging import get_logger

logger = get_logger(__name__)


# Wikipedia Current Events API/URLs
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
CURRENT_EVENTS_PAGE = "Portal:Current_events"

# Wikipedia editions by language for international coverage
WIKIPEDIA_EDITIONS = [
    {"lang": "en", "base": "https://en.wikipedia.org", "country": None},
    {"lang": "de", "base": "https://de.wikipedia.org", "country": "DE"},
    {"lang": "fr", "base": "https://fr.wikipedia.org", "country": "FR"},
    {"lang": "es", "base": "https://es.wikipedia.org", "country": "ES"},
    {"lang": "it", "base": "https://it.wikipedia.org", "country": "IT"},
    {"lang": "pt", "base": "https://pt.wikipedia.org", "country": "PT"},
    {"lang": "ru", "base": "https://ru.wikipedia.org", "country": "RU"},
    {"lang": "ja", "base": "https://ja.wikipedia.org", "country": "JP"},
    {"lang": "zh", "base": "https://zh.wikipedia.org", "country": "CN"},
    {
        "lang": "ar",
        "base": "https://ar.wikipedia.org",
        "country": None,
    },  # Arabic - multiple countries
    {"lang": "ko", "base": "https://ko.wikipedia.org", "country": "KR"},
    {"lang": "nl", "base": "https://nl.wikipedia.org", "country": "NL"},
    {"lang": "pl", "base": "https://pl.wikipedia.org", "country": "PL"},
    {"lang": "uk", "base": "https://uk.wikipedia.org", "country": "UA"},
    {"lang": "he", "base": "https://he.wikipedia.org", "country": "IL"},
    {"lang": "sv", "base": "https://sv.wikipedia.org", "country": "SE"},
    {"lang": "vi", "base": "https://vi.wikipedia.org", "country": "VN"},
    {"lang": "id", "base": "https://id.wikipedia.org", "country": "ID"},
    {"lang": "tr", "base": "https://tr.wikipedia.org", "country": "TR"},
    {"lang": "cs", "base": "https://cs.wikipedia.org", "country": "CZ"},
    {"lang": "th", "base": "https://th.wikipedia.org", "country": "TH"},
    {"lang": "el", "base": "https://el.wikipedia.org", "country": "GR"},
    {"lang": "ro", "base": "https://ro.wikipedia.org", "country": "RO"},
    {"lang": "hu", "base": "https://hu.wikipedia.org", "country": "HU"},
    {"lang": "da", "base": "https://da.wikipedia.org", "country": "DK"},
    {"lang": "fi", "base": "https://fi.wikipedia.org", "country": "FI"},
    {"lang": "no", "base": "https://no.wikipedia.org", "country": "NO"},
]


class WikipediaCollector(BaseCollector):
    """Collector for Wikipedia Current Events."""

    source_type = "wikipedia"

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout, follow_redirects=True)

    def is_configured(self) -> bool:
        """Wikipedia is public and free."""
        return True

    async def collect(self) -> List[CollectedArticle]:
        """Collect current events from Wikipedia."""
        articles = []

        # Fetch from multiple language editions
        for edition in WIKIPEDIA_EDITIONS[:10]:  # Limit to main editions
            try:
                edition_articles = await self._fetch_current_events(edition)
                articles.extend(edition_articles)
                logger.debug(
                    "Fetched Wikipedia current events",
                    lang=edition["lang"],
                    count=len(edition_articles),
                )
            except Exception as e:
                logger.debug(
                    "Failed to fetch Wikipedia current events",
                    lang=edition["lang"],
                    error=str(e),
                )

        # Also fetch recent changes to news-related articles
        try:
            recent_news = await self._fetch_recent_news_articles()
            articles.extend(recent_news)
        except Exception as e:
            logger.debug("Failed to fetch recent news articles", error=str(e))

        logger.info("Fetched Wikipedia articles", count=len(articles))
        return articles

    async def _fetch_current_events(self, edition: dict) -> List[CollectedArticle]:
        """Fetch current events from a Wikipedia edition."""
        articles = []

        try:
            # Get the current events page content
            api_url = f"{edition['base']}/w/api.php"

            # Get page titles in Category:Current events
            params = {
                "action": "parse",
                "page": "Portal:Current_events",
                "format": "json",
                "prop": "text",
                "section": 0,
            }

            response = await self.client.get(api_url, params=params)
            response.raise_for_status()

            data = response.json()

            if "parse" not in data:
                return articles

            html_content = data["parse"].get("text", {}).get("*", "")
            if not html_content:
                return articles

            # Parse the HTML to extract events
            soup = BeautifulSoup(html_content, "lxml")

            # Find list items (events)
            for li in soup.find_all("li")[:50]:
                article = self._parse_event(li, edition)
                if article:
                    articles.append(article)

        except Exception as e:
            raise Exception(f"Failed to fetch from {edition['base']}: {e}")

        return articles

    async def _fetch_recent_news_articles(self) -> List[CollectedArticle]:
        """Fetch recently edited news-related Wikipedia articles."""
        articles = []

        try:
            # Get recent changes in news-related categories
            params = {
                "action": "query",
                "list": "recentchanges",
                "rcnamespace": 0,  # Main namespace
                "rclimit": 100,
                "rctype": "edit|new",
                "rcprop": "title|timestamp|comment",
                "format": "json",
            }

            response = await self.client.get(WIKIPEDIA_API, params=params)
            response.raise_for_status()

            data = response.json()
            changes = data.get("query", {}).get("recentchanges", [])

            # Filter for likely news articles (rough heuristic)
            news_keywords = [
                "election",
                "war",
                "conflict",
                "president",
                "minister",
                "government",
                "parliament",
                "protest",
                "crisis",
                "disaster",
                "earthquake",
                "hurricane",
                "pandemic",
                "outbreak",
                "summit",
                "agreement",
                "treaty",
                "death",
                "assassination",
                "coup",
                "referendum",
                "vote",
                "legislation",
                "bill",
                "law",
            ]

            for change in changes:
                title = change.get("title", "").lower()
                comment = (change.get("comment") or "").lower()

                # Check if it's likely news-related
                is_news = any(kw in title or kw in comment for kw in news_keywords)

                if is_news:
                    article = self._parse_recent_change(change)
                    if article:
                        articles.append(article)

        except Exception as e:
            raise Exception(f"Failed to fetch recent changes: {e}")

        return articles

    def _parse_event(self, li_element, edition: dict) -> Optional[CollectedArticle]:
        """Parse a current events list item into a CollectedArticle."""
        try:
            text = li_element.get_text().strip()
            if not text or len(text) < 20:
                return None

            # Get first link as the main topic
            first_link = li_element.find("a")
            if first_link and first_link.get("href"):
                href = first_link.get("href")
                if href.startswith("/wiki/"):
                    url = f"{edition['base']}{href}"
                else:
                    url = f"{edition['base']}/wiki/Portal:Current_events"
            else:
                url = f"{edition['base']}/wiki/Portal:Current_events"

            # Detect country from content
            country_code = edition.get("country")
            if not country_code:
                country_code = detect_country_from_text(text, text[:100])

            # Use text as title (truncated)
            title = text[:250]
            if len(text) > 250:
                title += "..."

            return CollectedArticle(
                source_type=self.source_type,
                source_name=f"Wikipedia ({edition['lang'].upper()})",
                title=title,
                url=url,
                content=text,
                country_code=country_code,
                published_at=datetime.utcnow(),  # Current events are recent
            )

        except Exception as e:
            logger.debug("Failed to parse Wikipedia event", error=str(e))
            return None

    def _parse_recent_change(self, change: dict) -> Optional[CollectedArticle]:
        """Parse a recent change into a CollectedArticle."""
        try:
            title = change.get("title")
            if not title:
                return None

            url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"

            # Parse timestamp
            published_at = None
            timestamp = change.get("timestamp")
            if timestamp:
                try:
                    published_at = datetime.fromisoformat(
                        timestamp.replace("Z", "+00:00")
                    )
                except (ValueError, TypeError):
                    pass

            # Detect country
            country_code = detect_country_from_text(title, change.get("comment", ""))

            return CollectedArticle(
                source_type=self.source_type,
                source_name="Wikipedia (Recent)",
                title=title,
                url=url,
                content=change.get("comment"),
                country_code=country_code,
                published_at=published_at,
            )

        except Exception as e:
            logger.debug("Failed to parse recent change", error=str(e))
            return None

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
