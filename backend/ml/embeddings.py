"""
Sentence Transformer embeddings with lazy loading.
Gracefully returns empty results if sentence_transformers is not installed.
"""

import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

_HAS_SENTENCE_TRANSFORMERS = True
try:
    from sentence_transformers import SentenceTransformer as _SentenceTransformer
except ImportError:
    _HAS_SENTENCE_TRANSFORMERS = False
    logger.warning("sentence_transformers not installed — embeddings unavailable")


@lru_cache(maxsize=1)
def _load_model():
    """Lazy-load the Sentence Transformer model (cached after first call)."""
    if not _HAS_SENTENCE_TRANSFORMERS:
        return None
    try:
        model = _SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("SentenceTransformer all-MiniLM-L6-v2 loaded successfully")
        return model
    except Exception as exc:
        logger.error("Failed to load SentenceTransformer model: %s", exc)
        return None


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Encode a list of texts into 384-dimensional embedding vectors.

    Returns a list of plain Python float lists (not numpy arrays).
    Returns an empty list if the model is unavailable.
    """
    if not texts:
        return []

    model = _load_model()
    if model is None:
        return []

    try:
        embeddings = model.encode(texts, show_progress_bar=False)
        return [vec.tolist() for vec in embeddings]
    except Exception as exc:
        logger.error("Embedding inference failed: %s", exc)
        return []


def embed_object(obj_type: str, properties: dict) -> str:
    """
    Build a text representation of a domain object for embedding.

    Supported obj_type values:
      - "company"  → name + description + sector
      - "article"  → title
      - "person"   → name + role

    Returns a concatenated string suitable for passing to embed_texts().
    """
    obj_type_lower = obj_type.lower() if obj_type else ""

    if obj_type_lower == "company":
        parts = [
            properties.get("name", ""),
            properties.get("description", ""),
            properties.get("sector", ""),
        ]
    elif obj_type_lower == "article":
        parts = [
            properties.get("title", ""),
        ]
    elif obj_type_lower == "person":
        parts = [
            properties.get("name", ""),
            properties.get("role", ""),
        ]
    else:
        # Generic fallback: concatenate all string values
        parts = [str(v) for v in properties.values() if v]

    return " ".join(p for p in parts if p).strip()
