"""Free News API collectors - NewsData.io, Currents API, TheNewsAPI.

These APIs provide free tiers for accessing news from around the world.
Add API keys to your .env file to enable them.
"""

import httpx
from typing import List, Optional
from datetime import datetime

from app.collectors.base import BaseCollector, CollectedArticle
from app.utils.geo import get_country_code, detect_country_from_text
from app.utils.logging import get_logger
from app.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


# Countries to fetch news for (ISO 3166-1 alpha-2 codes)
TARGET_COUNTRIES = [
    "us",
    "gb",
    "ca",
    "au",
    "nz",  # English-speaking
    "de",
    "fr",
    "es",
    "it",
    "pt",
    "nl",
    "be",
    "at",
    "ch",  # Western Europe
    "se",
    "no",
    "dk",
    "fi",
    "is",  # Nordic
    "pl",
    "cz",
    "hu",
    "ro",
    "bg",
    "gr",
    "ua",
    "ru",  # Eastern Europe
    "jp",
    "kr",
    "cn",
    "tw",
    "hk",
    "sg",
    "my",
    "id",
    "th",
    "vn",
    "ph",  # Asia
    "in",
    "pk",
    "bd",
    "lk",
    "np",  # South Asia
    "il",
    "sa",
    "ae",
    "eg",
    "tr",
    "ir",
    "iq",
    "lb",
    "jo",  # Middle East
    "za",
    "ng",
    "ke",
    "et",
    "gh",
    "tz",  # Africa
    "br",
    "mx",
    "ar",
    "cl",
    "co",
    "pe",
    "ve",  # Latin America
]


class NewsDataCollector(BaseCollector):
    """Collector for NewsData.io API (free tier: 200 requests/day)."""

    source_type = "newsdata"

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        self.api_key = getattr(settings, "newsdata_api_key", None)
        self.base_url = "https://newsdata.io/api/1/news"

    def is_configured(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)

    async def collect(self) -> List[CollectedArticle]:
        """Collect news from NewsData.io for multiple countries."""
        if not self.is_configured():
            logger.debug("NewsData.io not configured - skipping")
            return []

        articles = []

        # Fetch for major countries (limit API calls for free tier)
        for country in TARGET_COUNTRIES[:15]:
            try:
                country_articles = await self._fetch_country(country)
                articles.extend(country_articles)
            except Exception as e:
                logger.debug(
                    "Failed to fetch NewsData.io", country=country, error=str(e)
                )

        logger.info("Fetched NewsData.io articles", count=len(articles))
        return articles

    async def _fetch_country(self, country: str) -> List[CollectedArticle]:
        """Fetch news for a specific country."""
        articles = []

        try:
            params = {
                "apikey": self.api_key,
                "country": country,
                "language": "en",
            }

            response = await self.client.get(self.base_url, params=params)
            response.raise_for_status()

            data = response.json()

            if data.get("status") != "success":
                return articles

            for item in data.get("results", []):
                article = self._parse_article(item, country.upper())
                if article:
                    articles.append(article)

        except Exception as e:
            raise Exception(f"NewsData.io error for {country}: {e}")

        return articles

    def _parse_article(self, item: dict, country: str) -> Optional[CollectedArticle]:
        """Parse a NewsData.io article."""
        try:
            title = item.get("title")
            url = item.get("link")

            if not title or not url:
                return None

            # Parse date
            published_at = None
            pubdate = item.get("pubDate")
            if pubdate:
                try:
                    published_at = datetime.fromisoformat(
                        pubdate.replace("Z", "+00:00")
                    )
                except (ValueError, TypeError):
                    pass

            return CollectedArticle(
                source_type=self.source_type,
                source_name=item.get("source_id", "NewsData"),
                title=title,
                url=url,
                content=item.get("description"),
                country_code=country,
                published_at=published_at,
            )

        except Exception as e:
            logger.debug("Failed to parse NewsData article", error=str(e))
            return None

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


class CurrentsAPICollector(BaseCollector):
    """Collector for Currents API (free tier: 600 requests/day)."""

    source_type = "currents"

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        self.api_key = getattr(settings, "currents_api_key", None)
        self.base_url = "https://api.currentsapi.services/v1"

    def is_configured(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)

    async def collect(self) -> List[CollectedArticle]:
        """Collect news from Currents API."""
        if not self.is_configured():
            logger.debug("Currents API not configured - skipping")
            return []

        articles = []

        # Fetch latest news
        try:
            latest = await self._fetch_latest()
            articles.extend(latest)
        except Exception as e:
            logger.debug("Failed to fetch Currents latest", error=str(e))

        # Fetch by region
        regions = [
            "us",
            "eu",
            "asia",
            "africa",
            "middle_east",
            "latin_america",
            "oceania",
        ]
        for region in regions:
            try:
                region_articles = await self._fetch_region(region)
                articles.extend(region_articles)
            except Exception as e:
                logger.debug(
                    "Failed to fetch Currents region", region=region, error=str(e)
                )

        logger.info("Fetched Currents API articles", count=len(articles))
        return articles

    async def _fetch_latest(self) -> List[CollectedArticle]:
        """Fetch latest news."""
        articles = []

        try:
            params = {"apiKey": self.api_key, "language": "en"}
            response = await self.client.get(
                f"{self.base_url}/latest-news", params=params
            )
            response.raise_for_status()

            data = response.json()

            for item in data.get("news", []):
                article = self._parse_article(item)
                if article:
                    articles.append(article)

        except Exception as e:
            raise Exception(f"Currents API error: {e}")

        return articles

    async def _fetch_region(self, region: str) -> List[CollectedArticle]:
        """Fetch news for a region."""
        articles = []

        region_map = {
            "us": "United States",
            "eu": "Europe",
            "asia": "Asia",
            "africa": "Africa",
            "middle_east": "Middle East",
            "latin_america": "South America",
            "oceania": "Australia",
        }

        try:
            params = {
                "apiKey": self.api_key,
                "language": "en",
                "country": region_map.get(region, region),
            }
            response = await self.client.get(
                f"{self.base_url}/latest-news", params=params
            )
            response.raise_for_status()

            data = response.json()

            for item in data.get("news", []):
                article = self._parse_article(item)
                if article:
                    articles.append(article)

        except Exception as e:
            raise Exception(f"Currents API error for {region}: {e}")

        return articles

    def _parse_article(self, item: dict) -> Optional[CollectedArticle]:
        """Parse a Currents API article."""
        try:
            title = item.get("title")
            url = item.get("url")

            if not title or not url:
                return None

            # Parse date
            published_at = None
            published = item.get("published")
            if published:
                try:
                    published_at = datetime.fromisoformat(
                        published.replace("Z", "+00:00")
                    )
                except (ValueError, TypeError):
                    pass

            # Get country from article or detect
            country = item.get("country")
            country_code = None
            if country:
                if len(country) == 2:
                    country_code = country.upper()
                else:
                    country_code = get_country_code(country)

            if not country_code:
                country_code = detect_country_from_text(
                    item.get("description", ""), title
                )

            return CollectedArticle(
                source_type=self.source_type,
                source_name=item.get("author", "Currents"),
                title=title,
                url=url,
                content=item.get("description"),
                country_code=country_code,
                published_at=published_at,
            )

        except Exception as e:
            logger.debug("Failed to parse Currents article", error=str(e))
            return None

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


class TheNewsAPICollector(BaseCollector):
    """Collector for TheNewsAPI (free tier: 100 requests/day)."""

    source_type = "thenewsapi"

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        self.api_key = getattr(settings, "thenewsapi_api_key", None)
        self.base_url = "https://api.thenewsapi.com/v1/news"

    def is_configured(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)

    async def collect(self) -> List[CollectedArticle]:
        """Collect news from TheNewsAPI."""
        if not self.is_configured():
            logger.debug("TheNewsAPI not configured - skipping")
            return []

        articles = []

        # Fetch top news
        try:
            top = await self._fetch_top()
            articles.extend(top)
        except Exception as e:
            logger.debug("Failed to fetch TheNewsAPI top", error=str(e))

        # Fetch by locale
        locales = ["us", "gb", "au", "ca", "de", "fr", "jp", "in", "br", "mx"]
        for locale in locales:
            try:
                locale_articles = await self._fetch_locale(locale)
                articles.extend(locale_articles)
            except Exception as e:
                logger.debug(
                    "Failed to fetch TheNewsAPI locale", locale=locale, error=str(e)
                )

        logger.info("Fetched TheNewsAPI articles", count=len(articles))
        return articles

    async def _fetch_top(self) -> List[CollectedArticle]:
        """Fetch top news."""
        articles = []

        try:
            params = {"api_token": self.api_key, "language": "en", "limit": 50}
            response = await self.client.get(f"{self.base_url}/top", params=params)
            response.raise_for_status()

            data = response.json()

            for item in data.get("data", []):
                article = self._parse_article(item)
                if article:
                    articles.append(article)

        except Exception as e:
            raise Exception(f"TheNewsAPI error: {e}")

        return articles

    async def _fetch_locale(self, locale: str) -> List[CollectedArticle]:
        """Fetch news for a locale."""
        articles = []

        try:
            params = {
                "api_token": self.api_key,
                "locale": locale,
                "limit": 30,
            }
            response = await self.client.get(f"{self.base_url}/top", params=params)
            response.raise_for_status()

            data = response.json()

            for item in data.get("data", []):
                article = self._parse_article(item, locale.upper())
                if article:
                    articles.append(article)

        except Exception as e:
            raise Exception(f"TheNewsAPI error for {locale}: {e}")

        return articles

    def _parse_article(
        self, item: dict, default_country: str = None
    ) -> Optional[CollectedArticle]:
        """Parse a TheNewsAPI article."""
        try:
            title = item.get("title")
            url = item.get("url")

            if not title or not url:
                return None

            # Parse date
            published_at = None
            published = item.get("published_at")
            if published:
                try:
                    published_at = datetime.fromisoformat(
                        published.replace("Z", "+00:00")
                    )
                except (ValueError, TypeError):
                    pass

            # Get country
            country_code = default_country
            locale = item.get("locale")
            if locale and len(locale) >= 2:
                country_code = locale[:2].upper()

            if not country_code:
                country_code = detect_country_from_text(
                    item.get("description", ""), title
                )

            return CollectedArticle(
                source_type=self.source_type,
                source_name=item.get("source", "TheNewsAPI"),
                title=title,
                url=url,
                content=item.get("description"),
                country_code=country_code,
                published_at=published_at,
            )

        except Exception as e:
            logger.debug("Failed to parse TheNewsAPI article", error=str(e))
            return None

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
