from world_predictor.simulation.engine import SimulationEngine
from world_predictor.data.agents import AgentGenerator
from world_predictor.data.news import NewsProcessor

def get_simulation_engine() -> SimulationEngine:
    # This acts as a placeholder dependency that gets overridden
    # in app.py's lifespan context manager with the global singleton.
    return SimulationEngine([])

def get_agent_generator() -> AgentGenerator:
    return AgentGenerator()

def get_news_processor() -> NewsProcessor:
    return NewsProcessor()
