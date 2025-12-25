"""Application configuration using pydantic-settings."""

from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus, urlparse, urlunparse


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Supabase - loaded from .env
    supabase_url: str = ""
    supabase_key: str = ""
    
    # Database connection - separate fields for proper encoding
    db_user: str = ""
    db_password: str = ""
    db_host: str = ""
    db_port: str = "6543"
    db_name: str = "postgres"
    
    @property
    def database_url(self) -> str:
        if self.db_password and self.db_host and self.db_user:
            # URL-encode password to handle special characters
            encoded_password = quote_plus(self.db_password)
            return f"postgresql://{self.db_user}:{encoded_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        return "sqlite:///./sentiment.db"
    
    # Reddit API (optional - works without but limited)
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "SentimentEngine/1.0"
    
    # Mastodon API (optional)
    mastodon_access_token: str = ""
    mastodon_api_base_url: str = "https://mastodon.social"
    
    # ============================================
    # NEWS API KEYS (all optional, free tiers available)
    # ============================================
    
    # NewsData.io - Free tier: 200 requests/day
    # Get key at: https://newsdata.io/
    newsdata_api_key: str = ""
    
    # Currents API - Free tier: 600 requests/day
    # Get key at: https://currentsapi.services/
    currents_api_key: str = ""
    
    # TheNewsAPI - Free tier: 100 requests/day
    # Get key at: https://www.thenewsapi.com/
    thenewsapi_api_key: str = ""
    
    # ============================================
    # ML Settings
    # ============================================
    use_gpu: bool = True  # Set to False for cloud deployment
    
    # Sentiment model options:
    # - cardiffnlp/twitter-xlm-roberta-base-sentiment (multilingual, recommended)
    # - cardiffnlp/twitter-roberta-base-sentiment-latest (English, very accurate)
    # - nlptown/bert-base-multilingual-uncased-sentiment (6 languages, 5-star)
    # - ProsusAI/finbert (financial text only)
    # - siebert/sentiment-roberta-large-english (English, high accuracy)
    sentiment_model: str = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
    batch_size: int = 32
    
    # Scheduler
    collection_interval_hours: int = 1
    
    # Data retention
    retention_days: int = 30
    
    # API
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://localhost:3002",
        "http://localhost:3003",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "*"  # Allow all origins in development
    ]
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",  # Ignore extra fields like old DATABASE_URL
    }


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
