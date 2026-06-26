import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from world_predictor.api.app import app, lifespan


@pytest_asyncio.fixture
async def client(tmp_path, monkeypatch):
    monkeypatch.setenv("WP_DB_PATH", str(tmp_path / "world_predictor_test.db"))
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
async def test_prediction_explanation(client):
    resp = await client.get("/predictions/US/explain")
    assert resp.status_code == 200
    data = resp.json()
    assert data["country"] == "US"
    assert data["confidence"]["level"] in {"low", "medium", "high"}
    assert data["drivers"]
    assert "low_trust" in data["risk_components"]


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
    assert data["all_countries"]["US"]["agent_count"] > 0


@pytest.mark.asyncio
async def test_simulate_rejects_invalid_news_payload(client):
    payload = [
        {
            "title": "Impossible impact",
            "source": {"name": "Reuters", "politics": 0.0, "credibility": 0.9},
            "category": "ECONOMIC_POLICY",
            "region": "US",
            "impact": 2.0,
        }
    ]
    resp = await client.post("/simulate", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_batch_days_validation(client):
    resp = await client.post("/simulate/batch?days=0")
    assert resp.status_code == 422


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


@pytest.mark.asyncio
async def test_market_signals_frontend_contract(client, monkeypatch):
    from datetime import datetime, timezone
    from world_predictor.data.market import MarketDataFetcher

    def fake_fetch_exchange_rates(self, base="USD"):
        self._last_fetch = datetime(2026, 1, 1, tzinfo=timezone.utc)
        return {"USD": 1.0, "EUR": 0.8, "JPY": 160.0}

    monkeypatch.setattr(MarketDataFetcher, "fetch_exchange_rates", fake_fetch_exchange_rates)

    resp = await client.get("/market/signals")
    assert resp.status_code == 200
    data = resp.json()
    assert set(data) == {"base_currency", "fetched_at", "stale", "signals"}
    assert data["base_currency"] == "USD"
    assert data["stale"] is False
    assert isinstance(data["signals"], list)

    by_country = {signal["country"]: signal for signal in data["signals"]}
    assert by_country["US"] == {
        "country": "US",
        "currency": "USD",
        "exchange_rate": 1.0,
        "strength": 0.5,
    }
    assert by_country["DE"]["currency"] == "EUR"
    assert by_country["DE"]["exchange_rate"] == 0.8


@pytest.mark.asyncio
async def test_scenario_parse_endpoint(client):
    resp = await client.post(
        "/scenarios/parse",
        json={"text": "China blocks rare earth exports to the US for 90 days"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["event_type"] == "TRADE_WAR"
    assert data["duration_days"] == 90
    assert "CN" in data["affected_countries"]
    assert "US" in data["affected_countries"]
    assert "trade" in data["sectors"]
    assert data["confidence"]["level"] in {"medium", "high"}


@pytest.mark.asyncio
async def test_validation_backtest_endpoint(client):
    payload = {
        "event_name": "US Capitol Riot",
        "lookback_days": 3,
        "daily_results": [
            {"US": {"day": 1, "metrics": {"revolution_risk": 0.2}}},
            {"US": {"day": 2, "metrics": {"revolution_risk": 0.34}}},
            {"US": {"day": 3, "metrics": {"revolution_risk": 0.55}}},
        ],
    }
    resp = await client.post("/validation/backtest", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["event"]["name"] == "US Capitol Riot"
    assert data["source"] == "request"
    assert data["days_evaluated"] == 3
    assert data["result"]["risk_increase_detected"] is True
    assert data["summary"]["total_events"] == 1
