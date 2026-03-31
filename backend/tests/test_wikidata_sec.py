"""Tests for Wikidata SPARQL and SEC XBRL connectors."""

import pytest
from pytest_httpx import HTTPXMock

from connectors.wikidata import WikidataConnector
from connectors.sec_edgar import SECEdgarConnector

MOCK_SPARQL = {
    "results": {
        "bindings": [
            {
                "companyKey": {"value": "apple"},
                "ceoLabel": {"value": "Tim Cook"},
                "founderLabel": {"value": "Steve Jobs"},
                "founded": {"value": "1976-04-01T00:00:00Z"},
                "hqLabel": {"value": "Cupertino"},
                "employees": {"value": "164000"},
            },
            {
                "companyKey": {"value": "apple"},
                "founderLabel": {"value": "Steve Wozniak"},
            },
            {
                "companyKey": {"value": "microsoft"},
                "ceoLabel": {"value": "Satya Nadella"},
                "founded": {"value": "1975-04-04T00:00:00Z"},
                "hqLabel": {"value": "Redmond"},
            },
        ]
    }
}

MOCK_XBRL = {
    "facts": {
        "us-gaap": {
            "Revenues": {
                "units": {
                    "USD": [
                        {"form": "10-K", "end": "2024-09-30", "val": 394328000000},
                        {"form": "10-Q", "end": "2024-06-30", "val": 84000000000},
                        {"form": "10-K", "end": "2023-09-30", "val": 383000000000},
                    ]
                }
            },
            "NetIncomeLoss": {
                "units": {"USD": [{"form": "10-K", "end": "2024-09-30", "val": 93736000000}]}
            },
            "Assets": {
                "units": {"USD": [{"form": "10-K", "end": "2024-09-30", "val": 352583000000}]}
            },
            "ResearchAndDevelopmentExpense": {
                "units": {"USD": [{"form": "10-K", "end": "2024-09-30", "val": 29915000000}]}
            },
        }
    }
}


class TestWikidataConnector:
    async def test_fetch_all_companies(self, fake_redis, httpx_mock: HTTPXMock):
        httpx_mock.add_response(json=MOCK_SPARQL)
        conn = WikidataConnector(fake_redis)

        result = await conn.fetch_all_companies()

        assert "apple" in result
        assert result["apple"]["ceo"] == "Tim Cook"
        assert result["apple"]["founded"] == 1976
        assert result["apple"]["hq"] == "Cupertino"
        assert result["apple"]["employees"] == 164000

    async def test_multiple_founders(self, fake_redis, httpx_mock: HTTPXMock):
        httpx_mock.add_response(json=MOCK_SPARQL)
        conn = WikidataConnector(fake_redis)

        result = await conn.fetch_all_companies()

        assert "Steve Jobs" in result["apple"]["founders"]
        assert "Steve Wozniak" in result["apple"]["founders"]

    async def test_multiple_companies(self, fake_redis, httpx_mock: HTTPXMock):
        httpx_mock.add_response(json=MOCK_SPARQL)
        conn = WikidataConnector(fake_redis)

        result = await conn.fetch_all_companies()

        assert "microsoft" in result
        assert result["microsoft"]["ceo"] == "Satya Nadella"
        assert result["microsoft"]["founded"] == 1975

    async def test_caches_results(self, fake_redis, httpx_mock: HTTPXMock):
        httpx_mock.add_response(json=MOCK_SPARQL)
        conn = WikidataConnector(fake_redis)

        await conn.fetch_all_companies()
        await conn.fetch_all_companies()

        assert len(httpx_mock.get_requests()) == 1

    async def test_empty_response(self, fake_redis, httpx_mock: HTTPXMock):
        httpx_mock.add_response(json={"results": {"bindings": []}})
        conn = WikidataConnector(fake_redis)

        result = await conn.fetch_all_companies()
        assert result == {}


class TestSECXBRL:
    async def test_fetch_financials(self, fake_redis, httpx_mock: HTTPXMock):
        httpx_mock.add_response(json=MOCK_XBRL)
        conn = SECEdgarConnector(fake_redis)

        result = await conn.fetch_financials("0000320193")

        assert result["revenue"] == 394328000000
        assert result["net_income"] == 93736000000
        assert result["total_assets"] == 352583000000
        assert result["rd_expense"] == 29915000000

    async def test_only_annual_10k(self, fake_redis, httpx_mock: HTTPXMock):
        httpx_mock.add_response(json=MOCK_XBRL)
        conn = SECEdgarConnector(fake_redis)

        result = await conn.fetch_financials("0000320193")

        # Should be latest 10-K (2024), not 10-Q
        assert result["revenue"] == 394328000000

    async def test_latest_year_selected(self, fake_redis, httpx_mock: HTTPXMock):
        httpx_mock.add_response(json=MOCK_XBRL)
        conn = SECEdgarConnector(fake_redis)

        result = await conn.fetch_financials("0000320193")

        # 2024 value, not 2023
        assert result["revenue"] == 394328000000

    async def test_missing_concepts(self, fake_redis, httpx_mock: HTTPXMock):
        httpx_mock.add_response(json={"facts": {"us-gaap": {}}})
        conn = SECEdgarConnector(fake_redis)

        result = await conn.fetch_financials("0000320193")
        assert result == {}
