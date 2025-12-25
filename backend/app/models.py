"""SQLAlchemy database models."""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from app.database import Base


class Article(Base):
    """Articles and posts from all data sources."""

    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)

    # Source information
    source_type = Column(
        String(20), nullable=False
    )  # rss, reddit, mastodon, hn, scraper
    source_name = Column(String(100), nullable=False)  # e.g., "BBC News", "r/worldnews"

    # Geographic data
    country_code = Column(String(2), nullable=True, index=True)  # ISO 3166-1 alpha-2

    # Content
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=True)
    url = Column(String(2048), unique=True, nullable=False)

    # Sentiment analysis results
    sentiment_score = Column(Float, nullable=True)  # -1 to 1
    sentiment_label = Column(String(20), nullable=True)  # positive, negative, neutral
    confidence = Column(Float, nullable=True)  # 0 to 1

    # Timestamps
    published_at = Column(DateTime, nullable=True)
    analyzed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes for common queries
    __table_args__ = (
        Index("idx_articles_country_created", "country_code", "created_at"),
        Index("idx_articles_source_created", "source_type", "created_at"),
    )


class CountrySentiment(Base):
    """Hourly aggregated sentiment per country."""

    __tablename__ = "country_sentiment"

    id = Column(Integer, primary_key=True, index=True)

    country_code = Column(String(2), nullable=False, index=True)
    hour = Column(DateTime, nullable=False, index=True)

    # Aggregated metrics
    avg_sentiment = Column(Float, nullable=False)
    weighted_sentiment = Column(Float, nullable=True)  # Source credibility weighted
    article_count = Column(Integer, nullable=False, default=0)

    # Top articles for this period
    top_positive_id = Column(Integer, ForeignKey("articles.id"), nullable=True)
    top_negative_id = Column(Integer, ForeignKey("articles.id"), nullable=True)

    # Relationships
    top_positive = relationship("Article", foreign_keys=[top_positive_id])
    top_negative = relationship("Article", foreign_keys=[top_negative_id])

    __table_args__ = (
        UniqueConstraint("country_code", "hour", name="uq_country_hour"),
        Index("idx_country_sentiment_lookup", "country_code", "hour"),
    )


class DataSource(Base):
    """Registered data sources and their metadata."""

    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, index=True)

    source_type = Column(
        String(20), nullable=False
    )  # rss, reddit, mastodon, hn, scraper
    name = Column(String(100), nullable=False, unique=True)
    url = Column(String(2048), nullable=False)
    country_code = Column(String(2), nullable=True)  # Default country for this source

    # Credibility score for weighted sentiment
    credibility_score = Column(Float, default=1.0)  # 0.0 to 1.0

    # Status
    is_active = Column(
        Integer, default=1
    )  # Using Integer for SQLite/PostgreSQL compatibility
    last_fetched = Column(DateTime, nullable=True)
    fetch_error_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
