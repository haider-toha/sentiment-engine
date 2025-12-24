"""Sentiment analysis service using HuggingFace transformers."""

from typing import List, Optional
from dataclasses import dataclass
import re

from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class SentimentResult:
    """Result of sentiment analysis."""
    score: float  # -1 to 1
    label: str  # positive, negative, neutral
    confidence: float  # 0 to 1


class SentimentAnalyzer:
    """Sentiment analyzer using HuggingFace transformers."""
    
    def __init__(self):
        self._model = None
        self._is_ready = False
        self._load_model()
    
    def _load_model(self):
        """Load the sentiment analysis model."""
        try:
            import torch
            from transformers import pipeline
            
            # Determine device
            if settings.use_gpu and torch.cuda.is_available():
                device = 0
                logger.info("Using GPU for inference", device=torch.cuda.get_device_name(0))
            else:
                device = -1
                logger.info("Using CPU for inference")
            
            # Load model
            self._model = pipeline(
                "sentiment-analysis",
                model=settings.sentiment_model,
                device=device,
                truncation=True,
                max_length=512,
            )
            
            self._is_ready = True
            logger.info("Sentiment model loaded successfully", model=settings.sentiment_model)
        
        except Exception as e:
            logger.error("Failed to load sentiment model", error=str(e))
            self._is_ready = False
    
    @property
    def is_ready(self) -> bool:
        """Check if the model is ready for inference."""
        return self._is_ready
    
    def analyze(self, text: str) -> Optional[SentimentResult]:
        """Analyze sentiment of a single text."""
        if not self._is_ready or not text:
            return None
        
        try:
            # Clean text
            cleaned = self._clean_text(text)
            if len(cleaned) < 10:
                return None
            
            # Run inference
            result = self._model(cleaned[:512])[0]
            
            # Convert to standardized format
            return self._convert_result(result)
        
        except Exception as e:
            logger.debug("Sentiment analysis failed", error=str(e))
            return None
    
    def analyze_batch(self, texts: List[str]) -> List[Optional[SentimentResult]]:
        """Analyze sentiment of multiple texts efficiently."""
        if not self._is_ready or not texts:
            return [None] * len(texts)
        
        try:
            # Clean texts
            cleaned = [self._clean_text(t)[:512] for t in texts]
            
            # Filter out too-short texts but remember indices
            valid_indices = []
            valid_texts = []
            for i, text in enumerate(cleaned):
                if len(text) >= 10:
                    valid_indices.append(i)
                    valid_texts.append(text)
            
            if not valid_texts:
                return [None] * len(texts)
            
            # Batch inference
            results = self._model(
                valid_texts,
                batch_size=settings.batch_size,
                truncation=True,
            )
            
            # Map results back to original indices
            output = [None] * len(texts)
            for idx, result in zip(valid_indices, results):
                output[idx] = self._convert_result(result)
            
            return output
        
        except Exception as e:
            logger.error("Batch sentiment analysis failed", error=str(e))
            return [None] * len(texts)
    
    def _clean_text(self, text: str) -> str:
        """Clean text for analysis."""
        if not text:
            return ""
        
        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _convert_result(self, result: dict) -> SentimentResult:
        """Convert model output to standardized SentimentResult."""
        label = result["label"].lower()
        confidence = result["score"]
        
        # FinBERT uses positive/negative/neutral
        # Convert to score between -1 and 1
        if label == "positive":
            score = confidence
        elif label == "negative":
            score = -confidence
        else:  # neutral
            score = 0.0
        
        return SentimentResult(
            score=score,
            label=label,
            confidence=confidence,
        )

