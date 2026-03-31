"""
FinBERT sentiment analysis with lazy loading.
Gracefully returns neutral defaults if transformers is not installed.
"""

import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

_HAS_TRANSFORMERS = True
try:
    from transformers import pipeline as _pipeline
except ImportError:
    _HAS_TRANSFORMERS = False
    logger.warning("transformers not installed — FinBERT sentiment analysis unavailable")


@lru_cache(maxsize=1)
def _load_model():
    """Lazy-load the FinBERT pipeline (cached after first call)."""
    if not _HAS_TRANSFORMERS:
        return None
    try:
        model = _pipeline(
            "text-classification",
            model="ProsusAI/finbert",
            device=-1,
            truncation=True,
            max_length=512,
        )
        logger.info("FinBERT model loaded successfully")
        return model
    except Exception as exc:
        logger.error("Failed to load FinBERT model: %s", exc)
        return None


# Map FinBERT labels to numeric multipliers for sentiment_score
_LABEL_MULTIPLIER = {
    "positive": 1.0,
    "negative": -1.0,
    "neutral": 0.0,
}


def analyze_sentiment(texts: list[str]) -> list[dict]:
    """
    Batch sentiment classification.

    Returns a list of {"label": "positive"|"negative"|"neutral", "score": float}
    for each input text. Falls back to neutral if model unavailable.
    """
    neutral = {"label": "neutral", "score": 0.5}

    if not texts:
        return []

    pipe = _load_model()
    if pipe is None:
        return [neutral for _ in texts]

    try:
        results = pipe(texts)
        return [{"label": r["label"], "score": round(r["score"], 4)} for r in results]
    except Exception as exc:
        logger.error("FinBERT inference failed: %s", exc)
        return [neutral for _ in texts]


def sentiment_score(text: str) -> float:
    """
    Single text → sentiment score in range -1.0 (bearish) to +1.0 (bullish).

    The raw FinBERT confidence is scaled by the label direction.
    Returns 0.0 if model is unavailable.
    """
    if not text:
        return 0.0

    result = analyze_sentiment([text])
    if not result:
        return 0.0

    item = result[0]
    label = item["label"].lower()
    multiplier = _LABEL_MULTIPLIER.get(label, 0.0)
    return round(multiplier * item["score"], 4)
