"""Scenario/What-If Engine.

Fork the current simulation state, inject hypothetical events or policies,
run N days, and compare outcomes against baseline. Supports multiple
concurrent scenario comparisons.
"""

import copy
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime

from world_predictor.data.agents import Agent
from world_predictor.data.news import NewsItem

logger = logging.getLogger(__name__)


@dataclass
class ScenarioResult:
    """Results from running a scenario."""
    scenario_id: str
    name: str
    description: str
    days_simulated: int
    daily_results: List[Dict[str, Any]]  # per-day, per-country metrics
    final_state: Dict[str, Any]          # final metrics per country
    events_injected: List[str]
    policies_injected: List[str]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class ScenarioEngine:
    """Run what-if scenarios by forking simulation state."""

    def __init__(self):
        self.results: Dict[str, ScenarioResult] = {}
        self._counter = 0

    def run_scenario(
        self,
        engine,  # SimulationEngine
        name: str,
        description: str,
        events: Optional[List] = None,
        policies: Optional[Dict[str, List]] = None,
        news_items: Optional[List[NewsItem]] = None,
        days: int = 30,
    ) -> ScenarioResult:
        """Fork engine state, inject events/policies, run N days.

        Args:
            engine: The main SimulationEngine to fork from
            name: Scenario name
            description: What we're testing
            events: List of GeoEvent objects to inject
            policies: Dict of {country: [Policy, ...]} to enact
            news_items: News items to feed each day (same items repeated)
            days: Number of days to simulate
        """
        from world_predictor.simulation.engine import CountryEngine, SimulationEngine
        from world_predictor.simulation.events import EventManager
        from world_predictor.simulation.institutions import Institution

        self._counter += 1
        scenario_id = f"scenario_{self._counter}"

        # Deep-copy all agents to create an isolated fork
        forked_engines: Dict[str, CountryEngine] = {}
        for country, ce in engine.engines.items():
            forked_agents = [
                Agent(
                    id=a.id,
                    demographics=dict(a.demographics),
                    economic=dict(a.economic),
                    behavior=dict(a.behavior),
                    location=a.location,
                    politics=float(a.politics),
                    iq=a.iq,
                )
                for a in ce.agents
            ]
            forked_ce = CountryEngine(country, forked_agents)
            forked_ce.current_day = ce.current_day
            forked_engines[country] = forked_ce

        # Create event manager for this scenario
        event_mgr = EventManager()
        event_names = []
        if events:
            start_day = next(iter(forked_engines.values())).current_day
            for event in events:
                event_copy = copy.deepcopy(event)
                event_mgr.inject_event(event_copy, start_day)
                event_names.append(event_copy.name)

        # Track policies injected
        policy_names = []
        if policies:
            for country, policy_list in policies.items():
                if country in forked_engines:
                    # We'll apply policy effects directly each day
                    for p in policy_list:
                        policy_names.append(f"{country}: {p.name}")

        # Run simulation for N days
        daily_results = []
        default_news = news_items or []

        for day_num in range(days):
            day_data = {}
            for country, ce in forked_engines.items():
                current_day = ce.current_day + 1

                # Apply event effects to agents
                effects = event_mgr.get_country_effects(country, current_day)
                if any(v != 0 for k, v in effects.items() if k != "news_amplifier"):
                    self._apply_event_effects(ce, effects)

                # Apply policy effects
                if policies and country in policies:
                    for policy in policies[country]:
                        if policy.is_active():
                            self._apply_policy_effects(ce, policy)
                            policy.tick()

                # Amplify news impact if events are active
                scenario_news = default_news
                if effects["news_amplifier"] > 1.0:
                    scenario_news = self._amplify_news(default_news, effects["news_amplifier"], country)

                # Run day
                country_news = [n for n in scenario_news if n.region == country or n.region == "Global"]
                result = ce.process_day(country_news)
                day_data[country] = {
                    "day": result["day"],
                    "metrics": result["metrics"],
                    "reactions": result["reactions"],
                }

            event_mgr.tick_all(next(iter(forked_engines.values())).current_day)
            daily_results.append(day_data)

        # Final state
        final_state = {}
        for country, ce in forked_engines.items():
            final_state[country] = ce._calculate_metrics()
            final_state[country]["revolution_risk"] = ce._calculate_revolution_risk(
                final_state[country], ce.reaction_history.get(ce.current_day, {})
            )

        result = ScenarioResult(
            scenario_id=scenario_id,
            name=name,
            description=description,
            days_simulated=days,
            daily_results=daily_results,
            final_state=final_state,
            events_injected=event_names,
            policies_injected=policy_names,
        )
        self.results[scenario_id] = result
        return result

    def compare_scenarios(self, baseline_id: str, scenario_id: str) -> Dict[str, Any]:
        """Compare two scenario results."""
        if baseline_id not in self.results or scenario_id not in self.results:
            return {"error": "Scenario not found"}

        baseline = self.results[baseline_id]
        scenario = self.results[scenario_id]

        comparison = {}
        for country in baseline.final_state:
            if country not in scenario.final_state:
                continue
            base_m = baseline.final_state[country]
            scen_m = scenario.final_state[country]
            comparison[country] = {
                metric: {
                    "baseline": round(base_m.get(metric, 0), 4),
                    "scenario": round(scen_m.get(metric, 0), 4),
                    "delta": round(scen_m.get(metric, 0) - base_m.get(metric, 0), 4),
                }
                for metric in base_m
            }
        return {
            "baseline": {"id": baseline_id, "name": baseline.name},
            "scenario": {"id": scenario_id, "name": scenario.name},
            "comparison": comparison,
        }

    def _apply_event_effects(self, ce, effects: Dict[str, float]):
        """Apply geopolitical event effects to all agents in a country engine."""
        for agent in ce.agents:
            agent.behavior["optimism"] = max(0, min(1,
                agent.behavior["optimism"] + effects["optimism_shift"] * 0.1))
            agent.behavior["trust_institutions"] = max(0, min(1,
                agent.behavior["trust_institutions"] + effects["trust_shift"] * 0.1))
            agent.behavior["risk_aversion"] = max(0, min(1,
                agent.behavior["risk_aversion"] + effects["fear_shift"] * 0.1))
            agent.economic["financial_stability"] = max(0, min(1,
                agent.economic["financial_stability"] + effects["economic_impact"] * 0.1))
            # Polarization: push agents further from center
            if effects["polarization_boost"] > 0:
                shift = effects["polarization_boost"] * 0.02 * (1 if agent.politics > 0 else -1)
                agent.politics = max(-1, min(1, agent.politics + shift))

    def _apply_policy_effects(self, ce, policy):
        """Apply a policy's effects to all agents."""
        decay = policy.decay_factor
        strength = policy.magnitude * decay * 0.05
        for agent in ce.agents:
            agent.behavior["trust_institutions"] = max(0, min(1,
                agent.behavior["trust_institutions"] + policy.impact_on_trust * strength))
            agent.behavior["optimism"] = max(0, min(1,
                agent.behavior["optimism"] + policy.impact_on_optimism * strength))
            agent.economic["financial_stability"] = max(0, min(1,
                agent.economic["financial_stability"] + policy.impact_on_economy * strength))
            agent.behavior["risk_aversion"] = max(0, min(1,
                agent.behavior["risk_aversion"] + policy.impact_on_fear * strength))

    def _amplify_news(self, news_items: List[NewsItem], amplifier: float, country: str) -> List[NewsItem]:
        """Create amplified copies of news items for a country under event effects."""
        from world_predictor.data.news import NewsItem as NI, NewsSource
        amplified = []
        for n in news_items:
            amp = NI(
                title=n.title, source=n.source, category=n.category,
                content=n.content, url=n.url, region=n.region,
                impact=min(1.0, n.impact * amplifier),
            )
            amplified.append(amp)
        return amplified
