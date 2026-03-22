from fastapi import APIRouter, Depends
from typing import List

from world_predictor.simulation.engine import SimulationEngine
from world_predictor.data.agents import AgentGenerator
from world_predictor.api.container import get_simulation_engine, get_agent_generator
from world_predictor.api.models import SimulationResult

router = APIRouter()

@router.post("/simulate", response_model=SimulationResult)
async def simulate(
    news_items: List[dict],
    engine: SimulationEngine = Depends(get_simulation_engine)
):
    """Run a simulation with provided news items"""
    from world_predictor.data.news import NewsItem, NewsSource
    
    items = []
    for ni in news_items:
        source_data = ni.get('source', {})
        source = NewsSource(
            name=source_data.get('name', 'Unknown'),
            politics=source_data.get('politics', 0.0),
            credibility=source_data.get('credibility', 0.5)
        )
        item = NewsItem(
            title=ni.get('title', ''),
            source=source,
            category=ni.get('category', 'GENERAL'),
            content=ni.get('content', ''),
            url=ni.get('url', ''),
            region=ni.get('region', 'Global'),
            impact=ni.get('impact', 0.1)
        )
        items.append(item)
        
    result = engine.process_day(items)
    return result

@router.get("/status")
async def get_status(
    engine: SimulationEngine = Depends(get_simulation_engine)
):
    """Get current simulation status"""
    return {"status": "running", "day": engine.state.current_day}

@router.post("/agents/generate")
async def generate_agents(
    country: str,
    count: int = 1000,
    generator: AgentGenerator = Depends(get_agent_generator)
):
    """Generate agents for a specific country"""
    agents = generator.generate_agents_for_country(country, count)
    return {"count": len(agents), "country": country}
