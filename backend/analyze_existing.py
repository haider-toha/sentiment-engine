"""
Script to run sentiment analysis on existing articles that don't have scores yet.
Run from the backend directory with: python analyze_existing.py
"""

import sys
from datetime import datetime

# Add app to path
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models import Article
from app.services.sentiment import SentimentAnalyzer
from app.services.aggregator import SentimentAggregator
from app.config import get_settings

settings = get_settings()


def analyze_unscored_articles(batch_size: int = 100):
    """Analyze all articles that don't have sentiment scores."""
    
    print("=" * 60)
    print("SENTIMENT ANALYSIS FOR EXISTING ARTICLES")
    print("=" * 60)
    
    # Initialize sentiment analyzer
    print("\n[1/4] Loading sentiment model...")
    analyzer = SentimentAnalyzer()
    
    if not analyzer.is_ready:
        print("ERROR: Failed to load sentiment model!")
        return
    
    print(f"      Model loaded: {settings.sentiment_model}")
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Count unanalyzed articles
        total_unanalyzed = db.query(Article).filter(
            Article.sentiment_score.is_(None)
        ).count()
        
        print(f"\n[2/4] Found {total_unanalyzed:,} articles without sentiment scores")
        
        if total_unanalyzed == 0:
            print("      Nothing to analyze!")
            return
        
        # Process in batches
        print(f"\n[3/4] Analyzing in batches of {batch_size}...")
        
        processed = 0
        analyzed = 0
        batch_num = 0
        last_id = 0  # Track last processed ID to avoid infinite loop
        
        while True:
            # Get next batch of unanalyzed articles, ordered by ID
            # Use ID > last_id to ensure we don't re-process failed articles
            articles = db.query(Article).filter(
                Article.sentiment_score.is_(None),
                Article.id > last_id
            ).order_by(Article.id).limit(batch_size).all()
            
            if not articles:
                break
            
            batch_num += 1
            last_id = articles[-1].id  # Update last processed ID
            
            # Prepare texts for analysis
            texts = [
                f"{a.title} {a.content or ''}"[:512]
                for a in articles
            ]
            
            # Run batch inference
            results = analyzer.analyze_batch(texts)
            
            # Update articles with results
            batch_analyzed = 0
            for article, result in zip(articles, results):
                if result:
                    article.sentiment_score = result.score
                    article.sentiment_label = result.label
                    article.confidence = result.confidence
                    article.analyzed_at = datetime.utcnow()
                    batch_analyzed += 1
                else:
                    # Mark as attempted but failed (set score to 0 = neutral)
                    article.sentiment_score = 0.0
                    article.sentiment_label = "skipped"
                    article.analyzed_at = datetime.utcnow()
            
            db.commit()
            
            processed += len(articles)
            analyzed += batch_analyzed
            
            # Progress update
            pct = (processed / total_unanalyzed) * 100
            print(f"      Batch {batch_num}: {processed:,}/{total_unanalyzed:,} ({pct:.1f}%) - {batch_analyzed} scored")
        
        print(f"\n[4/4] Aggregating sentiment by country...")
        aggregator = SentimentAggregator(db)
        results = aggregator.aggregate_hourly()
        print(f"      Aggregated {len(results)} countries")
        
        print("\n" + "=" * 60)
        print(f"COMPLETE: Analyzed {analyzed:,} of {processed:,} articles")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        db.rollback()
        raise
    
    finally:
        db.close()


if __name__ == "__main__":
    # You can adjust batch size based on your GPU memory
    # Larger = faster but uses more memory
    batch_size = 64 if settings.use_gpu else 16
    
    analyze_unscored_articles(batch_size=batch_size)

