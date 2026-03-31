"""Tests for all connectors — uses httpx mocking and fake Redis."""

import json

import pytest
from pytest_httpx import HTTPXMock

from connectors.base import BaseConnector
from connectors.wikipedia import WikipediaConnector
from connectors.github import GitHubConnector
from connectors.sec_edgar import SECEdgarConnector
from connectors.hn_rss import HackerNewsConnector
from connectors.patents import PatentsViewConnector


# ---------------------------------------------------------------------------
# BaseConnector
# ---------------------------------------------------------------------------


class DummyConnector(BaseConnector):
    source_name = "dummy"


class TestBaseConnector:
    async def test_fetch_with_cache_miss(self, fake_redis, httpx_mock: HTTPXMock):
        httpx_mock.add_response(json={"hello": "world"})
        conn = DummyConnector(fake_redis)

        result = await conn._fetch_with_cache("https://example.com/api")

        assert result == {"hello": "world"}

    async def test_fetch_with_cache_hit(self, fake_redis, httpx_mock: HTTPXMock):
        conn = DummyConnector(fake_redis)
        url = "https://example.com/api"

        # Pre-populate cache
        cache_key = conn._cache_key(url + json.dumps({}, sort_keys=True))
        await fake_redis.setex(cache_key, 3600, json.dumps({"cached": True}))

        # Should NOT make an HTTP call — httpx_mock has no response registered
        result = await conn._fetch_with_cache(url)
        assert result == {"cached": True}

    async def test_fetch_raises_on_http_error(self, fake_redis, httpx_mock: HTTPXMock):
        httpx_mock.add_response(status_code=404)
        conn = DummyConnector(fake_redis)

        with pytest.raises(Exception):
            await conn._fetch_with_cache("https://example.com/missing")


# ---------------------------------------------------------------------------
# WikipediaConnector
# ---------------------------------------------------------------------------


class TestWikipediaConnector:
    async def test_fetch_company(self, fake_redis, httpx_mock: HTTPXMock):
        payload = {
            "displaytitle": "Apple Inc.",
            "extract": "Apple Inc. is an American company.",
            "titles": {"normalized": "Apple Inc."},
        }
        httpx_mock.add_response(json=payload)
        conn = WikipediaConnector(fake_redis)

        result = await conn.fetch_company("Apple_Inc.")

        assert result["displaytitle"] == "Apple Inc."
        assert "extract" in result


# ---------------------------------------------------------------------------
# GitHubConnector
# ---------------------------------------------------------------------------


class TestGitHubConnector:
    async def test_fetch_org(self, fake_redis, httpx_mock: HTTPXMock):
        payload = {"login": "apple", "public_repos": 300, "followers": 5000}
        httpx_mock.add_response(json=payload)
        conn = GitHubConnector(fake_redis, token="test-token")

        result = await conn.fetch_org("apple")

        assert result["login"] == "apple"
        assert result["public_repos"] == 300

    async def test_fetch_repos(self, fake_redis, httpx_mock: HTTPXMock):
        payload = [
            {"name": "swift", "stargazers_count": 60000},
            {"name": "ml-stable-diffusion", "stargazers_count": 15000},
        ]
        httpx_mock.add_response(json=payload)
        conn = GitHubConnector(fake_redis)

        result = await conn.fetch_repos("apple")

        assert len(result) == 2
        assert result[0]["name"] == "swift"

    async def test_auth_header_set_when_token_provided(self, fake_redis):
        conn = GitHubConnector(fake_redis, token="my-token")
        assert conn.headers["Authorization"] == "Bearer my-token"

    async def test_no_auth_header_without_token(self, fake_redis):
        conn = GitHubConnector(fake_redis)
        assert "Authorization" not in conn.headers


# ---------------------------------------------------------------------------
# SECEdgarConnector
# ---------------------------------------------------------------------------


class TestSECEdgarConnector:
    async def test_fetch_submissions(self, fake_redis, httpx_mock: HTTPXMock):
        payload = {"cik": "0000320193", "name": "Apple Inc.", "filings": {"recent": {}}}
        httpx_mock.add_response(json=payload)
        conn = SECEdgarConnector(fake_redis, user_agent="Test test@test.com")

        result = await conn.fetch_submissions("0000320193")

        assert result["name"] == "Apple Inc."

    async def test_fetch_company_facts(self, fake_redis, httpx_mock: HTTPXMock):
        payload = {"cik": 320193, "entityName": "APPLE INC", "facts": {}}
        httpx_mock.add_response(json=payload)
        conn = SECEdgarConnector(fake_redis)

        result = await conn.fetch_company_facts("0000320193")

        assert result["entityName"] == "APPLE INC"


# ---------------------------------------------------------------------------
# HackerNewsConnector
# ---------------------------------------------------------------------------


class TestHackerNewsConnector:
    async def test_fetch_mentions(self, fake_redis, httpx_mock: HTTPXMock):
        rss_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
        <channel>
            <item>
                <title>Apple releases new M5 chip</title>
                <link>https://example.com/article1</link>
                <pubDate>Mon, 31 Mar 2026 10:00:00 GMT</pubDate>
            </item>
            <item>
                <title>Apple AI features in iOS 20</title>
                <link>https://example.com/article2</link>
                <pubDate>Sun, 30 Mar 2026 08:00:00 GMT</pubDate>
            </item>
        </channel>
        </rss>"""
        httpx_mock.add_response(text=rss_xml, headers={"content-type": "application/xml"})
        conn = HackerNewsConnector(fake_redis)

        result = await conn.fetch_mentions("Apple")

        assert len(result) == 2
        assert result[0]["title"] == "Apple releases new M5 chip"
        assert "url" in result[0]


# ---------------------------------------------------------------------------
# PatentsViewConnector
# ---------------------------------------------------------------------------


class TestPatentsViewConnector:
    async def test_fetch_by_company(self, fake_redis, httpx_mock: HTTPXMock):
        payload = {
            "patents": [
                {
                    "patent_title": "Face recognition system",
                    "patent_date": "2025-01-15",
                    "patent_number": "US12345678",
                }
            ],
            "count": 1,
            "total_patent_count": 4821,
        }
        httpx_mock.add_response(json=payload)
        conn = PatentsViewConnector(fake_redis)

        result = await conn.fetch_by_company("Apple Inc.")

        assert result["total_patent_count"] == 4821
        assert len(result["patents"]) == 1
