"""Sentiment analysis service using HuggingFace transformers.

Supports multiple models with automatic label mapping:
- cardiffnlp/twitter-xlm-roberta-base-sentiment (multilingual, recommended)
- cardiffnlp/twitter-roberta-base-sentiment-latest (English only)
- nlptown/bert-base-multilingual-uncased-sentiment (5-star rating)
- ProsusAI/finbert (financial text)
- siebert/sentiment-roberta-large-english (high accuracy)
"""

from typing import List, Optional, Dict, Callable
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


# Label mappings for different models
# Maps model output labels to (normalized_label, score_multiplier)
LABEL_MAPPINGS: Dict[str, Dict[str, tuple]] = {
    # Cardiff NLP models use "negative", "neutral", "positive" or LABEL_0/1/2
    "cardiffnlp": {
        "negative": ("negative", -1.0),
        "neutral": ("neutral", 0.0),
        "positive": ("positive", 1.0),
        "label_0": ("negative", -1.0),
        "label_1": ("neutral", 0.0),
        "label_2": ("positive", 1.0),
    },
    # FinBERT uses "positive", "negative", "neutral"
    "finbert": {
        "positive": ("positive", 1.0),
        "negative": ("negative", -1.0),
        "neutral": ("neutral", 0.0),
    },
    # nlptown uses 1-5 star ratings
    "nlptown": {
        "1 star": ("negative", -1.0),
        "2 stars": ("negative", -0.5),
        "3 stars": ("neutral", 0.0),
        "4 stars": ("positive", 0.5),
        "5 stars": ("positive", 1.0),
    },
    # Siebert uses POSITIVE/NEGATIVE
    "siebert": {
        "positive": ("positive", 1.0),
        "negative": ("negative", -1.0),
    },
    # lxyuan distilbert
    "lxyuan": {
        "positive": ("positive", 1.0),
        "negative": ("negative", -1.0),
        "neutral": ("neutral", 0.0),
    },
    # Generic fallback
    "default": {
        "positive": ("positive", 1.0),
        "negative": ("negative", -1.0),
        "neutral": ("neutral", 0.0),
        "pos": ("positive", 1.0),
        "neg": ("negative", -1.0),
        "neu": ("neutral", 0.0),
    },
}


def get_model_type(model_name: str) -> str:
    """Determine the model type from the model name for label mapping."""
    model_lower = model_name.lower()

    if (
        "cardiffnlp" in model_lower
        or "twitter" in model_lower
        and "roberta" in model_lower
    ):
        return "cardiffnlp"
    elif "finbert" in model_lower:
        return "finbert"
    elif "nlptown" in model_lower:
        return "nlptown"
    elif "siebert" in model_lower:
        return "siebert"
    elif "lxyuan" in model_lower:
        return "lxyuan"
    else:
        return "default"


class SentimentAnalyzer:
    """Sentiment analyzer using HuggingFace transformers.

    Supports multilingual sentiment analysis with various models.
    Recommended: cardiffnlp/twitter-xlm-roberta-base-sentiment for multilingual news.
    """

    def __init__(self):
        self._model = None
        self._is_ready = False
        self._model_type = "default"
        self._load_model()

    def _load_model(self):
        """Load the sentiment analysis model."""
        try:
            import torch
            from transformers import (
                pipeline,
                AutoModelForSequenceClassification,
                AutoTokenizer,
            )

            # Determine device
            if settings.use_gpu and torch.cuda.is_available():
                device = 0
                gpu_name = torch.cuda.get_device_name(0)
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
                logger.info(
                    "Using GPU for inference",
                    device=gpu_name,
                    memory_gb=f"{gpu_memory:.1f}",
                )
            else:
                device = -1
                logger.info("Using CPU for inference")

            # Determine model type for label mapping
            self._model_type = get_model_type(settings.sentiment_model)
            logger.info("Model type detected", model_type=self._model_type)

            # Load tokenizer and model explicitly for better control
            tokenizer = AutoTokenizer.from_pretrained(settings.sentiment_model)
            model = AutoModelForSequenceClassification.from_pretrained(
                settings.sentiment_model
            )

            # Create pipeline
            self._model = pipeline(
                "sentiment-analysis",
                model=model,
                tokenizer=tokenizer,
                device=device,
                truncation=True,
                max_length=512,
                top_k=None,  # Return all scores for better analysis
            )

            self._is_ready = True
            logger.info(
                "Sentiment model loaded successfully",
                model=settings.sentiment_model,
                model_type=self._model_type,
            )

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
            result = self._model(cleaned[:512])

            # Handle both single result and list of results (top_k=None returns list)
            if isinstance(result, list) and len(result) > 0:
                if isinstance(result[0], list):
                    # top_k=None returns [[{label, score}, ...]]
                    result = result[0]
                # Find the highest scoring label
                best_result = max(result, key=lambda x: x["score"])
            else:
                best_result = result

            # Convert to standardized format
            return self._convert_result(best_result)

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

            # Batch inference - disable top_k for batch processing (faster)
            results = self._model(
                valid_texts,
                batch_size=settings.batch_size,
                truncation=True,
                top_k=1,  # Only get top result for batch (faster)
            )

            # Map results back to original indices
            output = [None] * len(texts)
            for idx, result in zip(valid_indices, results):
                # Handle nested list from pipeline
                if isinstance(result, list) and len(result) > 0:
                    result = result[0]
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
        text = re.sub(r"https?://\S+", "", text)

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)

        # Remove excessive special characters but keep unicode (for multilingual)
        text = re.sub(r"[#@]\w+", "", text)  # Remove hashtags and mentions

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def _convert_result(self, result: dict) -> SentimentResult:
        """Convert model output to standardized SentimentResult.

        Handles different label formats from various models.
        """
        raw_label = result["label"].lower().strip()
        confidence = result["score"]

        # Get label mapping for this model type
        label_map = LABEL_MAPPINGS.get(self._model_type, LABEL_MAPPINGS["default"])

        # Try to find the label in our mapping
        if raw_label in label_map:
            normalized_label, score_multiplier = label_map[raw_label]
        else:
            # Fallback: try to infer from label content
            if "pos" in raw_label or "5" in raw_label or "4" in raw_label:
                normalized_label, score_multiplier = "positive", 1.0
            elif "neg" in raw_label or "1" in raw_label or "2" in raw_label:
                normalized_label, score_multiplier = "negative", -1.0
            else:
                normalized_label, score_multiplier = "neutral", 0.0

            logger.debug(
                "Unknown label mapped", raw_label=raw_label, mapped_to=normalized_label
            )

        # Calculate score: confidence weighted by sentiment direction
        score = confidence * score_multiplier

        return SentimentResult(
            score=score,
            label=normalized_label,
            confidence=confidence,
        )
