from fastapi import APIRouter, Depends, Query
from typing import List

from world_predictor.simulation.engine import SimulationEngine
from world_predictor.data.agents import AgentGenerator
from world_predictor.api.container import get_simulation_engine, get_agent_generator
from world_predictor.api.models import NewsItemInput, SimulationResult

router = APIRouter()


@router.post("/simulate", response_model=SimulationResult)
async def simulate(
    news_items: List[NewsItemInput],
    engine: SimulationEngine = Depends(get_simulation_engine),
):
    """Run a simulation with provided news items (processes all countries)."""
    from world_predictor.data.news import NewsItem, NewsSource

    items = []
    for ni in news_items:
        source_data = ni.source
        source = NewsSource(
            name=source_data.name,
            politics=source_data.politics,
            credibility=source_data.credibility,
        )
        item = NewsItem(
            title=ni.title,
            source=source,
            category=ni.category,
            content=ni.content,
            url=ni.url,
            region=ni.region,
            impact=ni.impact,
        )
        items.append(item)

    results = engine.process_day(items)

    # Return first country for backward compatibility, plus all countries
    first_country = next(iter(results.values())) if results else {}
    return {
        "day": first_country.get("day", 0),
        "metrics": first_country.get("metrics", {}),
        "consensus": first_country.get("consensus", {}),
        "reactions": first_country.get("reactions", {}),
        "agent_updates": engine.engines[first_country["country"]].get_agent_updates()
        if first_country.get("country") in engine.engines else [],
        "all_countries": {
            country: {
                "country": country,
                "day": r["day"],
                "metrics": r["metrics"],
                "consensus": r["consensus"],
                "reactions": r["reactions"],
                "agent_count": r["agent_count"],
            }
            for country, r in results.items()
        },
    }


@router.get("/status")
async def get_status(engine: SimulationEngine = Depends(get_simulation_engine)):
    """Get current simulation status for all countries."""
    return {
        "status": "running",
        "metadata": engine.metadata,
        "countries": {
            code: {"day": e.current_day, "agent_count": len(e.agents)}
            for code, e in engine.engines.items()
        },
        "total_agents": sum(len(e.agents) for e in engine.engines.values()),
    }


@router.post("/agents/generate")
async def generate_agents(
    country: str = Query(min_length=2, max_length=2),
    count: int = Query(default=1000, ge=1, le=10000),
    generator: AgentGenerator = Depends(get_agent_generator),
):
    """Generate agents for a specific country."""
    agents = generator.generate_agents_for_country(country, count)
    return {"count": len(agents), "country": country}
