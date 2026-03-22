from typing import List, Dict, Any
import numpy as np
from world_predictor.data.agents import Agent
from world_predictor.data.news import NewsItem
from world_predictor.simulation.models import SimulationState

class SimulationEngine:
    def __init__(self, agents: List[Agent]):
        self.agents = agents
        self.state = SimulationState(
            agents=agents,
            news_items=[],
            current_day=0,
            parameters=self._load_parameters()
        )

    def _load_parameters(self) -> Dict[str, float]:
        """Load simulation parameters"""
        return {
            "economic_impact_weight": 0.4,
            "social_impact_weight": 0.3,
            "political_impact_weight": 0.3,
            "news_decay_rate": 0.95,
            "consensus_threshold": 0.6
        }

    def process_day(self, news_items: List[NewsItem]) -> Dict[str, Any]:
        """Process a single day of simulation"""
        self.state.news_items.extend(news_items)
        self.state.current_day += 1

        # Apply news impacts to agents
        self._apply_news_impacts(news_items)

        # Calculate daily metrics
        metrics = self._calculate_metrics()

        # Build consensus
        consensus = self._build_consensus()

        return {
            "day": self.state.current_day,
            "metrics": metrics,
            "consensus": consensus,
            "agent_updates": self._get_agent_updates()
        }

    def _apply_news_impacts(self, news_items: List[NewsItem]):
        """Apply news impacts to agents"""
        for news in news_items:
            for agent in self.agents:
                impact = self._calculate_agent_impact(agent, news)
                self._apply_impact_to_agent(agent, impact)

    def _calculate_agent_impact(self, agent: Agent, news: NewsItem) -> float:
        """Calculate impact of news on a specific agent"""
        # Base impact from news
        base_impact = news.impact

        # Demographic factors
        if agent.demographics.get('race') == 'minority':
            base_impact *= 1.5

        # Economic status
        if agent.economic.get('income', 0) < 30000:
            base_impact *= 1.3

        # Political alignment
        political_factor = 1 - abs(agent.politics - news.source.politics)
        base_impact *= political_factor

        # Geographic proximity
        if agent.location == news.region:
            base_impact *= 2.0

        return base_impact

    def _apply_impact_to_agent(self, agent: Agent, impact: float):
        """Apply calculated impact to agent"""
        # Update economic stability
        agent.economic['financial_stability'] = max(0, min(1, agent.economic.get('financial_stability', 0.5) + (impact * 0.1)))

        # Update optimism
        agent.behavior['optimism'] = max(0, min(1, agent.behavior.get('optimism', 0.5) + (impact * 0.05)))

        # Update trust in institutions
        agent.behavior['trust_institutions'] = max(0, min(1, agent.behavior.get('trust_institutions', 0.5) + (impact * 0.02)))

    def _calculate_metrics(self) -> Dict[str, float]:
        """Calculate daily metrics"""
        economic_sentiment = float(np.mean([a.economic['financial_stability'] for a in self.agents]))
        social_cohesion = float(np.mean([a.behavior['trust_institutions'] for a in self.agents]))
        political_stability = float(1 - (np.std([a.politics for a in self.agents]) / 2))

        return {
            "economic_sentiment": economic_sentiment,
            "social_cohesion": social_cohesion,
            "political_stability": political_stability,
            "average_optimism": float(np.mean([a.behavior['optimism'] for a in self.agents]))
        }

    def _build_consensus(self) -> Dict[str, float]:
        """Build consensus across agents"""
        # Calculate average opinions on key topics
        consensus = {
            "economic_policy_support": float(np.mean([1 if a.politics > 0 else 0 for a in self.agents])),
            "government_trust": float(np.mean([a.behavior['trust_institutions'] for a in self.agents])),
            "future_optimism": float(np.mean([a.behavior['optimism'] for a in self.agents]))
        }
        return consensus

    def _get_agent_updates(self) -> List[Dict[str, Any]]:
        """Get updates for all agents"""
        return [{
            "id": a.id,
            "economic_stability": a.economic['financial_stability'],
            "optimism": a.behavior['optimism'],
            "trust_institutions": a.behavior['trust_institutions']
        } for a in self.agents]
