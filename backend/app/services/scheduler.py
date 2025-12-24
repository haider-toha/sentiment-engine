"""APScheduler-based task scheduler for data collection."""

from datetime import datetime
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import get_settings
from app.database import SessionLocal
from app.models import Article
from app.collectors import (
    RSSCollector,
    RedditCollector,
    MastodonCollector,
    HackerNewsCollector,
    WebScraper,
)
from app.services.sentiment import SentimentAnalyzer
from app.services.aggregator import SentimentAggregator
from app.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Global scheduler instance
_scheduler: Optional[AsyncIOScheduler] = None
_last_collection: Optional[datetime] = None
_sentiment_analyzer: Optional[SentimentAnalyzer] = None


def scheduler_status() -> dict:
    """Get scheduler status."""
    return {
        "running": _scheduler.running if _scheduler else False,
        "last_collection": _last_collection,
    }


def start_scheduler():
    """Start the background scheduler."""
    global _scheduler, _sentiment_analyzer
    
    if _scheduler is not None:
        return
    
    # Initialize sentiment analyzer
    _sentiment_analyzer = SentimentAnalyzer()
    
    _scheduler = AsyncIOScheduler()
    
    # Schedule collection job
    _scheduler.add_job(
        run_collection_job,
        IntervalTrigger(hours=settings.collection_interval_hours),
        id="collection_job",
        name="Collect and analyze data",
        next_run_time=datetime.now(),  # Run immediately on startup
    )
    
    # Schedule cleanup job (daily)
    _scheduler.add_job(
        run_cleanup_job,
        IntervalTrigger(days=1),
        id="cleanup_job",
        name="Clean up old data",
    )
    
    _scheduler.start()
    logger.info("Scheduler started", interval_hours=settings.collection_interval_hours)


def stop_scheduler():
    """Stop the background scheduler."""
    global _scheduler
    
    if _scheduler:
        _scheduler.shutdown()
        _scheduler = None
        logger.info("Scheduler stopped")


async def run_collection_job():
    """Main collection job - fetches data, analyzes sentiment, and aggregates."""
    global _last_collection
    
    logger.info("Starting collection job...")
    
    db = SessionLocal()
    
    try:
        # Initialize collectors
        collectors = [
            RSSCollector(),
            RedditCollector(),
            MastodonCollector(),
            HackerNewsCollector(),
            WebScraper(),
        ]
        
        all_articles = []
        
        # Collect from all sources
        for collector in collectors:
            if not collector.is_configured():
                logger.info(f"Skipping {collector.source_type} - not configured")
                continue
            
            try:
                articles = await collector.collect()
                all_articles.extend(articles)
                logger.info(
                    f"Collected from {collector.source_type}",
                    count=len(articles)
                )
            except Exception as e:
                logger.error(
                    f"Collection failed for {collector.source_type}",
                    error=str(e)
                )
        
        logger.info("Total articles collected", count=len(all_articles))
        
        # Save articles to database (skip duplicates by URL)
        new_articles = []
        seen_urls = set()
        
        for collected in all_articles:
            # Skip if we've already seen this URL in this batch
            if collected.url in seen_urls:
                continue
            seen_urls.add(collected.url)
            
            # Check if URL already exists in database
            existing = db.query(Article).filter(Article.url == collected.url).first()
            if existing:
                continue
            
            article = Article(
                source_type=collected.source_type,
                source_name=collected.source_name,
                title=collected.title,
                content=collected.content,
                url=collected.url,
                country_code=collected.country_code,
                published_at=collected.published_at,
            )
            db.add(article)
            new_articles.append(article)
        
        db.commit()
        logger.info("New articles saved", count=len(new_articles))
        
        # Analyze sentiment for new articles
        if new_articles and _sentiment_analyzer and _sentiment_analyzer.is_ready:
            texts = [
                f"{a.title} {a.content or ''}"[:512]
                for a in new_articles
            ]
            
            results = _sentiment_analyzer.analyze_batch(texts)
            
            analyzed_count = 0
            for article, result in zip(new_articles, results):
                if result:
                    article.sentiment_score = result.score
                    article.sentiment_label = result.label
                    article.confidence = result.confidence
                    article.analyzed_at = datetime.utcnow()
                    analyzed_count += 1
            
            db.commit()
            logger.info("Sentiment analysis complete", analyzed=analyzed_count)
        
        # Aggregate by country
        aggregator = SentimentAggregator(db)
        aggregator.aggregate_hourly()
        
        _last_collection = datetime.utcnow()
        logger.info("Collection job complete")
        
        # Cleanup collectors
        for collector in collectors:
            if hasattr(collector, 'close'):
                await collector.close()
    
    except Exception as e:
        logger.error("Collection job failed", error=str(e))
        db.rollback()
    
    finally:
        db.close()


async def run_cleanup_job():
    """Cleanup job - removes old data."""
    logger.info("Starting cleanup job...")
    
    db = SessionLocal()
    
    try:
        aggregator = SentimentAggregator(db)
        deleted = aggregator.cleanup_old_data(days=settings.retention_days)
        logger.info("Cleanup job complete", deleted=deleted)
    
    except Exception as e:
        logger.error("Cleanup job failed", error=str(e))
        db.rollback()
    
    finally:
        db.close()


async def trigger_collection():
    """Manually trigger a collection job."""
    await run_collection_job()

