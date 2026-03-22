from pydantic import BaseModel
from typing import List, Dict

class NewsRequest(BaseModel):
    sources: List[str]
    categories: List[str]

class PredictionResponse(BaseModel):
    country: str
    stability_score: float
    economic_flow: Dict[str, float]
    social_sentiment: Dict[str, float]

class AgentUpdate(BaseModel):
    id: str
    economic_stability: float
    optimism: float
    trust_institutions: float

class SimulationResult(BaseModel):
    day: int
    metrics: dict
    consensus: dict
    agent_updates: List[AgentUpdate]
