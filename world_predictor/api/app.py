import os
import logging
from contextlib import asynccontextmanager

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

from world_predictor.config import api_config, sim_config
from world_predictor.simulation.engine import SimulationEngine
from world_predictor.data.agents import AgentGenerator
from world_predictor.data.news import NewsProcessor
from world_predictor.data.database import Database
from world_predictor.api.routes import router
from world_predictor.api.container import get_simulation_engine

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state
agent_generator = AgentGenerator()
news_processor = NewsProcessor(
    newsapi_key=os.environ.get("NEWSAPI_KEY"),
    anthropic_key=os.environ.get("ANTHROPIC_API_KEY"),
)
simulation_engine = None
db = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global simulation_engine, db

    # Initialize database
    db = Database()
    logger.info("Database initialized at %s", db.path)

    # Initialize multi-country simulation engine
    simulation_engine = SimulationEngine(db=db)
    logger.info(
        "World Predictor initialized: %d countries, %d total agents",
        len(simulation_engine.countries),
        sum(len(e.agents) for e in simulation_engine.engines.values()),
    )

    # Override dependency
    app.dependency_overrides[get_simulation_engine] = lambda: simulation_engine
    yield

    # Cleanup
    if db:
        db.close()


cfg = api_config()
app = FastAPI(
    title="World Predictor API",
    description="Multi-Agent AI Simulation for Global Trends Prediction",
    version="0.2.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=cfg.get("cors_origins", ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# Serve frontend (prefer built dist/, fallback to dev frontend/)
_dist_dir = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
_frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
_assets_dir = _dist_dir / "assets"
if _assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(_assets_dir)), name="assets")
elif _frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_frontend_dir)), name="frontend")


# ---- Core Endpoints ----

@app.get("/")
async def root():
    """Serve dashboard if frontend exists, otherwise API info."""
    if _dist_dir.exists() and (_dist_dir / "index.html").exists():
        return FileResponse(str(_dist_dir / "index.html"))
    if _frontend_dir.exists() and (_frontend_dir / "index.html").exists():
        return FileResponse(str(_frontend_dir / "index.html"))
    return {
        "message": "World Predictor API",
        "version": "0.2.0",
        "countries": simulation_engine.countries if simulation_engine else [],
    }


@app.get("/api")
async def api_info():
    return {
        "message": "World Predictor API",
        "version": "0.2.0",
        "countries": simulation_engine.countries if simulation_engine else [],
    }


@app.get("/countries")
async def get_countries():
    """Get list of active countries with agent counts."""
    if not simulation_engine:
        return {"countries": []}
    return {
        "countries": [
            {
                "code": code,
                "agent_count": len(engine.agents),
                "current_day": engine.current_day,
            }
            for code, engine in simulation_engine.engines.items()
        ]
    }


# ---- Predictions (REAL DATA) ----

@app.get("/predictions/{country}")
async def get_predictions(country: str):
    """Get real predictions for a specific country (no more dummy data)."""
    if not simulation_engine:
        return {"error": "Engine not initialized"}
    return simulation_engine.get_predictions(country)


@app.get("/predictions")
async def get_all_predictions():
    """Get predictions for all countries."""
    if not simulation_engine:
        return {"error": "Engine not initialized"}
    return simulation_engine.get_all_predictions()


# ---- News ----

@app.post("/fetch_news")
async def fetch_news():
    """Fetch real news, classify, and run simulation for all countries."""
    items = news_processor.fetch_daily_news()
    categorized = news_processor.categorize_news(items)

    # Run simulation with fetched news
    sim_results = {}
    if simulation_engine and items:
        sim_results = simulation_engine.process_day(items)

    return {
        "total_news": len(items),
        "categories": {cat: len(news) for cat, news in categorized.items()},
        "simulation_results": {
            country: {
                "day": r["day"],
                "metrics": r["metrics"],
                "reactions": r["reactions"],
            }
            for country, r in sim_results.items()
        },
        "news_sample": [
            {
                "title": item.title,
                "source": item.source.name,
                "category": item.category,
                "region": item.region,
                "impact": item.impact,
            }
            for item in items[:20]
        ],
    }


# ---- Simulation ----

@app.post("/simulate/batch")
async def simulate_batch(days: int = 10):
    """Run multiple days of simulation with current news."""
    if not simulation_engine:
        return {"error": "Engine not initialized"}

    items = news_processor.fetch_daily_news()
    results = simulation_engine.simulate_batch(items, days=days)

    return {
        "days_simulated": days,
        "news_items_used": len(items),
        "results": [
            {country: {"day": r["day"], "metrics": r["metrics"], "revolution_risk": r["metrics"].get("revolution_risk", 0)}
             for country, r in day_result.items()}
            for day_result in results
        ],
    }


# ---- History ----

@app.get("/history/{country}")
async def get_history(country: str, days: int = 30):
    """Get historical metrics for a country."""
    if not db:
        return {"error": "Database not initialized"}
    history = db.get_metrics_history(country, days)
    return {"country": country, "days": len(history), "history": history}


@app.get("/history")
async def get_all_history():
    """Get latest metrics for all countries."""
    if not db:
        return {"error": "Database not initialized"}
    return db.get_all_latest_metrics()


# ---- News Archive ----

@app.get("/news/archive")
async def search_news_archive(category: str = None, region: str = None, limit: int = 50):
    """Search the news archive."""
    if not db:
        return {"error": "Database not initialized"}
    return {
        "results": db.search_news(category=category, region=region, limit=limit),
        "stats": db.get_news_stats(),
    }


# ---- Agents ----

@app.get("/agents/{country}")
async def get_agents(country: str, limit: int = 100):
    """Get agents for a specific country."""
    if simulation_engine and country in simulation_engine.engines:
        agents = simulation_engine.engines[country].agents[:limit]
        return {"agents": [vars(a) for a in agents], "count": len(agents)}
    # Fallback: generate fresh agents
    agents = agent_generator.generate_agents_for_country(country, limit)
    return {"agents": [vars(a) for a in agents], "count": len(agents)}


@app.get("/country/{country}/profile")
async def get_country_profile(country: str):
    """Get full country profile: demographics breakdown, metrics, institutions, relations, news."""
    from collections import Counter
    import numpy as np

    if not simulation_engine or country not in simulation_engine.engines:
        return {"error": f"Country {country} not loaded"}

    ce = simulation_engine.engines[country]
    agents = ce.agents

    # Demographics breakdowns
    def dist(key):
        c = Counter(a.demographics[key] for a in agents)
        total = len(agents)
        return [{"label": k, "count": v, "pct": round(v / total * 100, 1)} for k, v in c.most_common()]

    ages = [int(a.demographics["age"]) for a in agents]
    iqs = [int(a.demographics["iq"]) for a in agents]
    incomes = [a.economic["income"] for a in agents]
    politics_vals = [a.politics for a in agents]

    # Age histogram buckets
    age_buckets = Counter()
    for age in ages:
        bucket = f"{(age // 10) * 10}s"
        age_buckets[bucket] += 1
    age_dist = [{"label": k, "count": v, "pct": round(v / len(agents) * 100, 1)}
                for k, v in sorted(age_buckets.items())]

    # Income quintiles
    inc_arr = np.array(incomes)
    quintiles = [round(float(np.percentile(inc_arr, p))) for p in [20, 40, 60, 80, 100]]

    # Politics distribution
    pol_buckets = {"far_left": 0, "left": 0, "center": 0, "right": 0, "far_right": 0}
    for p in politics_vals:
        if p < -0.5: pol_buckets["far_left"] += 1
        elif p < -0.1: pol_buckets["left"] += 1
        elif p < 0.1: pol_buckets["center"] += 1
        elif p < 0.5: pol_buckets["right"] += 1
        else: pol_buckets["far_right"] += 1
    pol_dist = [{"label": k, "count": v, "pct": round(v / len(agents) * 100, 1)} for k, v in pol_buckets.items()]

    # Current metrics
    metrics = ce._calculate_metrics()
    risk = ce._calculate_revolution_risk(metrics, ce.reaction_history.get(ce.current_day, {}))
    metrics["revolution_risk"] = risk

    # Institutions
    institutions = []
    if country in simulation_engine.institutions:
        institutions = [
            {"name": i.name, "type": i.institution_type, "politics": i.politics,
             "credibility": i.credibility, "power": i.power,
             "active_policies": [p.name for p in i.active_policies]}
            for i in simulation_engine.institutions[country]
        ]

    # Relations
    relations = simulation_engine.inter_country.get_country_network(country)

    # Country news (from archive)
    country_news = []
    if db:
        country_news = db.search_news(region=country, limit=20)
        # Also get Global news
        global_news = db.search_news(region="Global", limit=10)
        country_news = country_news + global_news

    # History
    history = []
    if db:
        history = db.get_metrics_history(country, 30)

    return {
        "country": country,
        "day": ce.current_day,
        "agent_count": len(agents),
        "metrics": metrics,
        "demographics": {
            "race": dist("race"),
            "religion": dist("religion"),
            "education": dist("education"),
            "gender": dist("gender"),
            "age": age_dist,
            "politics": pol_dist,
        },
        "biometrics": {
            "iq": {"mean": round(float(np.mean(iqs)), 1), "std": round(float(np.std(iqs)), 1),
                   "min": int(np.min(iqs)), "max": int(np.max(iqs))},
            "income": {"mean": round(float(np.mean(incomes))), "median": round(float(np.median(incomes))),
                       "quintiles": quintiles},
            "age": {"mean": round(float(np.mean(ages)), 1), "median": int(np.median(ages)),
                    "min": int(np.min(ages)), "max": int(np.max(ages))},
            "optimism": {"mean": round(float(np.mean([a.behavior["optimism"] for a in agents])), 3)},
            "trust": {"mean": round(float(np.mean([a.behavior["trust_institutions"] for a in agents])), 3)},
            "risk_aversion": {"mean": round(float(np.mean([a.behavior["risk_aversion"] for a in agents])), 3)},
        },
        "institutions": institutions,
        "relations": relations,
        "news": country_news,
        "history": history,
    }


# ---- Visualization ----

@app.get("/viz/globe")
async def viz_globe():
    """Get Plotly JSON for globe visualization."""
    from world_predictor.simulation.visualization import Visualizer
    viz = Visualizer()
    if not simulation_engine:
        return {"error": "Engine not initialized"}

    # Collect agent data across all countries
    agent_data = []
    for country, engine in simulation_engine.engines.items():
        for agent in engine.agents[:200]:  # sample per country
            agent_data.append(vars(agent))

    fig = viz.create_3d_globe(agent_data)
    return fig.to_dict()


@app.get("/viz/dashboard")
async def viz_dashboard():
    """Get Plotly JSON for metrics dashboard."""
    from world_predictor.simulation.visualization import Visualizer
    viz = Visualizer()
    if not simulation_engine:
        return {"error": "Engine not initialized"}

    # Use global average metrics
    all_metrics = {}
    for country in simulation_engine.engines:
        pred = simulation_engine.get_predictions(country)
        all_metrics[country] = pred["metrics"]

    # Average across countries
    avg = {}
    if all_metrics:
        keys = list(next(iter(all_metrics.values())).keys())
        for k in keys:
            vals = [m[k] for m in all_metrics.values() if k in m]
            avg[k] = sum(vals) / len(vals) if vals else 0

    fig = viz.create_metrics_dashboard(avg)
    return fig.to_dict()


@app.get("/viz/trends")
async def viz_trends():
    """Get Plotly JSON for trend charts (requires history in DB)."""
    from world_predictor.simulation.visualization import Visualizer
    viz = Visualizer()
    if not db:
        return {"error": "Database not initialized"}

    # Get history for all countries
    all_data = []
    for country in (simulation_engine.countries if simulation_engine else []):
        history = db.get_metrics_history(country, 30)
        for h in history:
            all_data.append(h)

    if not all_data:
        return {"message": "No history yet. Run /fetch_news or /simulate/batch first."}

    fig = viz.create_trend_chart(all_data)
    return fig.to_dict()


# ---- Geopolitical Events ----

@app.post("/events/inject")
async def inject_event(
    event_type: str,
    name: str,
    affected_countries: str,  # comma-separated
    magnitude: float = 0.8,
    duration_days: int = 14,
):
    """Inject a geopolitical shock event into the simulation."""
    from world_predictor.simulation.events import GeoEvent
    if not simulation_engine:
        return {"error": "Engine not initialized"}
    countries = [c.strip() for c in affected_countries.split(",")]
    event = GeoEvent(
        event_type=event_type, name=name,
        affected_countries=countries,
        magnitude=magnitude, duration_days=duration_days,
    )
    simulation_engine.inject_event(event)
    return {"message": f"Event '{name}' injected", "affected": countries, "magnitude": magnitude}


@app.post("/events/preset/{preset_name}")
async def inject_preset_event(preset_name: str):
    """Inject a preset event (us_election, ukraine_war, pandemic_outbreak, etc.)."""
    import copy
    from world_predictor.simulation.events import PRESET_EVENTS
    if not simulation_engine:
        return {"error": "Engine not initialized"}
    if preset_name not in PRESET_EVENTS:
        return {"error": f"Unknown preset. Available: {list(PRESET_EVENTS.keys())}"}
    event = copy.deepcopy(PRESET_EVENTS[preset_name])
    simulation_engine.inject_event(event)
    return {"message": f"Preset event '{event.name}' injected", "type": event.event_type}


@app.get("/events/active")
async def get_active_events():
    """Get currently active geopolitical events."""
    if not simulation_engine:
        return {"error": "Engine not initialized"}
    current_day = next(iter(simulation_engine.engines.values())).current_day
    return {
        "active_events": simulation_engine.event_manager.get_active_events(current_day),
        "history_count": len(simulation_engine.event_manager.event_history),
    }


# ---- Institution Policies ----

@app.post("/policies/enact")
async def enact_policy(
    country: str,
    policy_name: str,
):
    """Enact a preset policy in a country."""
    import copy
    from world_predictor.simulation.institutions import PRESET_POLICIES
    if not simulation_engine:
        return {"error": "Engine not initialized"}
    if policy_name not in PRESET_POLICIES:
        return {"error": f"Unknown policy. Available: {list(PRESET_POLICIES.keys())}"}
    policy = copy.deepcopy(PRESET_POLICIES[policy_name])
    simulation_engine.enact_policy(country, policy)
    return {"message": f"Policy '{policy.name}' enacted in {country}"}


@app.get("/institutions/{country}")
async def get_institutions(country: str):
    """Get institutional actors for a country."""
    if not simulation_engine or country not in simulation_engine.institutions:
        return {"error": f"No institutions for {country}"}
    return {
        "institutions": [
            {
                "id": i.id, "name": i.name, "type": i.institution_type,
                "politics": i.politics, "credibility": i.credibility,
                "power": i.power, "active_policies": len(i.active_policies),
            }
            for i in simulation_engine.institutions[country]
        ]
    }


# ---- Inter-Country Dynamics ----

@app.get("/relations/{country}")
async def get_country_relations(country: str):
    """Get a country's trade, alliance, and rivalry relationships."""
    if not simulation_engine:
        return {"error": "Engine not initialized"}
    return simulation_engine.inter_country.get_country_network(country)


@app.get("/global/tension")
async def get_global_tension():
    """Get the global tension index."""
    if not simulation_engine:
        return {"error": "Engine not initialized"}
    all_metrics = {}
    for country in simulation_engine.engines:
        pred = simulation_engine.get_predictions(country)
        all_metrics[country] = pred["metrics"]
    tension = simulation_engine.inter_country.get_global_tension_index(all_metrics)
    return {"global_tension_index": round(tension, 4)}


# ---- Market Data ----

@app.get("/market/signals")
async def get_market_signals():
    """Get economic signals from real market data."""
    from world_predictor.data.market import MarketDataFetcher
    fetcher = MarketDataFetcher()
    return fetcher.get_all_signals()


# ---- Scenarios ----

@app.post("/scenarios/run")
async def run_scenario(
    name: str,
    description: str = "",
    preset_event: str = None,
    preset_policy: str = None,
    policy_country: str = "US",
    days: int = 30,
):
    """Run a what-if scenario."""
    import copy
    from world_predictor.simulation.scenarios import ScenarioEngine
    from world_predictor.simulation.events import PRESET_EVENTS
    from world_predictor.simulation.institutions import PRESET_POLICIES

    if not simulation_engine:
        return {"error": "Engine not initialized"}

    if simulation_engine.scenario_engine is None:
        simulation_engine.scenario_engine = ScenarioEngine()

    events = []
    if preset_event and preset_event in PRESET_EVENTS:
        events.append(copy.deepcopy(PRESET_EVENTS[preset_event]))

    policies = {}
    if preset_policy and preset_policy in PRESET_POLICIES:
        policies[policy_country] = [copy.deepcopy(PRESET_POLICIES[preset_policy])]

    # Fetch current news for scenario
    items = news_processor.fetch_daily_news()

    result = simulation_engine.scenario_engine.run_scenario(
        engine=simulation_engine,
        name=name, description=description,
        events=events or None,
        policies=policies or None,
        news_items=items,
        days=days,
    )

    return {
        "scenario_id": result.scenario_id,
        "name": result.name,
        "days_simulated": result.days_simulated,
        "events_injected": result.events_injected,
        "policies_injected": result.policies_injected,
        "final_state": result.final_state,
    }


@app.get("/scenarios/compare")
async def compare_scenarios(baseline_id: str, scenario_id: str):
    """Compare two scenario results."""
    if not simulation_engine or not simulation_engine.scenario_engine:
        return {"error": "No scenarios run yet"}
    return simulation_engine.scenario_engine.compare_scenarios(baseline_id, scenario_id)


# ---- Validation ----

@app.get("/validation/events")
async def get_historical_events():
    """Get available historical events for validation."""
    from world_predictor.validation.backtester import Backtester
    return Backtester.get_historical_events()


@app.get("/presets/events")
async def list_preset_events():
    """List available preset events."""
    from world_predictor.simulation.events import PRESET_EVENTS
    return {
        name: {"type": e.event_type, "name": e.name,
               "affected": e.affected_countries, "magnitude": e.magnitude}
        for name, e in PRESET_EVENTS.items()
    }


@app.get("/presets/policies")
async def list_preset_policies():
    """List available preset policies."""
    from world_predictor.simulation.institutions import PRESET_POLICIES
    return {
        name: {"name": p.name, "category": p.category,
               "magnitude": p.magnitude, "duration_days": p.duration_days}
        for name, p in PRESET_POLICIES.items()
    }


# ---- SPA Catch-all (must be last) ----

@app.get("/{full_path:path}")
async def spa_fallback(full_path: str):
    """Serve SPA index.html for client-side routes."""
    if _dist_dir.exists() and (_dist_dir / "index.html").exists():
        return FileResponse(str(_dist_dir / "index.html"))
    return {"error": "Not found"}
