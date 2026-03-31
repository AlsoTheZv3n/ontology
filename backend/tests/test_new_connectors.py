"""Tests for the new connectors — uses httpx mocking and fake Redis."""

import json

import pytest
from pytest_httpx import HTTPXMock

from connectors.huggingface import HuggingFaceConnector
from connectors.hn_algolia import HNAlgoliaConnector
from connectors.papers_with_code import PapersWithCodeConnector
from connectors.arxiv import ArxivConnector
from connectors.npm_registry import NpmRegistryConnector
from connectors.pypi import PyPIConnector
from connectors.fred import FREDConnector
from connectors.eia import EIAConnector


# ---------------------------------------------------------------------------
# HuggingFaceConnector
# ---------------------------------------------------------------------------


class TestHuggingFaceConnector:
    async def test_fetch_models(self, fake_redis, httpx_mock: HTTPXMock):
        payload = [
            {"modelId": "meta-llama/Llama-2-7b", "downloads": 5000000},
            {"modelId": "meta-llama/Llama-2-13b", "downloads": 2000000},
        ]
        httpx_mock.add_response(json=payload)
        conn = HuggingFaceConnector(fake_redis)

        result = await conn.fetch_models("meta-llama")

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["modelId"] == "meta-llama/Llama-2-7b"
        assert result[0]["downloads"] == 5000000

    async def test_fetch_org(self, fake_redis, httpx_mock: HTTPXMock):
        payload = {"name": "Meta Llama", "fullname": "meta-llama"}
        httpx_mock.add_response(json=payload)
        conn = HuggingFaceConnector(fake_redis)

        result = await conn.fetch_org("meta-llama")

        assert result["name"] == "Meta Llama"


# ---------------------------------------------------------------------------
# HNAlgoliaConnector
# ---------------------------------------------------------------------------


class TestHNAlgoliaConnector:
    async def test_fetch_search(self, fake_redis, httpx_mock: HTTPXMock):
        payload = {
            "hits": [
                {
                    "title": "Show HN: My new project",
                    "url": "https://example.com",
                    "points": 150,
                    "num_comments": 42,
                    "created_at": "2026-03-30T12:00:00.000Z",
                },
                {
                    "title": "Rust vs Go in 2026",
                    "url": "https://example.com/rust-go",
                    "points": 300,
                    "num_comments": 200,
                    "created_at": "2026-03-29T08:00:00.000Z",
                },
            ],
            "nbHits": 1000,
        }
        httpx_mock.add_response(json=payload)
        conn = HNAlgoliaConnector(fake_redis)

        result = await conn.fetch_search("Rust")

        assert "hits" in result
        assert len(result["hits"]) == 2
        hit = result["hits"][0]
        assert "title" in hit
        assert "url" in hit
        assert "points" in hit
        assert "num_comments" in hit
        assert "created_at" in hit


# ---------------------------------------------------------------------------
# PapersWithCodeConnector
# ---------------------------------------------------------------------------


class TestPapersWithCodeConnector:
    async def test_fetch_papers(self, fake_redis, httpx_mock: HTTPXMock):
        payload = {
            "count": 100,
            "results": [
                {"id": "attention-is-all-you-need", "title": "Attention Is All You Need"},
                {"id": "bert", "title": "BERT: Pre-training of Deep Bidirectional Transformers"},
            ],
        }
        httpx_mock.add_response(json=payload)
        conn = PapersWithCodeConnector(fake_redis)

        result = await conn.fetch_papers("transformers")

        assert result["count"] == 100
        assert len(result["results"]) == 2
        assert result["results"][0]["title"] == "Attention Is All You Need"


# ---------------------------------------------------------------------------
# ArxivConnector
# ---------------------------------------------------------------------------

ARXIV_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/1706.03762v7</id>
    <title>Attention Is All You Need</title>
    <summary>The dominant sequence transduction models are based on complex recurrent or convolutional neural networks.</summary>
    <published>2017-06-12T17:57:34Z</published>
    <author><name>Ashish Vaswani</name></author>
    <author><name>Noam Shazeer</name></author>
    <link href="http://arxiv.org/abs/1706.03762v7" rel="alternate" type="text/html"/>
    <link title="pdf" href="http://arxiv.org/pdf/1706.03762v7" rel="related" type="application/pdf"/>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/1810.04805v2</id>
    <title>BERT: Pre-training of Deep Bidirectional Transformers</title>
    <summary>We introduce a new language representation model called BERT.</summary>
    <published>2018-10-11T00:00:00Z</published>
    <author><name>Jacob Devlin</name></author>
    <link href="http://arxiv.org/abs/1810.04805v2" rel="alternate" type="text/html"/>
    <link title="pdf" href="http://arxiv.org/pdf/1810.04805v2" rel="related" type="application/pdf"/>
  </entry>
</feed>"""


class TestArxivConnector:
    async def test_fetch_papers(self, fake_redis, httpx_mock: HTTPXMock):
        httpx_mock.add_response(text=ARXIV_XML, headers={"content-type": "application/xml"})
        conn = ArxivConnector(fake_redis)

        result = await conn.fetch_papers("transformers")

        assert isinstance(result, list)
        assert len(result) == 2

    async def test_xml_parsing_structure(self, fake_redis, httpx_mock: HTTPXMock):
        httpx_mock.add_response(text=ARXIV_XML, headers={"content-type": "application/xml"})
        conn = ArxivConnector(fake_redis)

        result = await conn.fetch_papers("transformers")
        paper = result[0]

        assert paper["title"] == "Attention Is All You Need"
        assert paper["authors"] == ["Ashish Vaswani", "Noam Shazeer"]
        assert paper["summary"].startswith("The dominant sequence")
        assert paper["published"] == "2017-06-12T17:57:34Z"
        assert paper["arxiv_id"] == "1706.03762v7"
        assert paper["pdf_url"] == "http://arxiv.org/pdf/1706.03762v7"

    async def test_xml_parsing_all_fields_present(self, fake_redis, httpx_mock: HTTPXMock):
        httpx_mock.add_response(text=ARXIV_XML, headers={"content-type": "application/xml"})
        conn = ArxivConnector(fake_redis)

        result = await conn.fetch_papers("bert")

        for paper in result:
            assert "title" in paper
            assert "authors" in paper
            assert "summary" in paper
            assert "published" in paper
            assert "arxiv_id" in paper
            assert "pdf_url" in paper

    async def test_parse_feed_static(self):
        """Test the static XML parser directly."""
        papers = ArxivConnector._parse_feed(ARXIV_XML)
        assert len(papers) == 2
        assert papers[1]["title"] == "BERT: Pre-training of Deep Bidirectional Transformers"
        assert papers[1]["authors"] == ["Jacob Devlin"]
        assert papers[1]["arxiv_id"] == "1810.04805v2"


# ---------------------------------------------------------------------------
# NpmRegistryConnector
# ---------------------------------------------------------------------------


class TestNpmRegistryConnector:
    async def test_fetch_package(self, fake_redis, httpx_mock: HTTPXMock):
        payload = {
            "name": "express",
            "description": "Fast, unopinionated, minimalist web framework",
            "dist-tags": {"latest": "4.18.2"},
        }
        httpx_mock.add_response(json=payload)
        conn = NpmRegistryConnector(fake_redis)

        result = await conn.fetch_package("express")

        assert result["name"] == "express"
        assert "dist-tags" in result

    async def test_fetch_downloads(self, fake_redis, httpx_mock: HTTPXMock):
        payload = {"downloads": 25000000, "package": "express", "start": "2026-03-01", "end": "2026-03-31"}
        httpx_mock.add_response(json=payload)
        conn = NpmRegistryConnector(fake_redis)

        result = await conn.fetch_downloads("express")

        assert result["downloads"] == 25000000
        assert result["package"] == "express"


# ---------------------------------------------------------------------------
# PyPIConnector
# ---------------------------------------------------------------------------


class TestPyPIConnector:
    async def test_fetch_package(self, fake_redis, httpx_mock: HTTPXMock):
        payload = {
            "info": {
                "name": "requests",
                "version": "2.31.0",
                "summary": "Python HTTP for Humans.",
                "author": "Kenneth Reitz",
            },
            "releases": {},
        }
        httpx_mock.add_response(json=payload)
        conn = PyPIConnector(fake_redis)

        result = await conn.fetch_package("requests")

        assert result["info"]["name"] == "requests"
        assert result["info"]["version"] == "2.31.0"
        assert "releases" in result


# ---------------------------------------------------------------------------
# FREDConnector
# ---------------------------------------------------------------------------


class TestFREDConnector:
    async def test_fetch_series(self, fake_redis, httpx_mock: HTTPXMock):
        payload = {
            "realtime_start": "2026-03-31",
            "realtime_end": "2026-03-31",
            "observation_start": "1776-07-04",
            "observation_end": "9999-12-31",
            "units": "lin",
            "output_type": 1,
            "file_type": "json",
            "order_by": "observation_date",
            "sort_order": "desc",
            "count": 30,
            "observations": [
                {"date": "2026-01-01", "value": "29500.0"},
                {"date": "2025-10-01", "value": "29000.0"},
            ],
        }
        httpx_mock.add_response(json=payload)
        conn = FREDConnector(fake_redis, api_key="test-key-123")

        result = await conn.fetch_series("GDP")

        assert "observations" in result
        assert len(result["observations"]) == 2
        assert result["observations"][0]["date"] == "2026-01-01"

    async def test_api_key_stored(self, fake_redis):
        conn = FREDConnector(fake_redis, api_key="my-secret-key")
        assert conn.api_key == "my-secret-key"


# ---------------------------------------------------------------------------
# EIAConnector
# ---------------------------------------------------------------------------


class TestEIAConnector:
    async def test_fetch_series(self, fake_redis, httpx_mock: HTTPXMock):
        payload = {
            "response": {
                "data": [
                    {"period": "2026-02", "value": 95.5},
                    {"period": "2026-01", "value": 92.3},
                ],
            },
        }
        httpx_mock.add_response(json=payload)
        conn = EIAConnector(fake_redis, api_key="eia-test-key")

        result = await conn.fetch_series("PET.RWTC.M")

        assert "response" in result
        assert len(result["response"]["data"]) == 2
        assert result["response"]["data"][0]["value"] == 95.5

    async def test_api_key_stored(self, fake_redis):
        conn = EIAConnector(fake_redis, api_key="my-eia-key")
        assert conn.api_key == "my-eia-key"
