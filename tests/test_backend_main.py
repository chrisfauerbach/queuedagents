"""Tests for backend.app.main — health endpoint, CORS, app config."""


async def test_health_endpoint(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_unknown_route_404(client):
    resp = await client.get("/api/nonexistent")
    assert resp.status_code in (404, 405)


async def test_app_title():
    from backend.app.main import app

    assert app.title == "Queued Agents API"


async def test_routers_registered():
    from backend.app.main import app

    paths = [route.path for route in app.routes]
    assert "/api/jobs" in paths
    assert "/api/health" in paths
    assert "/api/prompts" in paths
    assert "/api/leaderboard" in paths
