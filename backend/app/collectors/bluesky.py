"""Bluesky social network collector.

Bluesky is a decentralized social network with a public API.
We collect posts from verified news accounts and trending topics.
"""

import httpx
import re
from typing import List, Optional
from datetime import datetime

from app.collectors.base import BaseCollector, CollectedArticle
from app.utils.geo import detect_country_from_text
from app.utils.logging import get_logger

logger = get_logger(__name__)


# Bluesky AT Protocol API
BSKY_PUBLIC_API = "https://public.api.bsky.app"

# Verified news accounts to follow on Bluesky
# Format: handle (without @)
NEWS_ACCOUNTS = [
    # Major News Outlets
    "nytimes.bsky.social",
    "washingtonpost.com",
    "wsj.com",
    "reuters.com",
    "apnews.com",
    "bbc.bsky.social",
    "theguardian.com",
    "npr.org",
    "cnn.com",
    "economist.com",
    "ft.com",
    "politico.com",
    "thehill.com",
    "axios.com",
    "vox.com",
    "theatlantic.com",
    "newyorker.com",
    "time.com",
    "newsweek.com",
    "usatoday.com",
    "latimes.com",
    "chicagotribune.com",
    "bostonglobe.com",
    "sfchronicle.com",
    
    # Tech News
    "theverge.com",
    "wired.com",
    "arstechnica.com",
    "techcrunch.com",
    "engadget.com",
    "gizmodo.com",
    "mashable.com",
    "zdnet.com",
    "cnet.com",
    
    # International
    "dw.com",
    "france24.com",
    "aljazeera.com",
    "scmp.com",
    "japantimes.co.jp",
    "straitstimes.com",
    "abc.net.au",
    "cbc.ca",
    "globeandmail.com",
    "thestar.com",
    
    # Journalists and reporters
    "kaitlancollins.bsky.social",
    "maggieNYT.bsky.social",
    "jaaborough.bsky.social",
]

# News-related search terms for discovery
SEARCH_TERMS = [
    "breaking news",
    "ukraine",
    "congress",
    "parliament",
    "election",
    "climate",
    "economy",
    "covid",
    "health",
    "technology",
    "AI artificial intelligence",
    "middle east",
    "europe",
    "asia",
    "africa",
    "latin america",
]


class BlueskyCollector(BaseCollector):
    """Collector for Bluesky social network posts."""
    
    source_type = "bluesky"
    
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
    
    def is_configured(self) -> bool:
        """Bluesky public API doesn't require authentication."""
        return True
    
    async def collect(self) -> List[CollectedArticle]:
        """Collect posts from news accounts and trending topics."""
        articles = []
        
        # Collect from known news accounts
        for handle in NEWS_ACCOUNTS[:30]:  # Limit to prevent rate limiting
            try:
                account_posts = await self._fetch_author_feed(handle)
                articles.extend(account_posts)
            except Exception as e:
                logger.debug("Failed to fetch Bluesky account", handle=handle, error=str(e))
        
        # Search for news-related posts
        for term in SEARCH_TERMS[:10]:
            try:
                search_posts = await self._search_posts(term)
                articles.extend(search_posts)
            except Exception as e:
                logger.debug("Failed to search Bluesky", term=term, error=str(e))
        
        # Deduplicate by URL
        seen_urls = set()
        unique_articles = []
        for article in articles:
            if article.url not in seen_urls:
                seen_urls.add(article.url)
                unique_articles.append(article)
        
        logger.info("Fetched Bluesky posts", count=len(unique_articles))
        return unique_articles
    
    async def _fetch_author_feed(self, handle: str) -> List[CollectedArticle]:
        """Fetch recent posts from a specific author."""
        articles = []
        
        try:
            url = f"{BSKY_PUBLIC_API}/xrpc/app.bsky.feed.getAuthorFeed"
            params = {"actor": handle, "limit": 20}
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            feed = data.get("feed", [])
            
            for item in feed:
                article = self._parse_post(item.get("post", {}), handle)
                if article:
                    articles.append(article)
        
        except Exception as e:
            raise Exception(f"Failed to fetch feed for {handle}: {e}")
        
        return articles
    
    async def _search_posts(self, query: str) -> List[CollectedArticle]:
        """Search for posts matching a query."""
        articles = []
        
        try:
            url = f"{BSKY_PUBLIC_API}/xrpc/app.bsky.feed.searchPosts"
            params = {"q": query, "limit": 25}
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            posts = data.get("posts", [])
            
            for post in posts:
                article = self._parse_post(post)
                if article:
                    articles.append(article)
        
        except Exception as e:
            raise Exception(f"Failed to search for '{query}': {e}")
        
        return articles
    
    def _parse_post(self, post: dict, default_handle: str = None) -> Optional[CollectedArticle]:
        """Parse a Bluesky post into a CollectedArticle."""
        try:
            record = post.get("record", {})
            text = record.get("text", "")
            
            if not text or len(text) < 20:
                return None
            
            # Get post URI and create URL
            uri = post.get("uri", "")
            cid = post.get("cid", "")
            
            # Extract handle from author
            author = post.get("author", {})
            handle = author.get("handle", default_handle or "unknown")
            display_name = author.get("displayName", handle)
            
            # Create Bluesky web URL
            # Format: https://bsky.app/profile/{handle}/post/{rkey}
            rkey = uri.split("/")[-1] if uri else cid
            url = f"https://bsky.app/profile/{handle}/post/{rkey}"
            
            # Parse timestamp
            published_at = None
            created_at = record.get("createdAt")
            if created_at:
                try:
                    published_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    pass
            
            # Detect country from text
            country_code = detect_country_from_text(text, text[:100])
            
            # Use first 200 chars as title
            title = text[:200].replace("\n", " ")
            if len(text) > 200:
                title += "..."
            
            return CollectedArticle(
                source_type=self.source_type,
                source_name=f"@{handle}",
                title=title,
                url=url,
                content=text,
                country_code=country_code,
                published_at=published_at,
            )
        
        except Exception as e:
            logger.debug("Failed to parse Bluesky post", error=str(e))
            return None
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

