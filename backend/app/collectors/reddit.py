"""Reddit collector using PRAW."""

import asyncio
from typing import List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from app.collectors.base import BaseCollector, CollectedArticle
from app.utils.geo import get_country_from_subreddit
from app.utils.logging import get_logger
from app.config import get_settings

logger = get_logger(__name__)
settings = get_settings()

# Subreddits to monitor for news and sentiment
SUBREDDITS = [
    # Global news
    {"name": "worldnews", "country": None, "limit": 100},
    {"name": "news", "country": "US", "limit": 50},
    {"name": "politics", "country": "US", "limit": 50},
    
    # Country-specific
    {"name": "unitedkingdom", "country": "GB", "limit": 30},
    {"name": "ukpolitics", "country": "GB", "limit": 30},
    {"name": "europe", "country": None, "limit": 30},
    {"name": "france", "country": "FR", "limit": 20},
    {"name": "germany", "country": "DE", "limit": 20},
    {"name": "de", "country": "DE", "limit": 20},
    {"name": "india", "country": "IN", "limit": 30},
    {"name": "australia", "country": "AU", "limit": 20},
    {"name": "canada", "country": "CA", "limit": 20},
    {"name": "japan", "country": "JP", "limit": 20},
    {"name": "brasil", "country": "BR", "limit": 20},
    {"name": "mexico", "country": "MX", "limit": 20},
]


class RedditCollector(BaseCollector):
    """Collector for Reddit posts."""
    
    source_type = "reddit"
    
    def __init__(self):
        self._reddit = None
        self._executor = ThreadPoolExecutor(max_workers=2)
    
    def is_configured(self) -> bool:
        """Check if Reddit credentials are configured."""
        return bool(settings.reddit_client_id and settings.reddit_client_secret)
    
    def _get_reddit(self):
        """Get or create Reddit instance (must be done in sync context)."""
        if self._reddit is None:
            try:
                import praw
                self._reddit = praw.Reddit(
                    client_id=settings.reddit_client_id,
                    client_secret=settings.reddit_client_secret,
                    user_agent=settings.reddit_user_agent,
                )
            except Exception as e:
                logger.error("Failed to initialize Reddit client", error=str(e))
                return None
        return self._reddit
    
    async def collect(self) -> List[CollectedArticle]:
        """Collect posts from monitored subreddits."""
        if not self.is_configured():
            logger.warning("Reddit collector not configured - skipping")
            return []
        
        articles = []
        loop = asyncio.get_event_loop()
        
        for sub_config in SUBREDDITS:
            try:
                # Run PRAW in thread pool since it's synchronous
                sub_articles = await loop.run_in_executor(
                    self._executor,
                    self._fetch_subreddit,
                    sub_config
                )
                articles.extend(sub_articles)
                logger.info(
                    "Fetched subreddit",
                    subreddit=sub_config["name"],
                    count=len(sub_articles)
                )
            except Exception as e:
                logger.warning(
                    "Failed to fetch subreddit",
                    subreddit=sub_config["name"],
                    error=str(e)
                )
        
        return articles
    
    def _fetch_subreddit(self, sub_config: dict) -> List[CollectedArticle]:
        """Fetch posts from a subreddit (synchronous)."""
        articles = []
        
        try:
            reddit = self._get_reddit()
            if not reddit:
                return articles
            
            subreddit = reddit.subreddit(sub_config["name"])
            
            for post in subreddit.hot(limit=sub_config["limit"]):
                # Skip stickied posts and self posts without much content
                if post.stickied:
                    continue
                
                article = self._parse_post(post, sub_config)
                if article:
                    articles.append(article)
        
        except Exception as e:
            raise Exception(f"Failed to fetch r/{sub_config['name']}: {e}")
        
        return articles
    
    def _parse_post(self, post, sub_config: dict) -> CollectedArticle:
        """Parse a Reddit post into a CollectedArticle."""
        try:
            # Determine country
            country_code = sub_config.get("country")
            if not country_code:
                country_code = get_country_from_subreddit(sub_config["name"])
            
            # Get content
            content = post.selftext if post.selftext else post.title
            
            return CollectedArticle(
                source_type=self.source_type,
                source_name=f"r/{sub_config['name']}",
                title=post.title,
                url=f"https://reddit.com{post.permalink}",
                content=content[:2000] if content else None,  # Limit content length
                country_code=country_code,
                published_at=datetime.fromtimestamp(post.created_utc),
            )
        
        except Exception as e:
            logger.debug("Failed to parse Reddit post", error=str(e))
            return None

