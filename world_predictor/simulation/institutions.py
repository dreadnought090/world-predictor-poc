"""Institution Agents — Governments, Central Banks, Corporations, Media.

Institutions are macro-level actors that enact policies affecting all citizen
agents in their country. Unlike citizen agents, institutions have deliberate
policy-setting behavior rather than reactive sentiment.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class InstitutionType(str, Enum):
    GOVERNMENT = "GOVERNMENT"
    CENTRAL_BANK = "CENTRAL_BANK"
    CORPORATION = "CORPORATION"
    MEDIA = "MEDIA"
    MILITARY = "MILITARY"


@dataclass
class Policy:
    """A policy enacted by an institution."""
    name: str
    category: str                # ECONOMIC_POLICY, SOCIAL, MILITARY, etc.
    impact_on_trust: float       # -1 to 1
    impact_on_optimism: float    # -1 to 1
    impact_on_economy: float     # -1 to 1
    impact_on_fear: float        # -1 to 1
    magnitude: float = 0.5      # 0 to 1 (how strong the effect)
    duration_days: int = 30      # how long effect persists
    _days_active: int = 0

    def is_active(self) -> bool:
        return self._days_active < self.duration_days

    def tick(self):
        self._days_active += 1

    @property
    def decay_factor(self) -> float:
        """Impact decays linearly over duration."""
        if self.duration_days <= 0:
            return 0
        return max(0, 1 - (self._days_active / self.duration_days))


@dataclass
class Institution:
    """An institution agent that affects citizen agents."""
    id: str
    name: str
    institution_type: str
    country: str
    politics: float = 0.0          # -1 to 1
    credibility: float = 0.5       # 0 to 1
    power: float = 0.5             # 0 to 1 (influence strength)
    active_policies: List[Policy] = field(default_factory=list)

    def enact_policy(self, policy: Policy):
        """Enact a new policy."""
        self.active_policies.append(policy)

    def get_aggregate_impact(self) -> Dict[str, float]:
        """Calculate combined impact of all active policies."""
        impact = {"trust": 0.0, "optimism": 0.0, "economy": 0.0, "fear": 0.0}
        for policy in self.active_policies:
            if not policy.is_active():
                continue
            decay = policy.decay_factor
            strength = policy.magnitude * self.power * decay
            impact["trust"] += policy.impact_on_trust * strength
            impact["optimism"] += policy.impact_on_optimism * strength
            impact["economy"] += policy.impact_on_economy * strength
            impact["fear"] += policy.impact_on_fear * strength
        return impact

    def tick(self):
        """Advance one day — decay policies."""
        for policy in self.active_policies:
            policy.tick()
        self.active_policies = [p for p in self.active_policies if p.is_active()]


# ---------------------------------------------------------------------------
# Default institutions per country
# ---------------------------------------------------------------------------

def create_default_institutions(country: str) -> List[Institution]:
    """Create default institutional actors for a country."""
    return [
        Institution(
            id=f"{country}_gov", name=f"{country} Government",
            institution_type=InstitutionType.GOVERNMENT, country=country,
            politics=_default_gov_politics(country),
            credibility=_default_gov_credibility(country),
            power=0.8,
        ),
        Institution(
            id=f"{country}_cb", name=f"{country} Central Bank",
            institution_type=InstitutionType.CENTRAL_BANK, country=country,
            politics=0.0,  # central banks are (theoretically) apolitical
            credibility=_default_cb_credibility(country),
            power=0.6,
        ),
        Institution(
            id=f"{country}_mil", name=f"{country} Military",
            institution_type=InstitutionType.MILITARY, country=country,
            politics=_default_mil_politics(country),
            credibility=0.6,
            power=0.5,
        ),
    ]


def _default_gov_politics(country: str) -> float:
    """Approximate current government political leaning."""
    leanings = {
        "US": 0.1, "CN": 0.4, "IN": 0.3, "BR": 0.2, "RU": 0.5,
        "JP": 0.2, "DE": 0.0, "GB": 0.1, "FR": 0.0, "KR": 0.1,
        "AU": 0.1, "MX": -0.1, "ID": 0.1, "NG": 0.0, "EG": 0.4,
        "SA": 0.5, "TR": 0.3, "PK": 0.2, "PH": 0.1, "TH": 0.2,
    }
    return leanings.get(country, 0.0)


def _default_gov_credibility(country: str) -> float:
    """Government credibility (rough approximation)."""
    creds = {
        "US": 0.55, "CN": 0.60, "IN": 0.50, "BR": 0.40, "RU": 0.45,
        "JP": 0.65, "DE": 0.70, "GB": 0.55, "FR": 0.50, "KR": 0.55,
        "AU": 0.60, "MX": 0.35, "ID": 0.45, "NG": 0.30, "EG": 0.40,
        "SA": 0.50, "TR": 0.40, "PK": 0.35, "PH": 0.40, "TH": 0.45,
    }
    return creds.get(country, 0.45)


def _default_cb_credibility(country: str) -> float:
    """Central bank credibility."""
    creds = {
        "US": 0.75, "CN": 0.65, "IN": 0.60, "BR": 0.55, "RU": 0.50,
        "JP": 0.70, "DE": 0.80, "GB": 0.75, "FR": 0.75, "KR": 0.70,
        "AU": 0.70, "MX": 0.55, "ID": 0.55, "NG": 0.40, "EG": 0.45,
        "SA": 0.60, "TR": 0.35, "PK": 0.40, "PH": 0.50, "TH": 0.55,
    }
    return creds.get(country, 0.50)


def _default_mil_politics(country: str) -> float:
    """Military political alignment (usually slightly right/authoritarian)."""
    return min(0.5, _default_gov_politics(country) + 0.1)


# ---------------------------------------------------------------------------
# Preset policies for quick injection
# ---------------------------------------------------------------------------

PRESET_POLICIES = {
    "rate_hike": Policy(
        name="Interest Rate Hike", category="ECONOMIC_POLICY",
        impact_on_trust=0.1, impact_on_optimism=-0.1,
        impact_on_economy=-0.15, impact_on_fear=0.05,
        magnitude=0.6, duration_days=30,
    ),
    "rate_cut": Policy(
        name="Interest Rate Cut", category="ECONOMIC_POLICY",
        impact_on_trust=0.05, impact_on_optimism=0.15,
        impact_on_economy=0.10, impact_on_fear=-0.05,
        magnitude=0.6, duration_days=30,
    ),
    "stimulus_package": Policy(
        name="Economic Stimulus Package", category="ECONOMIC_POLICY",
        impact_on_trust=0.15, impact_on_optimism=0.20,
        impact_on_economy=0.20, impact_on_fear=-0.10,
        magnitude=0.7, duration_days=60,
    ),
    "austerity": Policy(
        name="Austerity Measures", category="ECONOMIC_POLICY",
        impact_on_trust=-0.20, impact_on_optimism=-0.25,
        impact_on_economy=-0.10, impact_on_fear=0.15,
        magnitude=0.7, duration_days=90,
    ),
    "martial_law": Policy(
        name="Declaration of Martial Law", category="POLITICAL",
        impact_on_trust=-0.30, impact_on_optimism=-0.30,
        impact_on_economy=-0.15, impact_on_fear=0.40,
        magnitude=0.9, duration_days=30,
    ),
    "free_trade": Policy(
        name="Free Trade Agreement", category="TRADE",
        impact_on_trust=0.10, impact_on_optimism=0.10,
        impact_on_economy=0.15, impact_on_fear=-0.05,
        magnitude=0.5, duration_days=60,
    ),
    "censorship": Policy(
        name="Internet Censorship", category="SOCIAL",
        impact_on_trust=-0.25, impact_on_optimism=-0.15,
        impact_on_economy=-0.05, impact_on_fear=0.10,
        magnitude=0.6, duration_days=90,
    ),
    "healthcare_reform": Policy(
        name="Universal Healthcare Reform", category="HEALTH",
        impact_on_trust=0.15, impact_on_optimism=0.20,
        impact_on_economy=-0.05, impact_on_fear=-0.10,
        magnitude=0.6, duration_days=120,
    ),
}
