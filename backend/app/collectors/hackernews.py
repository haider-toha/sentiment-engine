"""Hacker News collector using the official Firebase API."""

import httpx
import asyncio
from typing import List, Optional
from datetime import datetime

from app.collectors.base import BaseCollector, CollectedArticle
from app.utils.geo import detect_country_from_text
from app.utils.logging import get_logger

logger = get_logger(__name__)

HN_API_BASE = "https://hacker-news.firebaseio.com/v0"


class HackerNewsCollector(BaseCollector):
    """Collector for Hacker News stories."""

    source_type = "hn"

    def __init__(self, timeout: float = 30.0, max_stories: int = 200):
        self.timeout = timeout
        self.max_stories = max_stories  # Increased for more data
        self.client = httpx.AsyncClient(timeout=timeout)

    def is_configured(self) -> bool:
        """HN API is public, no configuration needed."""
        return True

    async def collect(self) -> List[CollectedArticle]:
        """Collect top and new stories from Hacker News."""
        articles = []

        try:
            # Get both top and new story IDs for more coverage
            top_ids = await self._get_story_ids("topstories")
            new_ids = await self._get_story_ids("newstories")
            best_ids = await self._get_story_ids("beststories")

            # Combine and dedupe
            all_ids = list(dict.fromkeys(top_ids[:100] + new_ids[:50] + best_ids[:50]))

            # Fetch stories in batches for efficiency
            batch_size = 25
            for i in range(0, min(len(all_ids), self.max_stories), batch_size):
                batch_ids = all_ids[i : i + batch_size]
                batch_stories = await asyncio.gather(
                    *[self._get_story(story_id) for story_id in batch_ids],
                    return_exceptions=True,
                )

                for story in batch_stories:
                    if isinstance(story, CollectedArticle):
                        articles.append(story)

            logger.info("Fetched Hacker News stories", count=len(articles))

        except Exception as e:
            logger.warning("Failed to fetch Hacker News", error=str(e))

        return articles

    async def _get_story_ids(self, endpoint: str) -> List[int]:
        """Get list of story IDs from a specific endpoint."""
        try:
            url = f"{HN_API_BASE}/{endpoint}.json"
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json() or []
        except Exception:
            return []

    async def _get_top_stories(self) -> List[int]:
        """Get list of top story IDs (for backwards compatibility)."""
        return await self._get_story_ids("topstories")

    async def _get_story(self, story_id: int) -> Optional[CollectedArticle]:
        """Fetch a single story by ID."""
        try:
            url = f"{HN_API_BASE}/item/{story_id}.json"
            response = await self.client.get(url)
            response.raise_for_status()

            item = response.json()
            if not item:
                return None

            return self._parse_story(item)

        except Exception as e:
            logger.debug("Failed to fetch HN story", story_id=story_id, error=str(e))
            return None

    def _parse_story(self, item: dict) -> Optional[CollectedArticle]:
        """Parse a HN story into a CollectedArticle."""
        try:
            # Only process stories (not comments, jobs, etc.)
            if item.get("type") != "story":
                return None

            title = item.get("title")
            if not title:
                return None

            # Get URL (external link or HN discussion)
            url = item.get("url")
            if not url:
                url = f"https://news.ycombinator.com/item?id={item['id']}"

            # Content is the title + text if it's an Ask HN / Show HN
            content = title
            if item.get("text"):
                content = f"{title}\n\n{item['text']}"

            # Parse timestamp
            published_at = None
            if item.get("time"):
                published_at = datetime.fromtimestamp(item["time"])

            # Detect country from content - HN is international
            # Default to US only if no country can be detected
            country_code = detect_country_from_text(content, title)
            if not country_code:
                country_code = "US"  # HN is primarily US-based tech community

            return CollectedArticle(
                source_type=self.source_type,
                source_name="Hacker News",
                title=title,
                url=url,
                content=content,
                country_code=country_code,
                published_at=published_at,
            )

        except Exception as e:
            logger.debug("Failed to parse HN story", error=str(e))
            return None

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
