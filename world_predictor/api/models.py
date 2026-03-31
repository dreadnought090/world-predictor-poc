from pydantic import BaseModel
from typing import List, Dict, Optional

class NewsRequest(BaseModel):
    sources: List[str] = []
    categories: List[str] = []

class PredictionResponse(BaseModel):
    country: str
    day: int
    agent_count: int
    metrics: Dict[str, float]

class AgentUpdate(BaseModel):
    id: str
    economic_stability: float
    optimism: float
    trust_institutions: float

class ReactionSummary(BaseModel):
    total_agents: int
    distribution: Dict[str, int]
    percentages: Dict[str, float]
    dominant: str

class CountrySimulationResult(BaseModel):
    country: str
    day: int
    metrics: dict
    consensus: dict
    reactions: ReactionSummary
    agent_count: int

class SimulationResult(BaseModel):
    day: int
    metrics: dict
    consensus: dict
    reactions: ReactionSummary
    agent_updates: List[AgentUpdate]

class BatchSimulateRequest(BaseModel):
    days: int = 10

class NewsSearchRequest(BaseModel):
    category: Optional[str] = None
    region: Optional[str] = None
    limit: int = 50
