from dataclasses import dataclass
from typing import List, Dict, Any
from world_predictor.data.agents import Agent
from world_predictor.data.news import NewsItem

@dataclass
class SimulationState:
    agents: List[Agent]
    news_items: List[NewsItem]
    current_day: int
    parameters: Dict[str, float]

class ReactionTypes:
    SUPPORT = 'SUPPORT'
    OPPOSITION = 'OPPOSITION'
    APATHY = 'APATHY'
    CONFUSION = 'CONFUSION'
    FEAR = 'FEAR'

class TrustModel:
    def calculate_trust(self, agent: Agent, news_source) -> float:
        """Calculate the level of trust an agent has in a specific news source."""
        # Political alignment
        alignment = 1 - abs(agent.politics - news_source.politics)
        # historical_trust = agent.trust_history.get(news_source, 0.5) 
        historical_trust = 0.5
        # Source credibility
        credibility = news_source.credibility
        return (alignment * 0.3) + (historical_trust * 0.4) + (credibility * 0.3)
