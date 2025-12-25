# Data collectors - comprehensive global news sources
from app.collectors.rss import RSSCollector
from app.collectors.reddit import RedditCollector
from app.collectors.mastodon import MastodonCollector
from app.collectors.hackernews import HackerNewsCollector
from app.collectors.scraper import WebScraper

# New collectors for maximum global coverage
from app.collectors.gdelt import GDELTCollector
from app.collectors.googlenews import GoogleNewsCollector
from app.collectors.official import OfficialSourcesCollector
from app.collectors.bluesky import BlueskyCollector
from app.collectors.lemmy import LemmyCollector
from app.collectors.wikipedia import WikipediaCollector
from app.collectors.newsapi import NewsDataCollector, CurrentsAPICollector, TheNewsAPICollector

__all__ = [
    # Original collectors
    "RSSCollector",
    "RedditCollector",
    "MastodonCollector",
    "HackerNewsCollector",
    "WebScraper",
    # New collectors for global coverage
    "GDELTCollector",
    "GoogleNewsCollector",
    "OfficialSourcesCollector",
    "BlueskyCollector",
    "LemmyCollector",
    "WikipediaCollector",
    "NewsDataCollector",
    "CurrentsAPICollector",
    "TheNewsAPICollector",
]


def get_all_collectors():
    """Get instances of all configured collectors."""
    return [
        RSSCollector(),
        RedditCollector(),
        MastodonCollector(),
        HackerNewsCollector(),
        WebScraper(),
        GDELTCollector(),
        GoogleNewsCollector(),
        OfficialSourcesCollector(),
        BlueskyCollector(),
        LemmyCollector(),
        WikipediaCollector(),
        NewsDataCollector(),
        CurrentsAPICollector(),
        TheNewsAPICollector(),
    ]
