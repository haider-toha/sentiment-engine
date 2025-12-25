"""Lemmy collector - Federated Reddit alternative.

Lemmy is a decentralized, federated link aggregator similar to Reddit.
We collect posts from major instances covering news and world events.
"""

import httpx
from typing import List, Optional
from datetime import datetime

from app.collectors.base import BaseCollector, CollectedArticle
from app.utils.geo import detect_country_from_text
from app.utils.logging import get_logger

logger = get_logger(__name__)


# Major Lemmy instances with news communities
LEMMY_INSTANCES = [
    {
        "base": "https://lemmy.world",
        "communities": [
            {"name": "world", "country": None},
            {"name": "news", "country": None},
            {"name": "worldnews", "country": None},
            {"name": "politics", "country": None},
            {"name": "europe", "country": None},
            {"name": "unitedkingdom", "country": "GB"},
            {"name": "technology", "country": None},
        ],
    },
    {
        "base": "https://lemmy.ml",
        "communities": [
            {"name": "worldnews", "country": None},
            {"name": "news", "country": None},
            {"name": "politics", "country": None},
            {"name": "technology", "country": None},
        ],
    },
    {
        "base": "https://lemm.ee",
        "communities": [
            {"name": "world", "country": None},
            {"name": "news", "country": None},
            {"name": "europe", "country": None},
        ],
    },
    {
        "base": "https://sh.itjust.works",
        "communities": [
            {"name": "news", "country": None},
            {"name": "world", "country": None},
            {"name": "politics", "country": "US"},
        ],
    },
    {
        "base": "https://feddit.de",
        "communities": [
            {"name": "nachrichten", "country": "DE"},
            {"name": "germany", "country": "DE"},
            {"name": "dach", "country": "DE"},
        ],
    },
    {
        "base": "https://feddit.nl",
        "communities": [
            {"name": "nieuws", "country": "NL"},
            {"name": "netherlands", "country": "NL"},
        ],
    },
    {
        "base": "https://feddit.it",
        "communities": [
            {"name": "italy", "country": "IT"},
            {"name": "news", "country": "IT"},
        ],
    },
    {
        "base": "https://aussie.zone",
        "communities": [
            {"name": "australia", "country": "AU"},
            {"name": "news", "country": "AU"},
        ],
    },
    {
        "base": "https://jlai.lu",
        "communities": [
            {"name": "france", "country": "FR"},
            {"name": "actualite", "country": "FR"},
        ],
    },
    {
        "base": "https://sopuli.xyz",
        "communities": [
            {"name": "worldnews", "country": None},
            {"name": "finland", "country": "FI"},
        ],
    },
]


class LemmyCollector(BaseCollector):
    """Collector for Lemmy federated link aggregator."""

    source_type = "lemmy"

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    def is_configured(self) -> bool:
        """Lemmy API is public."""
        return True

    async def collect(self) -> List[CollectedArticle]:
        """Collect posts from Lemmy instances."""
        articles = []

        for instance in LEMMY_INSTANCES:
            for community in instance["communities"]:
                try:
                    community_posts = await self._fetch_community(
                        instance["base"], community["name"], community.get("country")
                    )
                    articles.extend(community_posts)
                except Exception as e:
                    logger.debug(
                        "Failed to fetch Lemmy community",
                        instance=instance["base"],
                        community=community["name"],
                        error=str(e),
                    )

        logger.info("Fetched Lemmy posts", count=len(articles))
        return articles

    async def _fetch_community(
        self, base_url: str, community: str, default_country: Optional[str]
    ) -> List[CollectedArticle]:
        """Fetch posts from a Lemmy community."""
        articles = []

        try:
            # Lemmy API endpoint
            url = f"{base_url}/api/v3/post/list"
            params = {
                "community_name": community,
                "sort": "Hot",
                "limit": 25,
            }

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            posts = data.get("posts", [])

            for post_data in posts:
                article = self._parse_post(post_data, base_url, default_country)
                if article:
                    articles.append(article)

        except Exception as e:
            raise Exception(f"Failed to fetch {base_url}/c/{community}: {e}")

        return articles

    def _parse_post(
        self, post_data: dict, base_url: str, default_country: Optional[str]
    ) -> Optional[CollectedArticle]:
        """Parse a Lemmy post into a CollectedArticle."""
        try:
            post = post_data.get("post", {})
            community = post_data.get("community", {})

            title = post.get("name")
            if not title:
                return None

            # Get URL - prefer external URL, fallback to Lemmy post
            url = post.get("url")
            if not url:
                post_id = post.get("id")
                if post_id:
                    url = f"{base_url}/post/{post_id}"
                else:
                    return None

            # Get content
            content = post.get("body", title)

            # Parse timestamp
            published_at = None
            published = post.get("published")
            if published:
                try:
                    published_at = datetime.fromisoformat(
                        published.replace("Z", "+00:00")
                    )
                except (ValueError, TypeError):
                    pass

            # Detect country
            country_code = default_country
            if not country_code:
                country_code = detect_country_from_text(content, title)

            # Source name
            community_name = community.get("name", "unknown")
            instance_name = base_url.replace("https://", "").split("/")[0]

            return CollectedArticle(
                source_type=self.source_type,
                source_name=f"{community_name}@{instance_name}",
                title=title,
                url=url,
                content=content[:2000] if content else None,
                country_code=country_code,
                published_at=published_at,
            )

        except Exception as e:
            logger.debug("Failed to parse Lemmy post", error=str(e))
            return None

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
