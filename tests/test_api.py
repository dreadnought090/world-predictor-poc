import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from world_predictor.api.app import app, lifespan


@pytest_asyncio.fixture
async def client():
    async with lifespan(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


@pytest.mark.asyncio
async def test_root(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    # Root serves HTML dashboard or JSON API info
    content_type = resp.headers.get("content-type", "")
    if "html" in content_type:
        assert "root" in resp.text
    else:
        data = resp.json()
        assert data["message"] == "World Predictor API"


@pytest.mark.asyncio
async def test_api_info(client):
    resp = await client.get("/api")
    assert resp.status_code == 200
    data = resp.json()
    assert data["version"] == "0.2.0"


@pytest.mark.asyncio
async def test_countries(client):
    resp = await client.get("/countries")
    assert resp.status_code == 200
    data = resp.json()
    countries = data["countries"]
    assert len(countries) > 0
    codes = [c["code"] for c in countries]
    assert "US" in codes


@pytest.mark.asyncio
async def test_predictions(client):
    resp = await client.get("/predictions/US")
    assert resp.status_code == 200
    data = resp.json()
    assert data["country"] == "US"
    assert "metrics" in data
    assert data["metrics"]["economic_sentiment"] > 0


@pytest.mark.asyncio
async def test_all_predictions(client):
    resp = await client.get("/predictions")
    assert resp.status_code == 200
    data = resp.json()
    assert "US" in data


@pytest.mark.asyncio
async def test_agents(client):
    resp = await client.get("/agents/US?limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 10
    assert len(data["agents"]) == 10
    agent = data["agents"][0]
    assert "iq" in agent["demographics"]


@pytest.mark.asyncio
async def test_agents_have_realistic_demographics(client):
    resp = await client.get("/agents/IN?limit=5")
    data = resp.json()
    for agent in data["agents"]:
        assert agent["location"] == "IN"
        assert int(agent["demographics"]["age"]) >= 18
        assert agent["economic"]["income"] > 0


@pytest.mark.asyncio
async def test_status(client):
    resp = await client.get("/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "countries" in data
    assert "total_agents" in data
    assert data["total_agents"] > 0


@pytest.mark.asyncio
async def test_simulate(client):
    payload = [
        {
            "title": "Test headline",
            "source": {"name": "Reuters", "politics": 0.0, "credibility": 0.9},
            "category": "ECONOMIC_POLICY",
            "content": "Test content",
            "url": "https://example.com",
            "region": "US",
            "impact": 0.5,
        }
    ]
    resp = await client.post("/simulate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["day"] >= 1
    assert "metrics" in data
    assert "reactions" in data
    assert "all_countries" in data


@pytest.mark.asyncio
async def test_history(client):
    resp = await client.get("/history/US")
    assert resp.status_code == 200
    data = resp.json()
    assert data["country"] == "US"


@pytest.mark.asyncio
async def test_news_archive(client):
    resp = await client.get("/news/archive")
    assert resp.status_code == 200
    data = resp.json()
    assert "stats" in data
