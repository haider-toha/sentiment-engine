"""Application configuration using pydantic-settings."""

from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "sqlite:///./sentiment.db"
    
    # Reddit API (optional - works without but limited)
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "SentimentEngine/1.0"
    
    # Mastodon API (optional)
    mastodon_access_token: str = ""
    mastodon_api_base_url: str = "https://mastodon.social"
    
    # ML Settings
    use_gpu: bool = True  # Set to False for cloud deployment
    sentiment_model: str = "ProsusAI/finbert"
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
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

