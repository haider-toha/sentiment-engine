"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from app.config import get_settings
from app.database import init_db
from app.utils.logging import setup_logging, get_logger
from app.api.routes import router
from app.services.scheduler import start_scheduler, stop_scheduler, scheduler_status
from app.services.sentiment import SentimentAnalyzer

settings = get_settings()
logger = get_logger(__name__)

# Global sentiment analyzer instance
sentiment_analyzer: SentimentAnalyzer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global sentiment_analyzer

    # Startup
    setup_logging()

    if settings.readonly_mode:
        logger.info("Starting Sentiment Engine in READ-ONLY mode...")
    else:
        logger.info("Starting Sentiment Engine...")

    # Initialize database
    logger.info("Initializing database...")
    init_db()

    # Only load ML model and scheduler in full mode (not read-only)
    if not settings.readonly_mode:
        # Initialize sentiment analyzer
        logger.info("Loading sentiment model...", model=settings.sentiment_model)
        sentiment_analyzer = SentimentAnalyzer()
        app.state.sentiment_analyzer = sentiment_analyzer

        # Start scheduler
        logger.info("Starting scheduler...")
        start_scheduler()
    else:
        logger.info("Skipping ML model and scheduler (read-only mode)")

    logger.info("Sentiment Engine started successfully!")

    yield

    # Shutdown
    logger.info("Shutting down Sentiment Engine...")
    if not settings.readonly_mode:
        stop_scheduler()
    logger.info("Shutdown complete.")


app = FastAPI(
    title="Global Sentiment Engine",
    description="Real-time sentiment analysis from global news and social media",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware - allow all origins in development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Global Sentiment Engine",
        "version": "1.0.0",
        "docs": "/docs",
    }
