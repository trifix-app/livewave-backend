import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services import cache


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.mark.asyncio
async def test_root():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "LiveWave TV" in data["app"]


@pytest.mark.asyncio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "upstream_url" in data
        assert "fallback_active" in data


@pytest.mark.asyncio
async def test_get_categories():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/categories")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total"] > 0
        assert len(data["categories"]) > 0

        first_cat = data["categories"][0]
        assert "id" in first_cat
        assert "name" in first_cat
        assert first_cat["name"] == "Sports"


@pytest.mark.asyncio
async def test_get_category_by_id():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/categories/1")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["category"]["id"] == 1
        assert data["category"]["name"] == "Sports"


@pytest.mark.asyncio
async def test_get_nonexistent_category():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/categories/99999")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_category_channels():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/categories/1/channels")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["category_id"] == 1
        assert len(data["channels"]) > 0

        # Check first channel fields
        channel = data["channels"][0]
        assert channel["name"] == "beIN Sports 1"
        assert channel["category_id"] == 1
        assert channel["is_live"] is True
        assert channel["stream_format"] == "hls"


@pytest.mark.asyncio
async def test_get_channel_detail_with_playable_stream():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/channels/101")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        channel = data["channel"]
        assert channel["id"] == 101
        assert channel["name"] == "beIN Sports 1"
        assert channel["stream_url"] is not None
        assert channel["stream_url"].endswith(".m3u8")
        assert channel["stream_format"] == "hls"
        assert "headers" in channel


@pytest.mark.asyncio
async def test_get_nonexistent_channel():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/channels/99999")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_cache_behavior():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Initial request should cache
        assert cache.get("v1:categories") is None
        res1 = await client.get("/api/v1/categories")
        assert res1.status_code == 200
        assert cache.get("v1:categories") is not None

        # Second request should read from cache
        res2 = await client.get("/api/v1/categories")
        assert res2.status_code == 200
        assert res1.json() == res2.json()


@pytest.mark.asyncio
async def test_ping():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/ping")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["message"] == "pong"
        assert "timestamp" in data


@pytest.mark.asyncio
async def test_get_all_channels():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/channels")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total"] > 0
        assert len(data["channels"]) > 0


@pytest.mark.asyncio
async def test_search_channels():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Search for "Sports"
        response = await client.get("/api/v1/search?q=Sports")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total"] > 0
        assert any("Sports" in ch["name"] for ch in data["channels"])


@pytest.mark.asyncio
async def test_stream_status():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/channels/101/status")
        assert response.status_code == 200
        data = response.json()
        assert data["channel_id"] == 101
        assert "is_reachable" in data
        assert "latency_ms" in data
        assert data["is_hls"] is True


@pytest.mark.asyncio
async def test_admin_login_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/admin/login",
            json={"username": "admin", "password": "admin1234"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert "token" in data
        assert data["username"] == "admin"


@pytest.mark.asyncio
async def test_admin_login_invalid():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/admin/login",
            json={"username": "admin", "password": "wrongpassword"},
        )
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_admin_unauthorized_access():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/v1/admin/cache/flush")
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_admin_cache_flush():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Login
        login_res = await client.post(
            "/api/v1/admin/login",
            json={"username": "admin", "password": "admin1234"},
        )
        token = login_res.json()["token"]

        # 2. Flush cache with Bearer token
        flush_res = await client.post(
            "/api/v1/admin/cache/flush",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert flush_res.status_code == 200
        assert flush_res.json()["success"] is True


@pytest.mark.asyncio
async def test_channel_epg():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/channels/101/epg")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["channel_id"] == 101
        assert "current_program" in data
        assert data["current_program"]["title"] is not None
        assert len(data["schedule"]) > 0


@pytest.mark.asyncio
async def test_all_epg():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/epg")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total"] > 0
        assert len(data["epg"]) > 0



