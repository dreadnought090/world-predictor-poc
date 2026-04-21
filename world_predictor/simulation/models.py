import random
from dataclasses import dataclass, field
from typing import List, Dict, Any
from world_predictor.data.agents import Agent
from world_predictor.data.news import NewsItem


@dataclass
class SimulationState:
    agents: List[Agent]
    news_items: List[NewsItem]
    current_day: int
    parameters: Dict[str, float]
    # Track agent reactions per day: {day: {agent_id: reaction_type}}
    reaction_history: Dict[int, Dict[str, str]] = field(default_factory=dict)


class ReactionTypes:
    SUPPORT = "SUPPORT"
    OPPOSITION = "OPPOSITION"
    APATHY = "APATHY"
    CONFUSION = "CONFUSION"
    FEAR = "FEAR"

    ALL = [SUPPORT, OPPOSITION, APATHY, CONFUSION, FEAR]


class TrustModel:
    """Calculate how much an agent trusts a news source and determine reactions."""

    def calculate_trust(self, agent: Agent, news_source) -> float:
        """Calculate the level of trust an agent has in a specific news source.

        Combines political alignment, institutional trust, and source credibility.
        Returns 0.0 (no trust) to 1.0 (full trust).
        """
        # Political alignment: closer politics = higher trust
        alignment = 1 - abs(agent.politics - news_source.politics)

        # Agent's general trust in institutions (from behavior)
        institutional_trust = agent.behavior.get("trust_institutions", 0.5)

        # Source credibility (inherent quality of the outlet)
        credibility = news_source.credibility

        # IQ factor: higher IQ agents weigh credibility more, lower IQ agents
        # are more influenced by political alignment
        iq = agent.iq
        iq_factor = min(1.0, max(0.0, (iq - 70) / 60.0))  # 0.0 at IQ 70, 1.0 at IQ 130

        # Weighted combination — IQ shifts weight from alignment toward credibility
        alignment_weight = 0.35 - iq_factor * 0.10   # 0.35 -> 0.25
        trust_weight = 0.30
        credibility_weight = 0.35 + iq_factor * 0.10  # 0.35 -> 0.45

        trust = (
            alignment * alignment_weight
            + institutional_trust * trust_weight
            + credibility * credibility_weight
        )
        return max(0.0, min(1.0, trust))

    def determine_reaction(self, agent: Agent, news: NewsItem, trust_score: float) -> str:
        """Determine how an agent reacts to a news item based on trust and profile.

        Returns one of ReactionTypes: SUPPORT, OPPOSITION, APATHY, CONFUSION, FEAR.
        """
        impact = news.impact
        political_gap = abs(agent.politics - news.source.politics)
        iq = agent.iq
        risk_aversion = agent.behavior.get("risk_aversion", 0.5)
        optimism = agent.behavior.get("optimism", 0.5)

        # Base probabilities
        p_support = 0.2
        p_opposition = 0.2
        p_apathy = 0.2
        p_confusion = 0.2
        p_fear = 0.2

        # High trust + aligned politics -> more likely to support
        if trust_score > 0.6 and political_gap < 0.4:
            p_support += 0.3
            p_opposition -= 0.1

        # Low trust + misaligned politics -> opposition
        if trust_score < 0.4 and political_gap > 0.5:
            p_opposition += 0.3
            p_support -= 0.1

        # High impact + high risk aversion -> fear
        if impact > 0.6 and risk_aversion > 0.5:
            p_fear += 0.25
            p_apathy -= 0.1

        # Low impact -> apathy
        if impact < 0.3:
            p_apathy += 0.3
            p_fear -= 0.1
            p_support -= 0.1

        # Lower IQ + high impact + low trust -> confusion
        if iq < 90 and impact > 0.5 and trust_score < 0.5:
            p_confusion += 0.2

        # Higher IQ -> less confusion, more decisive (support or opposition)
        if iq > 110:
            p_confusion -= 0.1
            if optimism > 0.5:
                p_support += 0.1
            else:
                p_opposition += 0.1

        # Optimistic agents less fearful
        if optimism > 0.7:
            p_fear -= 0.1
            p_support += 0.1

        # Clamp and normalize
        probs = [max(0.01, p) for p in [p_support, p_opposition, p_apathy, p_confusion, p_fear]]
        total = sum(probs)
        probs = [p / total for p in probs]

        return random.choices(ReactionTypes.ALL, weights=probs, k=1)[0]
