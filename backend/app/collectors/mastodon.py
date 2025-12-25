"""Mastodon/Fediverse collector."""

import httpx
import re
from typing import List, Optional
from datetime import datetime

from app.collectors.base import BaseCollector, CollectedArticle
from app.utils.geo import detect_country_from_text
from app.utils.logging import get_logger
from app.config import get_settings

logger = get_logger(__name__)
settings = get_settings()

# Language to country mapping (rough approximation)
# Uses most common country for each language
LANGUAGE_COUNTRY = {
    "en": None,  # Too generic - English is global
    "de": "DE",  # German → Germany
    "fr": "FR",  # French → France
    "es": "ES",  # Spanish → Spain (could be Latin America too)
    "it": "IT",  # Italian → Italy
    "pt": "PT",  # Portuguese → Portugal (or Brazil)
    "pt-BR": "BR",  # Brazilian Portuguese
    "ja": "JP",  # Japanese → Japan
    "ko": "KR",  # Korean → South Korea
    "zh": "CN",  # Chinese → China
    "zh-TW": "TW",  # Traditional Chinese → Taiwan
    "zh-HK": "HK",  # Hong Kong Chinese
    "ru": "RU",  # Russian → Russia
    "nl": "NL",  # Dutch → Netherlands
    "pl": "PL",  # Polish → Poland
    "sv": "SE",  # Swedish → Sweden
    "no": "NO",  # Norwegian → Norway
    "da": "DK",  # Danish → Denmark
    "fi": "FI",  # Finnish → Finland
    "is": "IS",  # Icelandic → Iceland
    "uk": "UA",  # Ukrainian → Ukraine
    "cs": "CZ",  # Czech → Czech Republic
    "sk": "SK",  # Slovak → Slovakia
    "hu": "HU",  # Hungarian → Hungary
    "ro": "RO",  # Romanian → Romania
    "bg": "BG",  # Bulgarian → Bulgaria
    "el": "GR",  # Greek → Greece
    "tr": "TR",  # Turkish → Turkey
    "ar": None,  # Arabic → too many countries
    "he": "IL",  # Hebrew → Israel
    "fa": "IR",  # Persian/Farsi → Iran
    "hi": "IN",  # Hindi → India
    "bn": "BD",  # Bengali → Bangladesh (or India)
    "ta": "IN",  # Tamil → India (or Sri Lanka)
    "te": "IN",  # Telugu → India
    "mr": "IN",  # Marathi → India
    "th": "TH",  # Thai → Thailand
    "vi": "VN",  # Vietnamese → Vietnam
    "id": "ID",  # Indonesian → Indonesia
    "ms": "MY",  # Malay → Malaysia
    "tl": "PH",  # Tagalog → Philippines
    "lt": "LT",  # Lithuanian → Lithuania
    "lv": "LV",  # Latvian → Latvia
    "et": "EE",  # Estonian → Estonia
    "sr": "RS",  # Serbian → Serbia
    "hr": "HR",  # Croatian → Croatia
    "sl": "SI",  # Slovenian → Slovenia
    "bs": "BA",  # Bosnian → Bosnia
    "mk": "MK",  # Macedonian → North Macedonia
    "sq": "AL",  # Albanian → Albania
    "ka": "GE",  # Georgian → Georgia
    "hy": "AM",  # Armenian → Armenia
    "az": "AZ",  # Azerbaijani → Azerbaijan
    "kk": "KZ",  # Kazakh → Kazakhstan
    "uz": "UZ",  # Uzbek → Uzbekistan
    "sw": None,  # Swahili → Kenya/Tanzania (multiple countries)
    "af": "ZA",  # Afrikaans → South Africa
    "zu": "ZA",  # Zulu → South Africa
}

# Multiple Mastodon instances to fetch from for more coverage
MASTODON_INSTANCES = [
    "https://mastodon.social",
    "https://mas.to",
    "https://mastodon.world",
    "https://techhub.social",
    "https://infosec.exchange",
    "https://journa.host",
    "https://mstdn.social",
    "https://universeodon.com",
]


class MastodonCollector(BaseCollector):
    """Collector for Mastodon public timeline."""

    source_type = "mastodon"

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        self.base_url = settings.mastodon_api_base_url.rstrip("/")

    def is_configured(self) -> bool:
        """Mastodon public timeline works without auth."""
        return True

    async def collect(self) -> List[CollectedArticle]:
        """Collect posts from multiple Mastodon instances."""
        articles = []

        # Collect from main configured instance
        try:
            posts = await self._fetch_public_timeline(self.base_url, limit=100)
            for post in posts:
                article = self._parse_post(post)
                if article:
                    articles.append(article)
            logger.info(
                "Fetched Mastodon posts", instance=self.base_url, count=len(articles)
            )
        except Exception as e:
            logger.warning(
                "Failed to fetch Mastodon timeline",
                instance=self.base_url,
                error=str(e),
            )

        # Also collect from other instances for more coverage
        for instance_url in MASTODON_INSTANCES:
            if instance_url.rstrip("/") == self.base_url:
                continue  # Skip if same as main

            try:
                posts = await self._fetch_public_timeline(instance_url, limit=50)
                instance_articles = []
                for post in posts:
                    article = self._parse_post(post)
                    if article:
                        instance_articles.append(article)
                        articles.append(article)
                logger.info(
                    "Fetched Mastodon posts",
                    instance=instance_url,
                    count=len(instance_articles),
                )
            except Exception as e:
                logger.debug(
                    "Failed to fetch from instance", instance=instance_url, error=str(e)
                )

        return articles

    async def _fetch_public_timeline(
        self, base_url: str, limit: int = 100
    ) -> List[dict]:
        """Fetch public timeline from a Mastodon instance."""
        url = f"{base_url.rstrip('/')}/api/v1/timelines/public"
        params = {"limit": min(limit, 40), "local": False}  # 40 is Mastodon max

        all_posts = []
        max_id = None

        # Paginate to get more posts
        while len(all_posts) < limit:
            if max_id:
                params["max_id"] = max_id

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            posts = response.json()
            if not posts:
                break

            all_posts.extend(posts)
            max_id = posts[-1]["id"]

            if len(posts) < params["limit"]:
                break

        return all_posts[:limit]

    def _parse_post(self, post: dict) -> Optional[CollectedArticle]:
        """Parse a Mastodon post into a CollectedArticle."""
        try:
            # Skip posts without content
            content = post.get("content", "")
            if not content or len(content) < 20:
                return None

            # Skip replies (unless they're substantial)
            if post.get("in_reply_to_id") and len(content) < 100:
                return None

            # Strip HTML tags for plain text
            text_content = re.sub(r"<[^>]+>", "", content)
            text_content = text_content.strip()

            if len(text_content) < 20:
                return None

            # Get language and infer country
            language = post.get("language")
            country_code = LANGUAGE_COUNTRY.get(language) if language else None

            # If no country from language, try to detect from content
            if not country_code:
                country_code = detect_country_from_text(
                    text_content, text_content[:200]
                )

            # Parse timestamp
            created_at = post.get("created_at")
            published_at = None
            if created_at:
                try:
                    published_at = datetime.fromisoformat(
                        created_at.replace("Z", "+00:00")
                    )
                except (ValueError, TypeError):
                    pass

            # Get account info for source name
            account = post.get("account", {})
            username = account.get("username", "unknown")
            instance = (
                account.get("url", "").split("/")[2]
                if account.get("url")
                else "mastodon.social"
            )

            return CollectedArticle(
                source_type=self.source_type,
                source_name=f"@{username}@{instance}",
                title=text_content[:200],  # Use first 200 chars as title
                url=post.get("url") or post.get("uri", ""),
                content=text_content,
                country_code=country_code,
                published_at=published_at,
            )

        except Exception as e:
            logger.debug("Failed to parse Mastodon post", error=str(e))
            return None

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
