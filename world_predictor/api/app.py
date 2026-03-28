from fastapi import FastAPI
from contextlib import asynccontextmanager

from world_predictor.simulation.engine import SimulationEngine
from world_predictor.data.agents import AgentGenerator
from world_predictor.data.news import NewsProcessor
from world_predictor.api.routes import router
from world_predictor.api.container import get_simulation_engine
from world_predictor.api.models import NewsRequest

# Global state
agent_generator = AgentGenerator()
news_processor = NewsProcessor()
simulation_engine = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global simulation_engine
    # Generate initial agents on startup
    agents = agent_generator.generate_agents_for_country("US", 1000)
    simulation_engine = SimulationEngine(agents)
    
    # Overriding the router dependency to return the global engine instance
    app.dependency_overrides[get_simulation_engine] = lambda: simulation_engine
    print("World Predictor initialized with 1000 agents")
    yield
    # Clean up on shutdown
    pass

app = FastAPI(title="World Predictor API", lifespan=lifespan)
app.include_router(router)

@app.get("/")
async def root():
    return {"message": "World Predictor API"}

@app.get("/countries")
async def get_countries():
    """Get list of available countries"""
    return {"countries": ["US", "CN", "IN", "BR", "RU"]}

@app.post("/fetch_news")
async def fetch_news(request: NewsRequest):
    """Fetch news from specified sources"""
    return {"message": "News fetching initiated", "sources": request.sources}

@app.get("/predictions/{country}")
async def get_predictions(country: str):
    """Get predictions for a specific country"""
    return {
        "country": country,
        "stability_score": 0.75,
        "economic_flow": {"growth": 0.02, "inflation": 0.03},
        "social_sentiment": {"optimism": 0.65, "trust": 0.7}
    }

@app.get("/agents/{country}")
async def get_agents(country: str, limit: int = 100):
    """Get agents for a specific country"""
    agents = agent_generator.generate_agents_for_country(country, limit)
    return {"agents": [vars(a) for a in agents], "count": len(agents)}
