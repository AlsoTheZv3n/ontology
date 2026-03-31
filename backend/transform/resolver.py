"""Entity Resolution via fuzzy string matching."""

from __future__ import annotations

from rapidfuzz import fuzz, process


class EntityResolver:
    STRIP_SUFFIXES = [
        " inc", " corp", " corporation", " ltd", " llc",
        " gmbh", " ag", " sa", " plc", " co", " company",
        ".", ",",
    ]

    def __init__(self, threshold: int = 85):
        self.threshold = threshold

    def normalize(self, name: str) -> str:
        result = name.lower().strip()
        prev = None
        while result != prev:
            prev = result
            for suffix in self.STRIP_SUFFIXES:
                result = result.removesuffix(suffix)
            result = result.strip()
        return result

    def find_match(self, candidate: str, existing_keys: list[str]) -> str | None:
        """Return the best matching key if score > threshold, else None."""
        if not existing_keys:
            return None

        norm = self.normalize(candidate)
        normed_map = {self.normalize(k): k for k in existing_keys}

        # Exact match shortcut
        if norm in normed_map:
            return normed_map[norm]

        match = process.extractOne(
            norm,
            list(normed_map.keys()),
            scorer=fuzz.ratio,
            score_cutoff=self.threshold,
        )

        if match:
            return normed_map[match[0]]
        return None
