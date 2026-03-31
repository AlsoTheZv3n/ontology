"""Tests for mappers, entity resolver, and derived properties."""

import pytest

from transform.mappers.company import CompanyMapper
from transform.mappers.person import PersonMapper
from transform.mappers.article import ArticleMapper
from transform.mappers.repo import RepoMapper
from transform.mappers.event import EventMapper
from transform.resolver import EntityResolver
from transform.derived import DerivedPropertyEngine, resolve_conflict


# ---------------------------------------------------------------------------
# CompanyMapper
# ---------------------------------------------------------------------------


class TestCompanyMapper:
    def setup_method(self):
        self.mapper = CompanyMapper()

    def test_from_wikipedia(self):
        raw = {
            "displaytitle": "Apple Inc.",
            "extract": "Apple Inc. is an American company.",
            "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Apple_Inc."}},
        }
        obj = self.mapper.from_wikipedia(raw, "apple")

        assert obj.type == "company"
        assert obj.key == "apple"
        assert obj.properties["name"] == "Apple Inc."
        assert obj.properties["description"] == "Apple Inc. is an American company."
        assert "wikipedia" in obj.sources

    def test_from_yahoo_finance(self):
        raw = {
            "symbol": "AAPL",
            "longName": "Apple Inc.",
            "marketCap": 3_000_000_000_000,
            "fullTimeEmployees": 164000,
            "totalRevenue": 394_000_000_000,
            "trailingPE": 28.4,
            "sector": "Technology",
            "city": "Cupertino",
            "country": "United States",
            "companyOfficers": [
                {"name": "Tim Cook", "title": "CEO & Chief Executive Officer"},
            ],
        }
        obj = self.mapper.from_yahoo_finance(raw)

        assert obj.key == "aapl"
        assert obj.properties["ticker"] == "AAPL"
        assert obj.properties["market_cap"] == 3_000_000_000_000
        assert obj.properties["ceo"] == "Tim Cook"
        assert obj.properties["hq"] == "Cupertino, United States"

    def test_from_yahoo_finance_no_ceo(self):
        raw = {"symbol": "AAPL", "companyOfficers": []}
        obj = self.mapper.from_yahoo_finance(raw)
        assert obj.properties["ceo"] is None

    def test_from_github_org(self):
        raw = {"login": "apple", "public_repos": 300, "followers": 5000}
        obj = self.mapper.from_github_org(raw)

        assert obj.key == "apple"
        assert obj.properties["github_repos"] == 300
        assert "github" in obj.sources

    def test_from_forbes(self):
        raw = {"name": "Apple", "rank": 1, "revenue": 394000}
        obj = self.mapper.from_forbes(raw)

        assert obj.key == "apple"
        assert obj.properties["rank"] == 1

    def test_from_sec(self):
        raw = {"cik": "0000320193", "name": "Apple Inc.", "sic": "3571"}
        obj = self.mapper.from_sec(raw)

        assert obj.properties["cik"] == "0000320193"
        assert "sec_edgar" in obj.sources


# ---------------------------------------------------------------------------
# PersonMapper
# ---------------------------------------------------------------------------


class TestPersonMapper:
    def setup_method(self):
        self.mapper = PersonMapper()

    def test_from_sec_officer(self):
        raw = {"name": "Tim Cook", "title": "Chief Executive Officer"}
        obj = self.mapper.from_sec_officer(raw, "apple")

        assert obj.type == "person"
        assert obj.key == "tim-cook-apple"
        assert obj.properties["role"] == "Chief Executive Officer"

    def test_from_github_contributor(self):
        raw = {"login": "torvalds", "contributions": 500}
        obj = self.mapper.from_github_contributor(raw, "linux/linux")

        assert obj.key == "torvalds"
        assert obj.properties["contributions"] == 500


# ---------------------------------------------------------------------------
# ArticleMapper
# ---------------------------------------------------------------------------


class TestArticleMapper:
    def test_from_hn(self):
        raw = {
            "title": "Apple announces M5",
            "url": "https://example.com/m5",
            "published": "2026-03-31",
            "score": 150,
            "comments": 42,
        }
        obj = ArticleMapper().from_hn(raw)

        assert obj.type == "article"
        assert obj.properties["title"] == "Apple announces M5"
        assert obj.properties["source"] == "hackernews"
        assert len(obj.key) == 12  # md5 hash prefix


# ---------------------------------------------------------------------------
# RepoMapper
# ---------------------------------------------------------------------------


class TestRepoMapper:
    def test_from_github(self):
        raw = {
            "full_name": "apple/swift",
            "name": "swift",
            "stargazers_count": 60000,
            "forks_count": 10000,
            "language": "Swift",
            "open_issues_count": 500,
            "html_url": "https://github.com/apple/swift",
        }
        obj = RepoMapper().from_github(raw)

        assert obj.type == "repository"
        assert obj.key == "apple/swift"
        assert obj.properties["stars"] == 60000


# ---------------------------------------------------------------------------
# EventMapper
# ---------------------------------------------------------------------------


class TestEventMapper:
    def setup_method(self):
        self.mapper = EventMapper()

    def test_from_patent(self):
        raw = {
            "patent_title": "Face recognition",
            "patent_date": "2025-01-15",
            "patent_number": "US12345678",
        }
        obj = self.mapper.from_patent(raw, "apple")

        assert obj.type == "event"
        assert obj.key == "patent-US12345678"
        assert obj.properties["event_type"] == "patent"

    def test_from_sec_filing(self):
        raw = {
            "form": "10-K",
            "filingDate": "2025-10-01",
            "accessionNumber": "0000320193-25-000001",
            "primaryDocDescription": "Annual Report",
        }
        obj = self.mapper.from_sec_filing(raw, "apple")

        assert obj.properties["form"] == "10-K"
        assert "filing" in obj.key


# ---------------------------------------------------------------------------
# EntityResolver
# ---------------------------------------------------------------------------


class TestEntityResolver:
    def setup_method(self):
        self.resolver = EntityResolver(threshold=85)

    def test_exact_match(self):
        keys = ["apple", "google", "microsoft"]
        assert self.resolver.find_match("Apple", keys) == "apple"

    def test_fuzzy_match_strips_suffix(self):
        keys = ["apple", "google"]
        assert self.resolver.find_match("Apple Inc.", keys) == "apple"

    def test_no_match_below_threshold(self):
        keys = ["apple", "google"]
        assert self.resolver.find_match("Netflix", keys) is None

    def test_empty_keys_returns_none(self):
        assert self.resolver.find_match("Apple", []) is None

    def test_normalize(self):
        assert self.resolver.normalize("Apple Inc.") == "apple"
        assert self.resolver.normalize("Microsoft Corp") == "microsoft"
        assert self.resolver.normalize("SAP AG") == "sap"
        assert self.resolver.normalize(" Tesla, Inc. ") == "tesla"


# ---------------------------------------------------------------------------
# DerivedPropertyEngine
# ---------------------------------------------------------------------------


class TestDerivedPropertyEngine:
    def setup_method(self):
        self.engine = DerivedPropertyEngine()

    def test_compute_coverage(self):
        sources = {"wikipedia": {}, "github": {}, "yahoo_finance": {}}
        result = self.engine.compute({}, sources)

        assert result["source_coverage"] == pytest.approx(3 / 7)
        assert "sec_edgar" in result["missing_sources"]
        assert "wikipedia" not in result["missing_sources"]

    def test_compute_innovation_score(self):
        props = {"github_stars": 50000, "patent_count": 200, "r_and_d_spend": 2e9}
        result = self.engine.compute(props, {})

        assert 0 <= result["innovation_score"] <= 100
        assert result["innovation_score"] > 0

    def test_innovation_score_zero_inputs(self):
        result = self.engine.compute({}, {})
        assert result["innovation_score"] == 0

    def test_innovation_score_capped_at_100(self):
        props = {"github_stars": 10_000_000, "patent_count": 10000, "r_and_d_spend": 100e9}
        result = self.engine.compute(props, {})
        assert result["innovation_score"] == 100.0


class TestResolveConflict:
    def test_priority_order(self):
        values = {"yahoo_finance": 164000, "wikipedia": 160000}
        assert resolve_conflict("employees", values) == 164000

    def test_falls_back_to_next(self):
        values = {"wikipedia": 160000}
        assert resolve_conflict("employees", values) == 160000

    def test_unknown_field_uses_first_available(self):
        values = {"source_a": "val_a", "source_b": "val_b"}
        assert resolve_conflict("unknown_field", values) == "val_a"

    def test_skips_none_values(self):
        values = {"sec_edgar": None, "yahoo_finance": 5000}
        assert resolve_conflict("employees", values) == 5000
