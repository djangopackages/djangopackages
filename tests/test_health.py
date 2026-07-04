from unittest.mock import AsyncMock, patch

from django.test import override_settings

LOCMEM_CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
}


@override_settings(CACHES=LOCMEM_CACHES, REDIS_URL="redis://localhost:6379/0")
def test_health_endpoint(db, tp):
    with patch("redis.asyncio.Redis.ping", new_callable=AsyncMock):
        response = tp.client.get("/health/", headers={"accept": "application/json"})

    assert response.status_code == 200
    assert response.json() == {
        "Cache(alias='default')": "OK",
        "Database(alias='default')": "OK",
        "Redis(db=0, host='localhost', port=6379)": "OK",
    }
