"""
spaCy Named Entity Recognition with lazy loading.
Gracefully returns empty results if spacy is not installed.
"""

import logging
from collections import Counter
from functools import lru_cache

logger = logging.getLogger(__name__)

_HAS_SPACY = True
try:
    import spacy as _spacy
except ImportError:
    _HAS_SPACY = False
    logger.warning("spacy not installed — NER extraction unavailable")

_MAX_INPUT_CHARS = 10_000

# Map spaCy entity labels to our output keys
_LABEL_MAP = {
    "PERSON": "persons",
    "ORG": "organizations",
    "GPE": "locations",
    "LOC": "locations",
    "PRODUCT": "products",
    "MONEY": "money",
}

_EMPTY_RESULT = {
    "persons": [],
    "organizations": [],
    "locations": [],
    "products": [],
    "money": [],
}


@lru_cache(maxsize=1)
def _load_nlp():
    """Lazy-load the spaCy English model (cached after first call)."""
    if not _HAS_SPACY:
        return None
    try:
        nlp = _spacy.load("en_core_web_sm")
        logger.info("spaCy en_core_web_sm model loaded successfully")
        return nlp
    except OSError as exc:
        logger.error("spaCy model not found (run: python -m spacy download en_core_web_sm): %s", exc)
        return None
    except Exception as exc:
        logger.error("Failed to load spaCy model: %s", exc)
        return None


def extract_entities(text: str) -> dict[str, list[str]]:
    """
    Extract named entities from text.

    Returns {"persons": [...], "organizations": [...], "locations": [...],
             "products": [...], "money": [...]}.
    Each category contains up to 10 deduplicated entities ordered by frequency.
    """
    if not text:
        return dict(_EMPTY_RESULT)

    nlp = _load_nlp()
    if nlp is None:
        return dict(_EMPTY_RESULT)

    try:
        # Truncate to avoid excessive processing
        truncated = text[:_MAX_INPUT_CHARS]
        doc = nlp(truncated)

        # Collect entities by category
        buckets: dict[str, list[str]] = {k: [] for k in _EMPTY_RESULT}
        for ent in doc.ents:
            key = _LABEL_MAP.get(ent.label_)
            if key:
                buckets[key].append(ent.text.strip())

        # Deduplicate using Counter, keep top 10 by frequency
        result = {}
        for key, values in buckets.items():
            if values:
                counter = Counter(values)
                result[key] = [name for name, _count in counter.most_common(10)]
            else:
                result[key] = []

        return result

    except Exception as exc:
        logger.error("NER extraction failed: %s", exc)
        return dict(_EMPTY_RESULT)
