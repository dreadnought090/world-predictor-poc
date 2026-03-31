"""Inter-Country Dynamics — Trade, Sanctions, Alliances, Migration.

Models relationships between countries that create spillover effects.
When one country's economy crashes, trade partners feel the impact.
Sanctions reduce economic sentiment. Alliances share security burdens.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple
from enum import Enum


class RelationType(str, Enum):
    TRADE = "TRADE"
    ALLIANCE = "ALLIANCE"
    RIVALRY = "RIVALRY"
    SANCTIONS = "SANCTIONS"


@dataclass
class CountryRelation:
    """A bilateral relationship between two countries."""
    country_a: str
    country_b: str
    relation_type: str
    strength: float  # 0 to 1

    def involves(self, country: str) -> bool:
        return country in (self.country_a, self.country_b)

    def partner(self, country: str) -> str:
        return self.country_b if country == self.country_a else self.country_a


# ---------------------------------------------------------------------------
# Default global relationships
# ---------------------------------------------------------------------------

DEFAULT_RELATIONS: List[CountryRelation] = [
    # Major trade relationships (strength = trade dependency)
    CountryRelation("US", "CN", RelationType.TRADE, 0.8),
    CountryRelation("US", "MX", RelationType.TRADE, 0.7),
    CountryRelation("US", "JP", RelationType.TRADE, 0.6),
    CountryRelation("US", "DE", RelationType.TRADE, 0.6),
    CountryRelation("US", "GB", RelationType.TRADE, 0.6),
    CountryRelation("US", "KR", RelationType.TRADE, 0.5),
    CountryRelation("CN", "JP", RelationType.TRADE, 0.6),
    CountryRelation("CN", "KR", RelationType.TRADE, 0.6),
    CountryRelation("CN", "AU", RelationType.TRADE, 0.5),
    CountryRelation("CN", "BR", RelationType.TRADE, 0.5),
    CountryRelation("CN", "DE", RelationType.TRADE, 0.5),
    CountryRelation("DE", "FR", RelationType.TRADE, 0.7),
    CountryRelation("DE", "GB", RelationType.TRADE, 0.5),
    CountryRelation("JP", "KR", RelationType.TRADE, 0.5),
    CountryRelation("IN", "SA", RelationType.TRADE, 0.5),
    CountryRelation("IN", "US", RelationType.TRADE, 0.4),
    CountryRelation("RU", "CN", RelationType.TRADE, 0.5),
    CountryRelation("RU", "IN", RelationType.TRADE, 0.4),
    CountryRelation("SA", "CN", RelationType.TRADE, 0.5),  # oil
    CountryRelation("ID", "CN", RelationType.TRADE, 0.5),
    CountryRelation("NG", "GB", RelationType.TRADE, 0.4),
    CountryRelation("TR", "DE", RelationType.TRADE, 0.5),

    # Alliances (strength = defense commitment)
    CountryRelation("US", "GB", RelationType.ALLIANCE, 0.9),   # special relationship
    CountryRelation("US", "JP", RelationType.ALLIANCE, 0.8),   # US-Japan security
    CountryRelation("US", "KR", RelationType.ALLIANCE, 0.8),
    CountryRelation("US", "AU", RelationType.ALLIANCE, 0.7),   # AUKUS/Five Eyes
    CountryRelation("US", "DE", RelationType.ALLIANCE, 0.7),   # NATO
    CountryRelation("US", "FR", RelationType.ALLIANCE, 0.7),   # NATO
    CountryRelation("US", "TR", RelationType.ALLIANCE, 0.5),   # NATO (strained)
    CountryRelation("DE", "FR", RelationType.ALLIANCE, 0.8),   # EU core
    CountryRelation("GB", "AU", RelationType.ALLIANCE, 0.7),   # Five Eyes
    CountryRelation("RU", "CN", RelationType.ALLIANCE, 0.5),   # strategic partnership
    CountryRelation("SA", "US", RelationType.ALLIANCE, 0.5),   # oil alliance

    # Rivalries (strength = tension level)
    CountryRelation("US", "CN", RelationType.RIVALRY, 0.6),
    CountryRelation("US", "RU", RelationType.RIVALRY, 0.7),
    CountryRelation("IN", "PK", RelationType.RIVALRY, 0.8),
    CountryRelation("IN", "CN", RelationType.RIVALRY, 0.5),
    CountryRelation("JP", "CN", RelationType.RIVALRY, 0.5),
    CountryRelation("KR", "CN", RelationType.RIVALRY, 0.3),
    CountryRelation("SA", "TR", RelationType.RIVALRY, 0.4),
    CountryRelation("EG", "TR", RelationType.RIVALRY, 0.4),
]


class InterCountryDynamics:
    """Calculate spillover effects between countries."""

    def __init__(self, relations: List[CountryRelation] = None):
        self.relations = relations or DEFAULT_RELATIONS

    def get_trade_partners(self, country: str) -> List[Tuple[str, float]]:
        """Get trade partners and their dependency strength."""
        return [
            (r.partner(country), r.strength)
            for r in self.relations
            if r.involves(country) and r.relation_type == RelationType.TRADE
        ]

    def get_allies(self, country: str) -> List[Tuple[str, float]]:
        return [
            (r.partner(country), r.strength)
            for r in self.relations
            if r.involves(country) and r.relation_type == RelationType.ALLIANCE
        ]

    def get_rivals(self, country: str) -> List[Tuple[str, float]]:
        return [
            (r.partner(country), r.strength)
            for r in self.relations
            if r.involves(country) and r.relation_type == RelationType.RIVALRY
        ]

    def calculate_spillover(
        self, source_country: str, source_metrics: Dict[str, float],
        all_metrics: Dict[str, Dict[str, float]],
    ) -> Dict[str, Dict[str, float]]:
        """Calculate economic/sentiment spillover from one country to others.

        Returns {country: {metric: delta}} for affected countries.
        """
        spillovers: Dict[str, Dict[str, float]] = {}

        source_econ = source_metrics.get("economic_sentiment", 0.5)
        source_stability = source_metrics.get("political_stability", 0.5)

        # Trade spillover: economic changes propagate to trade partners
        for partner, strength in self.get_trade_partners(source_country):
            econ_delta = (source_econ - 0.5) * strength * 0.1
            spillovers.setdefault(partner, {})
            spillovers[partner]["economic_sentiment"] = econ_delta

        # Alliance spillover: instability in ally → fear increase in partners
        for ally, strength in self.get_allies(source_country):
            if source_stability < 0.4:  # ally is unstable
                fear_delta = (0.5 - source_stability) * strength * 0.05
                spillovers.setdefault(ally, {})
                spillovers[ally]["fear_increase"] = fear_delta

        # Rivalry spillover: weakness in rival → optimism boost
        for rival, strength in self.get_rivals(source_country):
            if source_stability < 0.4:
                optimism_delta = (0.5 - source_stability) * strength * 0.03
                spillovers.setdefault(rival, {})
                spillovers[rival]["optimism_boost"] = optimism_delta

        return spillovers

    def get_country_network(self, country: str) -> Dict[str, List]:
        """Get full relationship network for a country."""
        return {
            "trade_partners": [{"country": c, "strength": s} for c, s in self.get_trade_partners(country)],
            "allies": [{"country": c, "strength": s} for c, s in self.get_allies(country)],
            "rivals": [{"country": c, "strength": s} for c, s in self.get_rivals(country)],
        }

    def add_sanction(self, country_a: str, country_b: str, strength: float = 0.7):
        """Add sanctions between two countries."""
        self.relations.append(CountryRelation(country_a, country_b, RelationType.SANCTIONS, strength))
        # Reduce trade relationship
        for r in self.relations:
            if (r.involves(country_a) and r.involves(country_b)
                    and r.relation_type == RelationType.TRADE):
                r.strength *= (1 - strength * 0.5)  # sanctions reduce trade

    def get_global_tension_index(self, all_metrics: Dict[str, Dict[str, float]]) -> float:
        """Calculate global tension index based on all rivalries and instabilities."""
        if not all_metrics:
            return 0.0
        tension = 0.0
        count = 0
        for r in self.relations:
            if r.relation_type == RelationType.RIVALRY:
                a_stab = all_metrics.get(r.country_a, {}).get("political_stability", 0.5)
                b_stab = all_metrics.get(r.country_b, {}).get("political_stability", 0.5)
                # Low stability + high rivalry = high tension
                pair_tension = r.strength * (1 - min(a_stab, b_stab))
                tension += pair_tension
                count += 1
        return tension / max(count, 1)
