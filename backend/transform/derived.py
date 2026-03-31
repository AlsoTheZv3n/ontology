"""Compute derived properties that don't exist in any single source."""

from __future__ import annotations

EXPECTED_SOURCES = ["wikipedia", "yahoo_finance", "github", "sec_edgar", "patents", "hn_rss", "forbes"]

FIELD_PRIORITY: dict[str, list[str]] = {
    "employees": ["sec_edgar", "yahoo_finance", "wikipedia", "forbes"],
    "revenue": ["sec_edgar", "yahoo_finance", "forbes"],
    "market_cap": ["yahoo_finance"],
    "description": ["wikipedia"],
    "github_stars": ["github"],
    "name": ["yahoo_finance", "sec_edgar", "wikipedia", "forbes"],
}


class DerivedPropertyEngine:
    def compute(self, properties: dict, sources: dict) -> dict:
        """Compute derived properties from existing properties and sources."""
        derived: dict = {}

        # Source coverage
        present = [s for s in EXPECTED_SOURCES if s in sources]
        derived["missing_sources"] = [s for s in EXPECTED_SOURCES if s not in sources]
        derived["source_coverage"] = (
            len(present) / len(EXPECTED_SOURCES) if EXPECTED_SOURCES else 0
        )

        # Innovation score (0–100)
        github_stars = properties.get("github_stars") or 0
        patent_count = properties.get("patent_count") or 0
        r_and_d = properties.get("r_and_d_spend") or 0
        derived["innovation_score"] = min(
            100.0,
            (github_stars / 10_000) * 30
            + (patent_count / 100) * 40
            + (r_and_d / 1e9) * 30,
        )

        return derived


def resolve_conflict(field: str, values: dict[str, object]) -> object:
    """Pick the authoritative value for a field based on source priority."""
    priority = FIELD_PRIORITY.get(field, list(values.keys()))
    for source in priority:
        if source in values and values[source] is not None:
            return values[source]
    return None
