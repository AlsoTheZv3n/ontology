"""Tests for expanded connectors — World Bank, Commodities, Countries, GDELT, Semantic Scholar."""

import json

import pytest
from pytest_httpx import HTTPXMock

from connectors.world_bank import WorldBankConnector, INDICATORS
from connectors.commodities import CommoditiesConnector
from connectors.countries import CountriesConnector
from connectors.gdelt import GDELTConnector
from connectors.semantic_scholar import SemanticScholarConnector


# ---------------------------------------------------------------------------
# WorldBankConnector
# ---------------------------------------------------------------------------


class TestWorldBankConnector:
    async def test_fetch_indicator_cache_miss(self, fake_redis, httpx_mock: HTTPXMock):
        payload = [
            {"page": 1, "pages": 1, "per_page": 5, "total": 5},
            [{"indicator": {"id": "NY.GDP.MKTP.CD"}, "country": {"id": "US"}, "value": 25000000000000}],
        ]
        httpx_mock.add_response(json=payload)
        conn = WorldBankConnector(fake_redis)

        result = await conn.fetch_indicator("US", "NY.GDP.MKTP.CD", years=5)

        assert result == payload

    async def test_fetch_indicator_parses_list(self, fake_redis, httpx_mock: HTTPXMock):
        payload = [
            {"page": 1},
            [{"value": 3.2}, {"value": 2.8}],
        ]
        httpx_mock.add_response(json=payload)
        conn = WorldBankConnector(fake_redis)

        result = await conn.fetch_indicator("DE", "FP.CPI.TOTL.ZG", years=2)

        assert isinstance(result, list)
        assert len(result) == 2

    async def test_fetch_indicator_empty_response(self, fake_redis, httpx_mock: HTTPXMock):
        payload = [{"page": 1, "pages": 0, "total": 0}, None]
        httpx_mock.add_response(json=payload)
        conn = WorldBankConnector(fake_redis)

        result = await conn.fetch_indicator("ZZ", "NY.GDP.MKTP.CD")

        assert result[1] is None

    async def test_fetch_indicator_http_error(self, fake_redis, httpx_mock: HTTPXMock):
        httpx_mock.add_response(status_code=500)
        conn = WorldBankConnector(fake_redis)

        with pytest.raises(Exception):
            await conn.fetch_indicator("US", "NY.GDP.MKTP.CD")

    async def test_fetch_all_macro(self, fake_redis, httpx_mock: HTTPXMock):
        """Each country/indicator combo triggers one HTTP call."""
        sample = [{"page": 1}, [{"value": 42}]]
        # 10 countries x 3 indicators = 30 requests
        for _ in range(30):
            httpx_mock.add_response(json=sample)

        conn = WorldBankConnector(fake_redis)
        result = await conn.fetch_all_macro()

        assert "US" in result
        assert "gdp_usd" in result["US"]


# ---------------------------------------------------------------------------
# CommoditiesConnector
# ---------------------------------------------------------------------------


class TestCommoditiesConnector:
    async def test_fetch_spot_prices_cache_miss(self, fake_redis, httpx_mock: HTTPXMock):
        httpx_mock.add_response(json={"price": 2350.50})
        httpx_mock.add_response(json={"price": 29.12})
        httpx_mock.add_response(json={"price": 4.35})

        conn = CommoditiesConnector(fake_redis)
        result = await conn.fetch_spot_prices()

        assert result["gold"] == 2350.50
        assert result["silver"] == 29.12
        assert result["copper"] == 4.35

    async def test_fetch_spot_prices_partial_failure(self, fake_redis, httpx_mock: HTTPXMock):
        httpx_mock.add_response(json={"price": 2350.50})
        httpx_mock.add_response(status_code=503)
        httpx_mock.add_response(json={"price": 4.35})

        conn = CommoditiesConnector(fake_redis)
        result = await conn.fetch_spot_prices()

        # One of the three should be None due to the 503
        assert None in result.values()

    async def test_cache_ttl_is_300(self, fake_redis):
        conn = CommoditiesConnector(fake_redis)
        assert conn.cache_ttl == 300

    async def test_fetch_spot_prices_empty_response(self, fake_redis, httpx_mock: HTTPXMock):
        httpx_mock.add_response(json={})
        httpx_mock.add_response(json={})
        httpx_mock.add_response(json={})

        conn = CommoditiesConnector(fake_redis)
        result = await conn.fetch_spot_prices()

        # No "price" key → all None
        assert all(v is None for v in result.values())


# ---------------------------------------------------------------------------
# CountriesConnector
# ---------------------------------------------------------------------------


class TestCountriesConnector:
    async def test_fetch_all_cache_miss(self, fake_redis, httpx_mock: HTTPXMock):
        payload = [
            {"name": {"common": "Germany"}, "cca2": "DE", "population": 83000000},
            {"name": {"common": "France"}, "cca2": "FR", "population": 67000000},
        ]
        httpx_mock.add_response(json=payload)
        conn = CountriesConnector(fake_redis)

        result = await conn.fetch_all()

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["cca2"] == "DE"

    async def test_fetch_country(self, fake_redis, httpx_mock: HTTPXMock):
        payload = [{"name": {"common": "Japan"}, "cca2": "JP", "population": 125000000}]
        httpx_mock.add_response(json=payload)
        conn = CountriesConnector(fake_redis)

        result = await conn.fetch_country("JP")

        assert result[0]["name"]["common"] == "Japan"

    async def test_cache_ttl_is_one_week(self, fake_redis):
        conn = CountriesConnector(fake_redis)
        assert conn.cache_ttl == 604800

    async def test_fetch_country_not_found(self, fake_redis, httpx_mock: HTTPXMock):
        httpx_mock.add_response(status_code=404)
        conn = CountriesConnector(fake_redis)

        with pytest.raises(Exception):
            await conn.fetch_country("ZZZ")

    async def test_fetch_all_empty(self, fake_redis, httpx_mock: HTTPXMock):
        httpx_mock.add_response(json=[])
        conn = CountriesConnector(fake_redis)

        result = await conn.fetch_all()

        assert result == []


# ---------------------------------------------------------------------------
# GDELTConnector
# ---------------------------------------------------------------------------


class TestGDELTConnector:
    async def test_search_mentions_cache_miss(self, fake_redis, httpx_mock: HTTPXMock):
        payload = {
            "articles": [
                {"url": "https://example.com/1", "title": "Trade tensions rise"},
                {"url": "https://example.com/2", "title": "New tariffs announced"},
            ]
        }
        httpx_mock.add_response(json=payload)
        conn = GDELTConnector(fake_redis)

        result = await conn.search_mentions("trade war")

        assert "articles" in result
        assert len(result["articles"]) == 2

    async def test_search_mentions_empty(self, fake_redis, httpx_mock: HTTPXMock):
        httpx_mock.add_response(json={"articles": []})
        conn = GDELTConnector(fake_redis)

        result = await conn.search_mentions("xyznonexistent")

        assert result["articles"] == []

    async def test_cache_ttl_is_900(self, fake_redis):
        conn = GDELTConnector(fake_redis)
        assert conn.cache_ttl == 900

    async def test_search_mentions_http_error(self, fake_redis, httpx_mock: HTTPXMock):
        httpx_mock.add_response(status_code=500)
        conn = GDELTConnector(fake_redis)

        with pytest.raises(Exception):
            await conn.search_mentions("test")


# ---------------------------------------------------------------------------
# SemanticScholarConnector
# ---------------------------------------------------------------------------


class TestSemanticScholarConnector:
    async def test_search_papers_cache_miss(self, fake_redis, httpx_mock: HTTPXMock):
        payload = {
            "total": 1200,
            "data": [
                {
                    "paperId": "abc123",
                    "title": "Attention Is All You Need",
                    "year": 2017,
                    "citationCount": 90000,
                    "authors": [{"name": "Ashish Vaswani"}],
                    "abstract": "The dominant sequence transduction models...",
                },
            ],
        }
        httpx_mock.add_response(json=payload)
        conn = SemanticScholarConnector(fake_redis)

        result = await conn.search_papers("transformer attention")

        assert result["total"] == 1200
        assert result["data"][0]["title"] == "Attention Is All You Need"

    async def test_search_papers_empty(self, fake_redis, httpx_mock: HTTPXMock):
        httpx_mock.add_response(json={"total": 0, "data": []})
        conn = SemanticScholarConnector(fake_redis)

        result = await conn.search_papers("xyznonexistentquery")

        assert result["total"] == 0
        assert result["data"] == []

    async def test_fetch_author(self, fake_redis, httpx_mock: HTTPXMock):
        payload = {
            "authorId": "12345",
            "name": "Geoffrey Hinton",
            "affiliations": ["University of Toronto"],
            "paperCount": 400,
            "citationCount": 500000,
            "hIndex": 170,
        }
        httpx_mock.add_response(json=payload)
        conn = SemanticScholarConnector(fake_redis)

        result = await conn.fetch_author("12345")

        assert result["name"] == "Geoffrey Hinton"
        assert result["hIndex"] == 170

    async def test_fetch_author_not_found(self, fake_redis, httpx_mock: HTTPXMock):
        httpx_mock.add_response(status_code=404)
        conn = SemanticScholarConnector(fake_redis)

        with pytest.raises(Exception):
            await conn.fetch_author("0000000")

    async def test_search_papers_http_error(self, fake_redis, httpx_mock: HTTPXMock):
        httpx_mock.add_response(status_code=429)
        conn = SemanticScholarConnector(fake_redis)

        with pytest.raises(Exception):
            await conn.search_papers("test")
