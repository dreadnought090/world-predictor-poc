"""Geopolitical Event System.

Models shock events (wars, elections, coups, pandemics, etc.) that dramatically
shift agent behavior beyond normal news impact. Events have magnitude, duration,
decay, and affect specific countries and news categories.
"""

import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class EventType(str, Enum):
    ELECTION = "ELECTION"
    COUP = "COUP"
    WAR = "WAR"
    CIVIL_UNREST = "CIVIL_UNREST"
    PANDEMIC = "PANDEMIC"
    NATURAL_DISASTER = "NATURAL_DISASTER"
    SANCTIONS = "SANCTIONS"
    TRADE_WAR = "TRADE_WAR"
    ECONOMIC_CRISIS = "ECONOMIC_CRISIS"
    TERROR_ATTACK = "TERROR_ATTACK"
    PEACE_DEAL = "PEACE_DEAL"
    TECH_BREAKTHROUGH = "TECH_BREAKTHROUGH"


# How each event type affects agent behavior
EVENT_IMPACT_PROFILES: Dict[str, Dict[str, float]] = {
    EventType.ELECTION: {
        "optimism_shift": 0.0,       # neutral (depends on who wins)
        "trust_shift": -0.05,        # slight distrust during elections
        "fear_shift": 0.02,
        "polarization_boost": 0.15,  # elections polarize
        "economic_impact": -0.02,
        "news_amplifier": 1.5,
    },
    EventType.COUP: {
        "optimism_shift": -0.20,
        "trust_shift": -0.30,
        "fear_shift": 0.25,
        "polarization_boost": 0.30,
        "economic_impact": -0.15,
        "news_amplifier": 3.0,
    },
    EventType.WAR: {
        "optimism_shift": -0.25,
        "trust_shift": -0.10,
        "fear_shift": 0.35,
        "polarization_boost": 0.10,
        "economic_impact": -0.20,
        "news_amplifier": 3.5,
    },
    EventType.CIVIL_UNREST: {
        "optimism_shift": -0.15,
        "trust_shift": -0.20,
        "fear_shift": 0.15,
        "polarization_boost": 0.20,
        "economic_impact": -0.08,
        "news_amplifier": 2.0,
    },
    EventType.PANDEMIC: {
        "optimism_shift": -0.15,
        "trust_shift": -0.05,
        "fear_shift": 0.30,
        "polarization_boost": 0.10,
        "economic_impact": -0.15,
        "news_amplifier": 2.5,
    },
    EventType.NATURAL_DISASTER: {
        "optimism_shift": -0.10,
        "trust_shift": 0.05,         # rallying effect
        "fear_shift": 0.20,
        "polarization_boost": -0.05,  # unifying
        "economic_impact": -0.10,
        "news_amplifier": 2.0,
    },
    EventType.SANCTIONS: {
        "optimism_shift": -0.10,
        "trust_shift": -0.05,
        "fear_shift": 0.05,
        "polarization_boost": 0.10,
        "economic_impact": -0.12,
        "news_amplifier": 1.5,
    },
    EventType.TRADE_WAR: {
        "optimism_shift": -0.08,
        "trust_shift": -0.03,
        "fear_shift": 0.05,
        "polarization_boost": 0.08,
        "economic_impact": -0.10,
        "news_amplifier": 1.3,
    },
    EventType.ECONOMIC_CRISIS: {
        "optimism_shift": -0.25,
        "trust_shift": -0.20,
        "fear_shift": 0.20,
        "polarization_boost": 0.15,
        "economic_impact": -0.30,
        "news_amplifier": 2.5,
    },
    EventType.TERROR_ATTACK: {
        "optimism_shift": -0.15,
        "trust_shift": -0.10,
        "fear_shift": 0.35,
        "polarization_boost": 0.15,
        "economic_impact": -0.05,
        "news_amplifier": 3.0,
    },
    EventType.PEACE_DEAL: {
        "optimism_shift": 0.20,
        "trust_shift": 0.15,
        "fear_shift": -0.15,
        "polarization_boost": -0.10,
        "economic_impact": 0.10,
        "news_amplifier": 1.5,
    },
    EventType.TECH_BREAKTHROUGH: {
        "optimism_shift": 0.15,
        "trust_shift": 0.05,
        "fear_shift": -0.05,
        "polarization_boost": 0.0,
        "economic_impact": 0.08,
        "news_amplifier": 1.3,
    },
}


@dataclass
class GeoEvent:
    """A geopolitical shock event."""
    event_type: str
    name: str
    affected_countries: List[str]
    magnitude: float = 1.0              # 0.1 (minor) to 1.0 (catastrophic)
    duration_days: int = 7              # how many days the event persists
    start_day: int = 0                  # simulation day when event starts
    decay_rate: float = 0.85            # daily magnitude decay
    secondary_countries: List[str] = field(default_factory=list)  # spillover
    secondary_magnitude: float = 0.3    # magnitude for secondary countries
    _current_magnitude: float = 0.0

    def __post_init__(self):
        self._current_magnitude = self.magnitude

    @property
    def profile(self) -> Dict[str, float]:
        """Get the impact profile for this event type."""
        return EVENT_IMPACT_PROFILES.get(self.event_type, EVENT_IMPACT_PROFILES[EventType.CIVIL_UNREST])

    def is_active(self, current_day: int) -> bool:
        """Check if event is still active."""
        return (current_day >= self.start_day and
                current_day < self.start_day + self.duration_days and
                self._current_magnitude > 0.01)

    def get_magnitude(self, country: str, current_day: int) -> float:
        """Get current magnitude for a country, accounting for decay."""
        if not self.is_active(current_day):
            return 0.0
        days_elapsed = current_day - self.start_day
        decayed = self.magnitude * (self.decay_rate ** days_elapsed)
        if country in self.affected_countries:
            return decayed
        elif country in self.secondary_countries:
            return decayed * self.secondary_magnitude
        return 0.0

    def tick(self):
        """Advance one day of decay."""
        self._current_magnitude *= self.decay_rate


class EventManager:
    """Manages active geopolitical events and their impact on the simulation."""

    def __init__(self):
        self.active_events: List[GeoEvent] = []
        self.event_history: List[GeoEvent] = []

    def inject_event(self, event: GeoEvent, current_day: int):
        """Inject a new event into the simulation."""
        event.start_day = current_day
        event._current_magnitude = event.magnitude
        self.active_events.append(event)
        self.event_history.append(event)

    def get_country_effects(self, country: str, current_day: int) -> Dict[str, float]:
        """Aggregate all active event effects for a country.

        Returns combined shifts for optimism, trust, fear, polarization, economic, news_amplifier.
        """
        combined = {
            "optimism_shift": 0.0,
            "trust_shift": 0.0,
            "fear_shift": 0.0,
            "polarization_boost": 0.0,
            "economic_impact": 0.0,
            "news_amplifier": 1.0,
        }

        for event in self.active_events:
            mag = event.get_magnitude(country, current_day)
            if mag <= 0:
                continue
            profile = event.profile
            combined["optimism_shift"] += profile["optimism_shift"] * mag
            combined["trust_shift"] += profile["trust_shift"] * mag
            combined["fear_shift"] += profile["fear_shift"] * mag
            combined["polarization_boost"] += profile["polarization_boost"] * mag
            combined["economic_impact"] += profile["economic_impact"] * mag
            combined["news_amplifier"] = max(combined["news_amplifier"], profile["news_amplifier"] * mag)

        return combined

    def tick_all(self, current_day: int):
        """Advance all events and remove expired ones."""
        for event in self.active_events:
            event.tick()
        self.active_events = [e for e in self.active_events if e.is_active(current_day)]

    def get_active_events(self, current_day: int) -> List[Dict]:
        """Get summary of active events."""
        return [
            {
                "name": e.name,
                "type": e.event_type,
                "affected": e.affected_countries,
                "magnitude": round(e.get_magnitude(e.affected_countries[0], current_day), 3) if e.affected_countries else 0,
                "days_remaining": max(0, (e.start_day + e.duration_days) - current_day),
            }
            for e in self.active_events if e.is_active(current_day)
        ]


# ---------------------------------------------------------------------------
# Preset events for quick injection
# ---------------------------------------------------------------------------

PRESET_EVENTS = {
    "us_election": GeoEvent(
        event_type=EventType.ELECTION, name="US Presidential Election",
        affected_countries=["US"], secondary_countries=["GB", "DE", "JP", "CN"],
        magnitude=0.8, duration_days=30, decay_rate=0.92,
    ),
    "ukraine_war": GeoEvent(
        event_type=EventType.WAR, name="Major Armed Conflict in Eastern Europe",
        affected_countries=["RU"], secondary_countries=["DE", "GB", "FR", "US", "CN"],
        magnitude=0.9, duration_days=90, decay_rate=0.98,
    ),
    "pandemic_outbreak": GeoEvent(
        event_type=EventType.PANDEMIC, name="Global Pandemic Outbreak",
        affected_countries=["CN", "US", "IN", "BR", "GB", "DE", "FR"],
        secondary_countries=["JP", "KR", "AU", "ID", "NG", "MX"],
        magnitude=0.85, duration_days=180, decay_rate=0.995,
    ),
    "financial_crash": GeoEvent(
        event_type=EventType.ECONOMIC_CRISIS, name="Global Financial Crisis",
        affected_countries=["US", "GB", "DE", "JP", "CN"],
        secondary_countries=["BR", "IN", "KR", "AU", "MX", "TR"],
        magnitude=0.9, duration_days=60, decay_rate=0.95,
    ),
    "middle_east_peace": GeoEvent(
        event_type=EventType.PEACE_DEAL, name="Middle East Peace Agreement",
        affected_countries=["SA", "EG", "TR"],
        secondary_countries=["US", "GB", "FR"],
        magnitude=0.7, duration_days=14, decay_rate=0.90,
    ),
    "ai_breakthrough": GeoEvent(
        event_type=EventType.TECH_BREAKTHROUGH, name="Major AI Breakthrough",
        affected_countries=["US", "CN", "GB"],
        secondary_countries=["JP", "KR", "DE", "IN", "FR"],
        magnitude=0.6, duration_days=21, decay_rate=0.88,
    ),
}
