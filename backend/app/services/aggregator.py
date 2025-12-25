"""Sentiment aggregation service for country-level statistics."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models import Article, CountrySentiment
from app.utils.geo import get_country_name, get_all_country_codes
from app.utils.logging import get_logger

logger = get_logger(__name__)


# Source credibility weights
SOURCE_WEIGHTS = {
    "rss": 1.0,  # News outlets - high credibility
    "hn": 0.8,  # Hacker News - tech-focused, fairly reliable
    "reddit": 0.6,  # Reddit - mixed credibility
    "mastodon": 0.5,  # Social media - lower weight
    "scraper": 0.9,  # Scraped news sites - high credibility
}


class SentimentAggregator:
    """Aggregates sentiment data by country and time period."""

    def __init__(self, db: Session):
        self.db = db

    def aggregate_hourly(self, hour: Optional[datetime] = None) -> Dict[str, dict]:
        """
        Aggregate sentiment by country for a given hour.

        Args:
            hour: The hour to aggregate (defaults to current hour)

        Returns:
            Dict mapping country codes to aggregated data
        """
        if hour is None:
            hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)

        hour_start = hour.replace(minute=0, second=0, microsecond=0)
        hour_end = hour_start + timedelta(hours=1)

        # Query articles with sentiment in this hour
        articles = (
            self.db.query(Article)
            .filter(
                and_(
                    Article.created_at >= hour_start,
                    Article.created_at < hour_end,
                    Article.sentiment_score.isnot(None),
                    Article.country_code.isnot(None),
                )
            )
            .all()
        )

        # Group by country
        country_data: Dict[str, dict] = {}

        for article in articles:
            code = article.country_code
            if code not in country_data:
                country_data[code] = {
                    "scores": [],
                    "weighted_scores": [],
                    "articles": [],
                }

            weight = SOURCE_WEIGHTS.get(article.source_type, 0.5)

            country_data[code]["scores"].append(article.sentiment_score)
            country_data[code]["weighted_scores"].append(
                (article.sentiment_score, weight)
            )
            country_data[code]["articles"].append(article)

        # Calculate aggregates and save to database
        results = {}

        for country_code, data in country_data.items():
            if not data["scores"]:
                continue

            # Simple average
            avg_sentiment = sum(data["scores"]) / len(data["scores"])

            # Weighted average
            total_weight = sum(w for _, w in data["weighted_scores"])
            weighted_sentiment = (
                sum(s * w for s, w in data["weighted_scores"]) / total_weight
            )

            # Find top positive and negative articles
            sorted_articles = sorted(data["articles"], key=lambda a: a.sentiment_score)
            top_negative = sorted_articles[0] if sorted_articles else None
            top_positive = sorted_articles[-1] if sorted_articles else None

            # Upsert country sentiment record
            existing = (
                self.db.query(CountrySentiment)
                .filter(
                    and_(
                        CountrySentiment.country_code == country_code,
                        CountrySentiment.hour == hour_start,
                    )
                )
                .first()
            )

            if existing:
                existing.avg_sentiment = avg_sentiment
                existing.weighted_sentiment = weighted_sentiment
                existing.article_count = len(data["articles"])
                existing.top_positive_id = top_positive.id if top_positive else None
                existing.top_negative_id = top_negative.id if top_negative else None
            else:
                country_sentiment = CountrySentiment(
                    country_code=country_code,
                    hour=hour_start,
                    avg_sentiment=avg_sentiment,
                    weighted_sentiment=weighted_sentiment,
                    article_count=len(data["articles"]),
                    top_positive_id=top_positive.id if top_positive else None,
                    top_negative_id=top_negative.id if top_negative else None,
                )
                self.db.add(country_sentiment)

            results[country_code] = {
                "avg_sentiment": avg_sentiment,
                "weighted_sentiment": weighted_sentiment,
                "article_count": len(data["articles"]),
                "country_name": get_country_name(country_code),
            }

        self.db.commit()
        logger.info(
            "Aggregated hourly sentiment", countries=len(results), hour=hour_start
        )

        return results

    def get_global_sentiment(self) -> Dict[str, any]:
        """Get current global sentiment overview."""
        # Get most recent hour with data
        latest = (
            self.db.query(CountrySentiment)
            .order_by(CountrySentiment.hour.desc())
            .first()
        )

        if not latest:
            return {
                "countries": [],
                "global_average": 0.0,
                "total_articles": 0,
                "last_updated": None,
            }

        # Get all countries for latest hour
        hour = latest.hour
        country_sentiments = (
            self.db.query(CountrySentiment).filter(CountrySentiment.hour == hour).all()
        )

        countries = []
        total_articles = 0
        weighted_sum = 0.0

        for cs in country_sentiments:
            countries.append(
                {
                    "country_code": cs.country_code,
                    "country_name": get_country_name(cs.country_code),
                    "sentiment_score": cs.weighted_sentiment or cs.avg_sentiment,
                    "article_count": cs.article_count,
                }
            )
            total_articles += cs.article_count
            weighted_sum += (
                cs.weighted_sentiment or cs.avg_sentiment
            ) * cs.article_count

        global_average = weighted_sum / total_articles if total_articles > 0 else 0.0

        return {
            "countries": countries,
            "global_average": global_average,
            "total_articles": total_articles,
            "last_updated": hour,
        }

    def get_country_detail(self, country_code: str, hours: int = 24) -> Optional[dict]:
        """Get detailed sentiment data for a country."""
        # Get hourly trend
        since = datetime.utcnow() - timedelta(hours=hours)
        hourly = (
            self.db.query(CountrySentiment)
            .filter(
                and_(
                    CountrySentiment.country_code == country_code,
                    CountrySentiment.hour >= since,
                )
            )
            .order_by(CountrySentiment.hour.asc())
            .all()
        )

        if not hourly:
            return None

        # Get headlines with highest absolute sentiment scores
        headlines = (
            self.db.query(Article)
            .filter(
                and_(
                    Article.country_code == country_code,
                    Article.created_at >= since,
                    Article.sentiment_score.isnot(None),
                )
            )
            .order_by(func.abs(Article.sentiment_score).desc())
            .limit(20)
            .all()
        )

        # Get source breakdown
        source_counts = (
            self.db.query(Article.source_type, func.count(Article.id))
            .filter(
                and_(
                    Article.country_code == country_code,
                    Article.created_at >= since,
                )
            )
            .group_by(Article.source_type)
            .all()
        )

        latest = hourly[-1] if hourly else None

        return {
            "country_code": country_code,
            "country_name": get_country_name(country_code),
            "current_sentiment": latest.weighted_sentiment if latest else 0.0,
            "article_count": sum(h.article_count for h in hourly),
            "hourly_trend": [
                {
                    "hour": h.hour,
                    "sentiment": h.weighted_sentiment or h.avg_sentiment,
                    "articles": h.article_count,
                }
                for h in hourly
            ],
            "top_headlines": [
                {
                    "id": a.id,
                    "title": a.title,
                    "source_name": a.source_name,
                    "source_type": a.source_type,
                    "sentiment_score": a.sentiment_score,
                    "sentiment_label": a.sentiment_label,
                    "published_at": a.published_at,
                    "url": a.url,
                }
                for a in headlines
            ],
            "source_breakdown": dict(source_counts),
        }

    def cleanup_old_data(self, days: int = 30) -> int:
        """Remove data older than specified days."""
        cutoff = datetime.utcnow() - timedelta(days=days)

        # Delete old articles
        deleted_articles = (
            self.db.query(Article).filter(Article.created_at < cutoff).delete()
        )

        # Delete old aggregates
        deleted_aggregates = (
            self.db.query(CountrySentiment)
            .filter(CountrySentiment.hour < cutoff)
            .delete()
        )

        self.db.commit()

        logger.info(
            "Cleaned up old data",
            deleted_articles=deleted_articles,
            deleted_aggregates=deleted_aggregates,
        )

        return deleted_articles + deleted_aggregates
