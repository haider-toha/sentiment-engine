"""Mastodon/Fediverse collector."""

import httpx
from typing import List, Optional
from datetime import datetime

from app.collectors.base import BaseCollector, CollectedArticle
from app.utils.logging import get_logger
from app.config import get_settings

logger = get_logger(__name__)
settings = get_settings()

# Language to country mapping (rough approximation)
LANGUAGE_COUNTRY = {
    "en": None,  # Too generic
    "de": "DE",
    "fr": "FR",
    "es": "ES",
    "it": "IT",
    "pt": "BR",
    "ja": "JP",
    "ko": "KR",
    "zh": "CN",
    "ru": "RU",
    "nl": "NL",
    "pl": "PL",
    "sv": "SE",
    "no": "NO",
    "da": "DK",
    "fi": "FI",
}


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
        """Collect posts from Mastodon public timeline."""
        articles = []
        
        try:
            # Fetch from public timeline (no auth required)
            posts = await self._fetch_public_timeline(limit=100)
            
            for post in posts:
                article = self._parse_post(post)
                if article:
                    articles.append(article)
            
            logger.info("Fetched Mastodon posts", count=len(articles))
        
        except Exception as e:
            logger.warning("Failed to fetch Mastodon timeline", error=str(e))
        
        return articles
    
    async def _fetch_public_timeline(self, limit: int = 100) -> List[dict]:
        """Fetch public timeline from Mastodon instance."""
        url = f"{self.base_url}/api/v1/timelines/public"
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
            import re
            text_content = re.sub(r'<[^>]+>', '', content)
            text_content = text_content.strip()
            
            if len(text_content) < 20:
                return None
            
            # Get language and infer country
            language = post.get("language")
            country_code = LANGUAGE_COUNTRY.get(language) if language else None
            
            # Parse timestamp
            created_at = post.get("created_at")
            published_at = None
            if created_at:
                try:
                    published_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    pass
            
            # Get account info for source name
            account = post.get("account", {})
            username = account.get("username", "unknown")
            instance = account.get("url", self.base_url).split("/")[2] if account.get("url") else "mastodon.social"
            
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

