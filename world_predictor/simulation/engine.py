"""World Predictor Simulation Engine.

Manages multi-country agent simulation with:
- News impact processing via TrustModel
- Agent reaction system (Support/Opposition/Fear/Confusion/Apathy)
- Opinion diffusion (Bounded Confidence Model)
- Memory decay (agents revert toward baseline)
- Revolution Risk Index
- Persistence via SQLite
"""

import random
import logging
from typing import List, Dict, Any, Optional
from collections import Counter

import numpy as np

from world_predictor.data.agents import Agent, AgentGenerator
from world_predictor.data.news import NewsItem
from world_predictor.simulation.models import SimulationState, TrustModel, ReactionTypes
from world_predictor.simulation.events import EventManager, GeoEvent
from world_predictor.simulation.institutions import Institution, create_default_institutions
from world_predictor.simulation.intercountry import InterCountryDynamics
from world_predictor.config import sim_config

logger = logging.getLogger(__name__)


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


class CountryEngine:
    """Simulation engine for a single country's agents."""

    def __init__(self, country_code: str, agents: List[Agent]):
        self.country_code = country_code
        self.agents = agents
        self.trust_model = TrustModel()
        self.current_day = 0
        self.reaction_history: Dict[int, Dict[str, str]] = {}
        self._baseline_optimism = np.mean([a.behavior["optimism"] for a in agents])
        self._baseline_trust = np.mean([a.behavior["trust_institutions"] for a in agents])

    def process_day(self, news_items: List[NewsItem]) -> Dict[str, Any]:
        """Process a single day: news reactions + opinion diffusion + decay."""
        self.current_day += 1
        cfg = sim_config()

        # 1. Process news reactions
        day_reactions = self._process_reactions(news_items)
        self.reaction_history[self.current_day] = day_reactions

        # 2. Opinion diffusion (agent-agent interaction)
        if cfg.get("opinion_diffusion", {}).get("enabled", True):
            self._opinion_diffusion()

        # 3. Memory decay (revert toward baseline)
        if cfg.get("memory_decay", {}).get("enabled", True):
            self._apply_memory_decay()

        # 4. Calculate metrics
        metrics = self._calculate_metrics()

        # 5. Revolution risk
        metrics["revolution_risk"] = self._calculate_revolution_risk(metrics, day_reactions)

        # 6. Build consensus
        consensus = self._build_consensus(day_reactions)

        # 7. Reaction summary
        reaction_summary = self._summarize_reactions(day_reactions)

        return {
            "country": self.country_code,
            "day": self.current_day,
            "metrics": metrics,
            "consensus": consensus,
            "reactions": reaction_summary,
            "agent_count": len(self.agents),
        }

    # ---- News Processing ----

    def _process_reactions(self, news_items: List[NewsItem]) -> Dict[str, str]:
        """Process agent reactions to news items."""
        agent_reactions: Dict[str, List[str]] = {}

        for news in news_items:
            for agent in self.agents:
                trust = self.trust_model.calculate_trust(agent, news.source)
                reaction = self.trust_model.determine_reaction(agent, news, trust)
                agent_reactions.setdefault(agent.id, []).append(reaction)
                self._apply_reaction_impact(agent, news, trust, reaction)

        # Dominant reaction per agent
        dominant: Dict[str, str] = {}
        for agent_id, reactions in agent_reactions.items():
            counts = Counter(reactions)
            dominant[agent_id] = counts.most_common(1)[0][0]
        return dominant

    def _apply_reaction_impact(self, agent: Agent, news: NewsItem, trust: float, reaction: str):
        """Apply behavioral changes based on reaction."""
        base_impact = news.impact * trust

        if reaction == ReactionTypes.SUPPORT:
            agent.behavior["optimism"] = _clamp(agent.behavior["optimism"] + base_impact * 0.05)
            agent.behavior["trust_institutions"] = _clamp(agent.behavior["trust_institutions"] + base_impact * 0.03)
            agent.economic["financial_stability"] = _clamp(agent.economic["financial_stability"] + base_impact * 0.02)
        elif reaction == ReactionTypes.OPPOSITION:
            agent.behavior["optimism"] = _clamp(agent.behavior["optimism"] - base_impact * 0.04)
            agent.behavior["trust_institutions"] = _clamp(agent.behavior["trust_institutions"] - base_impact * 0.05)
            shift = 0.02 * base_impact * (1 if agent.politics > 0 else -1)
            agent.politics = _clamp(agent.politics + shift, -1.0, 1.0)
        elif reaction == ReactionTypes.FEAR:
            agent.behavior["optimism"] = _clamp(agent.behavior["optimism"] - base_impact * 0.06)
            agent.behavior["risk_aversion"] = _clamp(agent.behavior["risk_aversion"] + base_impact * 0.04)
            agent.economic["financial_stability"] = _clamp(agent.economic["financial_stability"] - base_impact * 0.03)
        elif reaction == ReactionTypes.CONFUSION:
            agent.behavior["trust_institutions"] = _clamp(agent.behavior["trust_institutions"] - base_impact * 0.03)
            agent.behavior["optimism"] = _clamp(agent.behavior["optimism"] - base_impact * 0.02)

    # ---- Opinion Diffusion (Bounded Confidence Model) ----

    def _opinion_diffusion(self):
        """Agents interact with similar agents, pulling opinions closer.

        Bounded Confidence: agents only listen to others within a confidence bound.
        Creates emergent echo chambers and polarization clusters.
        """
        cfg = sim_config().get("opinion_diffusion", {})
        n_interactions = cfg.get("interactions_per_day", 5)
        confidence_bound = cfg.get("confidence_bound", 0.4)
        shift_rate = cfg.get("shift_rate", 0.05)

        for agent in self.agents:
            peers = random.sample(self.agents, min(n_interactions * 3, len(self.agents)))
            interactions = 0

            for peer in peers:
                if interactions >= n_interactions:
                    break
                if peer.id == agent.id:
                    continue

                # Check if within confidence bound (political proximity)
                political_distance = abs(agent.politics - peer.politics)
                if political_distance > confidence_bound:
                    continue

                interactions += 1

                # IQ + education similarity modulates influence strength
                iq_a = int(agent.demographics.get("iq", "100"))
                iq_p = int(peer.demographics.get("iq", "100"))
                iq_similarity = 1 - abs(iq_a - iq_p) / 60.0
                influence = shift_rate * max(0.2, iq_similarity)

                # Pull opinions toward each other
                agent.behavior["optimism"] = _clamp(
                    agent.behavior["optimism"] + influence * (peer.behavior["optimism"] - agent.behavior["optimism"])
                )
                agent.behavior["trust_institutions"] = _clamp(
                    agent.behavior["trust_institutions"] + influence * (peer.behavior["trust_institutions"] - agent.behavior["trust_institutions"])
                )
                agent.politics = _clamp(
                    agent.politics + influence * (peer.politics - agent.politics), -1.0, 1.0
                )

    # ---- Memory Decay ----

    def _apply_memory_decay(self):
        """Agents gradually revert toward baseline (mean reversion)."""
        cfg = sim_config().get("memory_decay", {})
        opt_decay = cfg.get("optimism_decay", 0.02)
        trust_decay = cfg.get("trust_decay", 0.01)
        fear_decay = cfg.get("fear_decay", 0.03)

        for agent in self.agents:
            # Optimism reverts toward population baseline
            agent.behavior["optimism"] = _clamp(
                agent.behavior["optimism"] + opt_decay * (self._baseline_optimism - agent.behavior["optimism"])
            )
            # Trust reverts
            agent.behavior["trust_institutions"] = _clamp(
                agent.behavior["trust_institutions"] + trust_decay * (self._baseline_trust - agent.behavior["trust_institutions"])
            )
            # Risk aversion decays toward 0.5 (neutral)
            agent.behavior["risk_aversion"] = _clamp(
                agent.behavior["risk_aversion"] + fear_decay * (0.5 - agent.behavior["risk_aversion"])
            )

    # ---- Revolution Risk Index ----

    def _calculate_revolution_risk(self, metrics: Dict, reactions: Dict[str, str]) -> float:
        """Composite revolution risk score (0.0 = stable, 1.0 = imminent revolution).

        Factors: low trust, high fear, high opposition, political polarization.
        """
        cfg = sim_config().get("revolution_risk", {})
        w_trust = cfg.get("trust_weight", 0.3)
        w_fear = cfg.get("fear_weight", 0.25)
        w_opposition = cfg.get("opposition_weight", 0.25)
        w_polarization = cfg.get("polarization_weight", 0.2)

        # Low trust = high risk
        trust_risk = 1 - metrics.get("social_cohesion", 0.5)

        # Fear proportion
        if reactions:
            counts = Counter(reactions.values())
            total = len(reactions)
            fear_risk = counts.get(ReactionTypes.FEAR, 0) / max(total, 1)
            opposition_risk = counts.get(ReactionTypes.OPPOSITION, 0) / max(total, 1)
        else:
            fear_risk = 0.0
            opposition_risk = 0.0

        # Political polarization (high std = polarized)
        polarization = float(np.std([a.politics for a in self.agents]))
        polarization_risk = min(1.0, polarization / 0.5)  # normalized

        risk = (
            w_trust * trust_risk
            + w_fear * fear_risk
            + w_opposition * opposition_risk
            + w_polarization * polarization_risk
        )
        return round(_clamp(risk), 4)

    # ---- Metrics ----

    def _calculate_metrics(self) -> Dict[str, float]:
        economic_sentiment = float(np.mean([a.economic["financial_stability"] for a in self.agents]))
        social_cohesion = float(np.mean([a.behavior["trust_institutions"] for a in self.agents]))
        political_stability = float(1 - (np.std([a.politics for a in self.agents]) / 2))
        avg_optimism = float(np.mean([a.behavior["optimism"] for a in self.agents]))
        avg_risk_aversion = float(np.mean([a.behavior["risk_aversion"] for a in self.agents]))

        return {
            "economic_sentiment": round(economic_sentiment, 4),
            "social_cohesion": round(social_cohesion, 4),
            "political_stability": round(political_stability, 4),
            "average_optimism": round(avg_optimism, 4),
            "average_risk_aversion": round(avg_risk_aversion, 4),
        }

    def _build_consensus(self, day_reactions: Dict[str, str]) -> Dict[str, Any]:
        consensus: Dict[str, Any] = {
            "economic_policy_support": float(np.mean([1 if a.politics > 0 else 0 for a in self.agents])),
            "government_trust": float(np.mean([a.behavior["trust_institutions"] for a in self.agents])),
            "future_optimism": float(np.mean([a.behavior["optimism"] for a in self.agents])),
        }
        if day_reactions:
            counts = Counter(day_reactions.values())
            total = len(day_reactions)
            consensus["reaction_distribution"] = {
                r: round(counts.get(r, 0) / total, 4) for r in ReactionTypes.ALL
            }
        return consensus

    def _summarize_reactions(self, day_reactions: Dict[str, str]) -> Dict[str, Any]:
        if not day_reactions:
            return {"total_agents": 0, "distribution": {r: 0 for r in ReactionTypes.ALL},
                    "percentages": {r: 0.0 for r in ReactionTypes.ALL}, "dominant": "APATHY"}
        counts = Counter(day_reactions.values())
        total = len(day_reactions)
        return {
            "total_agents": total,
            "distribution": {r: counts.get(r, 0) for r in ReactionTypes.ALL},
            "percentages": {r: round(counts.get(r, 0) / total * 100, 1) for r in ReactionTypes.ALL},
            "dominant": counts.most_common(1)[0][0],
        }

    def get_agent_updates(self, limit: int = 500) -> List[Dict[str, Any]]:
        """Get agent state updates (capped for API response size)."""
        return [
            {
                "id": a.id,
                "economic_stability": a.economic["financial_stability"],
                "optimism": a.behavior["optimism"],
                "trust_institutions": a.behavior["trust_institutions"],
            }
            for a in self.agents[:limit]
        ]


# ---------------------------------------------------------------------------
# Global Simulation Engine — orchestrates all countries
# ---------------------------------------------------------------------------

class SimulationEngine:
    """Multi-country simulation orchestrator with events, institutions, and inter-country dynamics."""

    def __init__(self, agents: Optional[List[Agent]] = None, db=None):
        self.engines: Dict[str, CountryEngine] = {}
        self.db = db
        self._generator = AgentGenerator()
        self.event_manager = EventManager()
        self.inter_country = InterCountryDynamics()
        self.institutions: Dict[str, List[Institution]] = {}
        self.scenario_engine = None  # lazy init
        cfg = sim_config()

        if agents:
            # Legacy: single-country mode (backward compatible)
            country = agents[0].location if agents else "US"
            self.engines[country] = CountryEngine(country, agents)
            self.institutions[country] = create_default_institutions(country)
        else:
            # Multi-country: generate agents for all configured countries
            for country in cfg.get("countries", ["US"]):
                count = cfg.get("agents_per_country", 1000)
                country_agents = self._generator.generate_agents_for_country(country, count)
                self.engines[country] = CountryEngine(country, country_agents)
                self.institutions[country] = create_default_institutions(country)
                logger.info("Initialized %d agents for %s", count, country)

    @property
    def state(self):
        """Backward-compatible state accessor (returns first country's state)."""
        if not self.engines:
            return SimulationState(agents=[], news_items=[], current_day=0, parameters={})
        first = next(iter(self.engines.values()))
        return SimulationState(
            agents=first.agents,
            news_items=[],
            current_day=first.current_day,
            parameters=sim_config().get("impact_weights", {}),
        )

    @property
    def agents(self):
        """Backward-compatible: return first country's agents."""
        if not self.engines:
            return []
        return next(iter(self.engines.values())).agents

    @property
    def countries(self) -> List[str]:
        return list(self.engines.keys())

    def process_day(self, news_items: List[NewsItem]) -> Dict[str, Any]:
        """Process a day for all countries with events, institutions, and spillover."""
        results: Dict[str, Any] = {}

        for country, engine in self.engines.items():
            current_day = engine.current_day + 1

            # 1. Apply geopolitical event effects before news processing
            event_effects = self.event_manager.get_country_effects(country, current_day)
            if any(v != 0 for k, v in event_effects.items() if k != "news_amplifier"):
                self._apply_event_effects(engine, event_effects)

            # 2. Apply institution policy effects
            if country in self.institutions:
                for inst in self.institutions[country]:
                    impact = inst.get_aggregate_impact()
                    if any(v != 0 for v in impact.values()):
                        self._apply_institution_impact(engine, impact)
                    inst.tick()

            # 3. Filter and optionally amplify news
            country_news = [n for n in news_items if n.region == country or n.region == "Global"]
            if event_effects["news_amplifier"] > 1.0:
                country_news = self._amplify_news(country_news, event_effects["news_amplifier"])

            # 4. Run country simulation
            result = engine.process_day(country_news)
            results[country] = result

            # 5. Persist to database
            if self.db:
                self.db.save_daily_metrics(
                    country, result["day"], result["metrics"],
                    result["reactions"], result["consensus"],
                )

        # 6. Inter-country spillover effects
        all_metrics = {c: r["metrics"] for c, r in results.items()}
        for country in self.engines:
            for source_country, source_metrics in all_metrics.items():
                if source_country == country:
                    continue
                spillovers = self.inter_country.calculate_spillover(
                    source_country, source_metrics, all_metrics
                )
                if country in spillovers:
                    self._apply_spillover(self.engines[country], spillovers[country])

        # 7. Tick events
        if self.engines:
            current = next(iter(self.engines.values())).current_day
            self.event_manager.tick_all(current)

        # 8. Add global tension to results
        global_tension = self.inter_country.get_global_tension_index(all_metrics)
        for r in results.values():
            r["metrics"]["global_tension"] = round(global_tension, 4)

        # Archive news
        if self.db and news_items:
            self.db.save_news_items(news_items)

        return results

    def inject_event(self, event: GeoEvent):
        """Inject a geopolitical event into the simulation."""
        current_day = next(iter(self.engines.values())).current_day if self.engines else 0
        self.event_manager.inject_event(event, current_day)

    def enact_policy(self, country: str, policy):
        """Enact a policy via a country's institution."""
        if country in self.institutions:
            for inst in self.institutions[country]:
                if inst.institution_type == "GOVERNMENT":
                    inst.enact_policy(policy)
                    return
        logger.warning("No government institution for %s", country)

    def _apply_event_effects(self, engine: CountryEngine, effects: Dict[str, float]):
        """Apply event effects to all agents."""
        for agent in engine.agents:
            agent.behavior["optimism"] = _clamp(agent.behavior["optimism"] + effects["optimism_shift"] * 0.1)
            agent.behavior["trust_institutions"] = _clamp(agent.behavior["trust_institutions"] + effects["trust_shift"] * 0.1)
            agent.behavior["risk_aversion"] = _clamp(agent.behavior["risk_aversion"] + effects["fear_shift"] * 0.1)
            agent.economic["financial_stability"] = _clamp(agent.economic["financial_stability"] + effects["economic_impact"] * 0.1)
            if effects["polarization_boost"] != 0:
                shift = effects["polarization_boost"] * 0.02 * (1 if agent.politics > 0 else -1)
                agent.politics = _clamp(agent.politics + shift, -1.0, 1.0)

    def _apply_institution_impact(self, engine: CountryEngine, impact: Dict[str, float]):
        """Apply institution policy impacts to agents."""
        for agent in engine.agents:
            agent.behavior["trust_institutions"] = _clamp(agent.behavior["trust_institutions"] + impact["trust"] * 0.05)
            agent.behavior["optimism"] = _clamp(agent.behavior["optimism"] + impact["optimism"] * 0.05)
            agent.economic["financial_stability"] = _clamp(agent.economic["financial_stability"] + impact["economy"] * 0.05)
            agent.behavior["risk_aversion"] = _clamp(agent.behavior["risk_aversion"] + impact["fear"] * 0.05)

    def _apply_spillover(self, engine: CountryEngine, spillover: Dict[str, float]):
        """Apply inter-country spillover effects."""
        for agent in engine.agents:
            if "economic_sentiment" in spillover:
                agent.economic["financial_stability"] = _clamp(
                    agent.economic["financial_stability"] + spillover["economic_sentiment"])
            if "fear_increase" in spillover:
                agent.behavior["risk_aversion"] = _clamp(
                    agent.behavior["risk_aversion"] + spillover["fear_increase"])
            if "optimism_boost" in spillover:
                agent.behavior["optimism"] = _clamp(
                    agent.behavior["optimism"] + spillover["optimism_boost"])

    def _amplify_news(self, news_items: List[NewsItem], amplifier: float) -> List[NewsItem]:
        """Create amplified copies of news items."""
        from world_predictor.data.news import NewsItem as NI
        return [
            NI(title=n.title, source=n.source, category=n.category,
               content=n.content, url=n.url, region=n.region,
               impact=min(1.0, n.impact * amplifier))
            for n in news_items
        ]

    def process_day_single(self, country: str, news_items: List[NewsItem]) -> Dict[str, Any]:
        """Process a day for a single country."""
        if country not in self.engines:
            raise ValueError(f"Country {country} not loaded")
        result = self.engines[country].process_day(news_items)
        if self.db:
            self.db.save_daily_metrics(
                country, result["day"], result["metrics"],
                result["reactions"], result["consensus"],
            )
        return result

    def get_predictions(self, country: str) -> Dict[str, Any]:
        """Get current predictions for a country (real metrics, not dummy)."""
        if country not in self.engines:
            return {"error": f"Country {country} not loaded"}
        engine = self.engines[country]
        metrics = engine._calculate_metrics()
        risk = engine._calculate_revolution_risk(metrics, engine.reaction_history.get(engine.current_day, {}))
        metrics["revolution_risk"] = risk
        return {
            "country": country,
            "day": engine.current_day,
            "agent_count": len(engine.agents),
            "metrics": metrics,
        }

    def get_all_predictions(self) -> Dict[str, Any]:
        """Get predictions for all countries."""
        predictions = {}
        for country in self.engines:
            predictions[country] = self.get_predictions(country)
        return predictions

    def simulate_batch(self, news_items: List[NewsItem], days: int = 10) -> List[Dict[str, Any]]:
        """Run multiple days of simulation."""
        results = []
        for _ in range(days):
            result = self.process_day(news_items)
            results.append(result)
        return results
