import pytest
import fakeredis.aioredis


@pytest.fixture
def fake_redis():
    """Provide a fake async Redis client for testing."""
    return fakeredis.aioredis.FakeRedis()
