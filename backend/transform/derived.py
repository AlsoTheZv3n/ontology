"""Compute derived properties that don't exist in any single source."""

from __future__ import annotations

EXPECTED_SOURCES = [
    "wikipedia", "alpha_vantage", "github", "sec_edgar", "sec_xbrl",
    "wikidata", "huggingface", "hn_rss", "forbes",
]

FIELD_PRIORITY: dict[str, list[str]] = {
    "employees": ["sec_edgar", "alpha_vantage", "wikidata", "forbes"],
    "revenue": ["sec_xbrl", "alpha_vantage", "forbes"],
    "market_cap": ["alpha_vantage"],
    "description": ["wikipedia"],
    "name": ["alpha_vantage", "sec_edgar", "wikipedia", "wikidata", "forbes"],
}


class DerivedPropertyEngine:
    def compute(self, properties: dict, sources: dict) -> dict:
        """Compute derived properties from existing properties and sources."""
        derived: dict = {}

        # Source coverage
        present = [s for s in EXPECTED_SOURCES if s in sources]
        derived["missing_sources"] = [s for s in EXPECTED_SOURCES if s not in sources]
        derived["source_coverage"] = (
            round(len(present) / len(EXPECTED_SOURCES), 2) if EXPECTED_SOURCES else 0
        )

        # Innovation score (0–100)
        derived["innovation_score"] = compute_innovation_score(properties)

        return derived


def compute_innovation_score(props: dict) -> float:
    """
    Score 0-100 based on:
    - GitHub repos & followers (developer activity)
    - HuggingFace models & downloads (AI activity)
    - R&D expense relative to revenue (investment intensity)
    - Source completeness (data richness)
    """
    score = 0.0

    # GitHub (max 30 points)
    repos = min(props.get("github_repos", 0) or 0, 5000)
    followers = min(props.get("github_followers", 0) or 0, 200000)
    score += (repos / 5000) * 15
    score += (followers / 200000) * 15

    # HuggingFace (max 25 points)
    hf_models = min(props.get("hf_model_count", 0) or 0, 100)
    hf_downloads = min(props.get("hf_total_downloads", 0) or 0, 1e9)
    score += (hf_models / 100) * 15
    score += (hf_downloads / 1e9) * 10

    # R&D / Revenue ratio (max 30 points)
    rd = props.get("rd_expense", 0) or 0
    revenue = props.get("revenue", 0) or 0
    if revenue > 0 and rd > 0:
        rd_ratio = min(rd / revenue, 0.5)
        score += (rd_ratio / 0.5) * 30

    # Data richness (max 15 points)
    data_fields = [
        props.get("ceo"), props.get("revenue"), props.get("market_cap"),
        props.get("github_repos"), props.get("hf_model_count"),
        props.get("founder"), props.get("founded"),
    ]
    filled = len([v for v in data_fields if v])
    score += (filled / 7) * 15

    return round(min(score, 100), 1)


def resolve_conflict(field: str, values: dict[str, object]) -> object:
    """Pick the authoritative value for a field based on source priority."""
    priority = FIELD_PRIORITY.get(field, list(values.keys()))
    for source in priority:
        if source in values and values[source] is not None:
            return values[source]
    return None
