"""API routes for the sentiment engine."""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.database import get_db
from app.models import Article, CountrySentiment
from app.schemas import (
    HealthStatus,
    GlobalSentiment,
    CountryData,
    CountryDetail,
    ArticlePreview,
    HourlyTrendItem,
)
from app.services.aggregator import SentimentAggregator
from app.services.scheduler import scheduler_status, trigger_collection
from app.utils.geo import get_country_name

router = APIRouter()


@router.get("/health", response_model=HealthStatus)
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint with system status."""
    from app.config import get_settings
    
    settings = get_settings()
    status = scheduler_status()

    # Count today's articles
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    articles_today = (
        db.query(func.count(Article.id)).filter(Article.created_at >= today).scalar()
    )

    # Check database
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    # In read-only mode, we're healthy if DB is ok (scheduler won't be running)
    if settings.readonly_mode:
        health_status = "healthy" if db_ok else "degraded"
    else:
        health_status = "healthy" if status["running"] else "degraded"

    return HealthStatus(
        status=health_status,
        last_collection=status["last_collection"],
        articles_today=articles_today or 0,
        model_loaded=not settings.readonly_mode,  # No model in read-only mode
        database_ok=db_ok,
    )


@router.get("/sentiment/global", response_model=GlobalSentiment)
async def get_global_sentiment(db: Session = Depends(get_db)):
    """Get global sentiment overview for all countries."""
    aggregator = SentimentAggregator(db)
    data = aggregator.get_global_sentiment()

    return GlobalSentiment(
        countries=[
            CountryData(
                country_code=c["country_code"],
                country_name=c["country_name"],
                sentiment_score=c["sentiment_score"],
                article_count=c["article_count"],
            )
            for c in data["countries"]
        ],
        global_average=data["global_average"],
        total_articles=data["total_articles"],
        last_updated=data["last_updated"] or datetime.utcnow(),
    )


@router.get("/sentiment/{country_code}", response_model=CountryDetail)
async def get_country_sentiment(
    country_code: str, hours: int = 24, db: Session = Depends(get_db)
):
    """Get detailed sentiment data for a specific country."""
    aggregator = SentimentAggregator(db)
    data = aggregator.get_country_detail(country_code.upper(), hours=hours)

    if not data:
        raise HTTPException(status_code=404, detail="Country not found or no data")

    return CountryDetail(
        country_code=data["country_code"],
        country_name=data["country_name"],
        current_sentiment=data["current_sentiment"],
        article_count=data["article_count"],
        hourly_trend=[
            HourlyTrendItem(
                hour=h["hour"],
                sentiment=h["sentiment"],
                articles=h["articles"],
            )
            for h in data["hourly_trend"]
        ],
        top_headlines=data["top_headlines"],
        source_breakdown=data["source_breakdown"],
    )


@router.get("/headlines/{country_code}")
async def get_country_headlines(
    country_code: str,
    limit: int = 20,
    sentiment: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get recent headlines for a country."""
    query = db.query(Article).filter(
        Article.country_code == country_code.upper(),
        Article.sentiment_score.isnot(None),
    )

    # Filter by sentiment if specified
    if sentiment == "positive":
        query = query.filter(Article.sentiment_score > 0.2)
    elif sentiment == "negative":
        query = query.filter(Article.sentiment_score < -0.2)
    elif sentiment == "neutral":
        query = query.filter(
            Article.sentiment_score >= -0.2, Article.sentiment_score <= 0.2
        )

    # Order by absolute sentiment score (most extreme first)
    headlines = (
        query.order_by(func.abs(Article.sentiment_score).desc()).limit(limit).all()
    )

    return [
        {
            "id": h.id,
            "title": h.title,
            "source_name": h.source_name,
            "source_type": h.source_type,
            "sentiment_score": h.sentiment_score,
            "sentiment_label": h.sentiment_label,
            "url": h.url,
            "published_at": h.published_at,
            "created_at": h.created_at,
        }
        for h in headlines
    ]


@router.get("/trends")
async def get_trends(hours: int = 24, db: Session = Depends(get_db)):
    """Get global sentiment trends over time."""
    since = datetime.utcnow() - timedelta(hours=hours)

    # Get hourly averages across all countries
    hourly = (
        db.query(
            CountrySentiment.hour,
            func.avg(CountrySentiment.weighted_sentiment).label("avg_sentiment"),
            func.sum(CountrySentiment.article_count).label("total_articles"),
            func.count(CountrySentiment.country_code).label("country_count"),
        )
        .filter(CountrySentiment.hour >= since)
        .group_by(CountrySentiment.hour)
        .order_by(CountrySentiment.hour.asc())
        .all()
    )

    return [
        {
            "hour": h.hour,
            "avg_sentiment": h.avg_sentiment,
            "total_articles": h.total_articles,
            "country_count": h.country_count,
        }
        for h in hourly
    ]


@router.get("/sources")
async def get_source_stats(db: Session = Depends(get_db)):
    """Get statistics by data source."""
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    stats = (
        db.query(
            Article.source_type,
            func.count(Article.id).label("count"),
            func.avg(Article.sentiment_score).label("avg_sentiment"),
        )
        .filter(Article.created_at >= today)
        .group_by(Article.source_type)
        .all()
    )

    return [
        {
            "source_type": s.source_type,
            "article_count": s.count,
            "avg_sentiment": s.avg_sentiment,
        }
        for s in stats
    ]


@router.post("/collect/trigger")
async def trigger_collection_job(background_tasks: BackgroundTasks):
    """Manually trigger a data collection job."""
    background_tasks.add_task(trigger_collection)
    return {"message": "Collection job triggered", "status": "running"}
