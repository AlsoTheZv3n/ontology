"""Tests for API routes — uses FastAPI TestClient with mocked DB."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient


class _FakeConn:
    """Async context manager mock for pool.acquire()."""

    def __init__(self):
        self.fetch = AsyncMock(return_value=[])
        self.fetchval = AsyncMock(return_value=0)
        self.fetchrow = AsyncMock(return_value=None)
        self.execute = AsyncMock()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class _FakePool:
    """Mock pool with working acquire() async context manager."""

    def __init__(self):
        self._conn = _FakeConn()

    def acquire(self):
        return self._conn


@pytest.fixture
def client():
    """Create a test client with mocked pool and redis."""
    from api.main import app

    app.state.pool = _FakePool()
    app.state.redis = AsyncMock()

    return TestClient(app, raise_server_exceptions=False)


class TestHealthEndpoint:
    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestObjectsEndpoints:
    def test_list_objects(self, client):
        with patch("api.routes.objects.OntologyReader") as MockReader:
            instance = MockReader.return_value
            instance.list_objects = AsyncMock(return_value=([], 0))

            response = client.get("/objects")
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "total" in data

    def test_list_objects_with_type_filter(self, client):
        with patch("api.routes.objects.OntologyReader") as MockReader:
            instance = MockReader.return_value
            instance.list_objects = AsyncMock(return_value=([], 0))

            response = client.get("/objects?type=company")
            assert response.status_code == 200

    def test_get_object_not_found(self, client):
        with patch("api.routes.objects.OntologyReader") as MockReader:
            instance = MockReader.return_value
            instance.get_object = AsyncMock(return_value=None)

            response = client.get("/objects/nonexistent")
            assert response.status_code == 404

    def test_get_object_found(self, client):
        obj = {
            "id": uuid4(),
            "type": "company",
            "key": "apple",
            "properties": {"name": "Apple"},
            "sources": {"wikipedia": {}},
            "created_at": "2026-01-01T00:00:00",
            "updated_at": "2026-01-01T00:00:00",
        }
        with patch("api.routes.objects.OntologyReader") as MockReader:
            instance = MockReader.return_value
            instance.get_object = AsyncMock(return_value=obj)

            response = client.get("/objects/apple")
            assert response.status_code == 200
            assert response.json()["key"] == "apple"

    def test_get_links(self, client):
        with patch("api.routes.objects.OntologyReader") as MockReader:
            instance = MockReader.return_value
            instance.get_links = AsyncMock(return_value=[])

            response = client.get("/objects/apple/links")
            assert response.status_code == 200
            assert response.json() == []

    def test_get_timeline(self, client):
        with patch("api.routes.objects.OntologyReader") as MockReader:
            instance = MockReader.return_value
            instance.get_timeline = AsyncMock(return_value=[])

            response = client.get("/objects/apple/timeline")
            assert response.status_code == 200


class TestGraphEndpoint:
    def test_get_graph(self, client):
        graph = {"nodes": [], "edges": []}
        with patch("api.routes.graph.OntologyReader") as MockReader:
            instance = MockReader.return_value
            instance.get_graph = AsyncMock(return_value=graph)

            response = client.get("/graph?root=apple&depth=2")
            assert response.status_code == 200
            assert "nodes" in response.json()
            assert "edges" in response.json()

    def test_get_graph_requires_root(self, client):
        response = client.get("/graph")
        assert response.status_code == 422  # missing required param


class TestSearchEndpoints:
    def test_search(self, client):
        with patch("api.routes.search.OntologyReader") as MockReader:
            instance = MockReader.return_value
            instance.search = AsyncMock(return_value=[])

            response = client.get("/search?q=apple")
            assert response.status_code == 200
            assert response.json() == []

    def test_search_requires_query(self, client):
        response = client.get("/search")
        assert response.status_code == 422


class TestInsightsEndpoints:
    def test_stats(self, client):
        response = client.get("/insights/stats")
        assert response.status_code == 200
        data = response.json()
        assert "object_counts" in data
        assert "total_links" in data

    def test_top_companies(self, client):
        with patch("api.routes.insights.OntologyReader") as MockReader:
            instance = MockReader.return_value
            instance.get_top_by_metric = AsyncMock(return_value=[])

            response = client.get("/insights/top?metric=market_cap")
            assert response.status_code == 200


class TestTrendingEndpoint:
    def test_trending(self, client):
        response = client.get("/insights/trending")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_movers(self, client):
        response = client.get("/insights/movers")
        assert response.status_code == 200

    def test_stale(self, client):
        response = client.get("/insights/stale?hours=24")
        assert response.status_code == 200


class TestSuggestEndpoint:
    def test_suggest_returns_results(self, client):
        response = client.get("/search/suggest?q=app")
        assert response.status_code == 200

    def test_suggest_empty_query(self, client):
        response = client.get("/search/suggest?q=")
        assert response.status_code == 200
        assert response.json() == []


class TestSyncEndpoints:
    def test_list_sources(self, client):
        response = client.get("/sync/sources")
        assert response.status_code == 200
        assert "wikipedia" in response.json()["sources"]

    def test_trigger_invalid_source(self, client):
        response = client.post("/sync/invalid_source")
        assert response.status_code == 400

    def test_trigger_valid_source(self, client):
        with patch("api.routes.sync.create_pool") as mock_pool:
            mock_arq = AsyncMock()
            mock_pool.return_value = mock_arq

            response = client.post("/sync/wikipedia")
            assert response.status_code == 200
            assert response.json()["status"] == "queued"
