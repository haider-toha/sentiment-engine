"""Pydantic schemas for API request/response models."""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


# ============ Article Schemas ============


class ArticleBase(BaseModel):
    """Base article schema."""

    source_type: str
    source_name: str
    country_code: Optional[str] = None
    title: str
    content: Optional[str] = None
    url: str
    published_at: Optional[datetime] = None


class ArticleCreate(ArticleBase):
    """Schema for creating an article."""

    pass


class ArticleSentiment(BaseModel):
    """Sentiment analysis result for an article."""

    sentiment_score: float = Field(..., ge=-1, le=1)
    sentiment_label: str
    confidence: float = Field(..., ge=0, le=1)


class Article(ArticleBase):
    """Full article schema with all fields."""

    id: int
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    confidence: Optional[float] = None
    analyzed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ArticlePreview(BaseModel):
    """Lightweight article preview for lists."""

    id: int
    title: str
    source_name: str
    source_type: Optional[str] = None
    country_code: Optional[str] = None
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    url: Optional[str] = None
    published_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============ Country Sentiment Schemas ============


class CountrySentimentBase(BaseModel):
    """Base country sentiment schema."""

    country_code: str
    avg_sentiment: float
    article_count: int


class CountrySentiment(CountrySentimentBase):
    """Full country sentiment with hour."""

    id: int
    hour: datetime
    weighted_sentiment: Optional[float] = None

    class Config:
        from_attributes = True


class HourlyTrendItem(BaseModel):
    """Hourly trend data point."""

    hour: datetime
    sentiment: float
    articles: int


class CountryData(BaseModel):
    """Country data for the globe visualization."""

    country_code: str
    country_name: str
    sentiment_score: float = Field(..., ge=-1, le=1)
    article_count: int
    trend: Optional[float] = None  # Change from previous hour


class GlobalSentiment(BaseModel):
    """Global sentiment overview."""

    countries: list[CountryData]
    global_average: float
    total_articles: int
    last_updated: datetime


class CountryDetail(BaseModel):
    """Detailed data for a single country."""

    country_code: str
    country_name: str
    current_sentiment: float
    article_count: int
    hourly_trend: list[HourlyTrendItem]
    top_headlines: list[dict]
    source_breakdown: dict[str, int]


# ============ Data Source Schemas ============


class DataSourceCreate(BaseModel):
    """Schema for creating a data source."""

    source_type: str
    name: str
    url: str
    country_code: Optional[str] = None
    credibility_score: float = 1.0


class DataSource(DataSourceCreate):
    """Full data source schema."""

    id: int
    is_active: bool
    last_fetched: Optional[datetime] = None
    fetch_error_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Health Check Schema ============


class HealthStatus(BaseModel):
    """API health status."""

    status: str
    last_collection: Optional[datetime] = None
    articles_today: int = 0
    model_loaded: bool = False
    database_ok: bool = False
