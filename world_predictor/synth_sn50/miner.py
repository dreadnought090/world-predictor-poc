"""SynthSN50Miner — Black-box miner implementation for UID100 on SYNTH SN50.

UID100 in this context means the miner agent operates with IQ=100 (median),
which sets specific weights inside the TrustModel used for HIGH asset prediction.

This module acts as the "black box" we want to reverse engineer. It receives
structured prompts (news events) and emits HIGH / NEUTRAL / LOW asset signals.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np


# ---------------------------------------------------------------------------
# Prompt & Output types
# ---------------------------------------------------------------------------

NEWS_CATEGORIES = [
    "economy", "politics", "military", "social",
    "technology", "environment", "health", "diplomacy", "crisis",
]


@dataclass
class MinerPrompt:
    """A single prediction prompt sent to the miner.

    Mirrors the fields the SN50 validator passes per-tick.
    """
    category: str          # one of NEWS_CATEGORIES
    impact: float          # 0.0 (low) → 1.0 (high)
    source_credibility: float  # 0.0 → 1.0
    source_politics: float     # -1.0 (far-left) → +1.0 (far-right)
    region: str            # ISO-2 country code, e.g. "US"
    headline: str = ""     # optional text label

    def __post_init__(self):
        self.impact = float(np.clip(self.impact, 0.0, 1.0))
        self.source_credibility = float(np.clip(self.source_credibility, 0.0, 1.0))
        self.source_politics = float(np.clip(self.source_politics, -1.0, 1.0))


@dataclass
class MinerOutput:
    """Prediction output from the miner for one prompt."""
    signal: str             # "HIGH" | "NEUTRAL" | "LOW"
    confidence: float       # 0.0 → 1.0
    raw_score: float        # raw composite before thresholding
    trust_score: float      # trust UID100 gave the source
    reaction: str           # dominant reaction type
    delta_stability: float  # net change in agent financial_stability
    agent_state: Dict[str, float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Internal helpers — mirrors TrustModel from simulation/models.py
# but frozen to UID100 parameters
# ---------------------------------------------------------------------------

_REACTION_TYPES = ["SUPPORT", "OPPOSITION", "APATHY", "CONFUSION", "FEAR"]


def _uid100_trust(
    agent_politics: float,
    institutional_trust: float,
    source_politics: float,
    source_credibility: float,
) -> float:
    """TrustModel.calculate_trust() specialised for IQ=100.

    IQ=100  →  iq_factor = (100-70)/60 = 0.5
    alignment_weight   = 0.35 - 0.5*0.10 = 0.30
    trust_weight       = 0.30
    credibility_weight = 0.35 + 0.5*0.10 = 0.40
    """
    alignment = 1.0 - abs(agent_politics - source_politics)
    trust = (
        alignment * 0.30
        + institutional_trust * 0.30
        + source_credibility * 0.40
    )
    return float(np.clip(trust, 0.0, 1.0))


def _determine_reaction(
    agent_politics: float,
    source_politics: float,
    trust_score: float,
    impact: float,
    risk_aversion: float,
    optimism: float,
    iq: int = 100,
) -> str:
    political_gap = abs(agent_politics - source_politics)

    p_support = 0.2
    p_opposition = 0.2
    p_apathy = 0.2
    p_confusion = 0.2
    p_fear = 0.2

    if trust_score > 0.6 and political_gap < 0.4:
        p_support += 0.3
        p_opposition -= 0.1
    if trust_score < 0.4 and political_gap > 0.5:
        p_opposition += 0.3
        p_support -= 0.1
    if impact > 0.6 and risk_aversion > 0.5:
        p_fear += 0.25
        p_apathy -= 0.1
    if impact < 0.3:
        p_apathy += 0.3
        p_fear -= 0.1
        p_support -= 0.1
    if iq < 90 and impact > 0.5 and trust_score < 0.5:
        p_confusion += 0.2
    if iq > 110:
        p_confusion -= 0.1
        if optimism > 0.5:
            p_support += 0.1
        else:
            p_opposition += 0.1
    if optimism > 0.7:
        p_fear -= 0.1
        p_support += 0.1

    probs = [max(0.01, p) for p in [p_support, p_opposition, p_apathy, p_confusion, p_fear]]
    total = sum(probs)
    probs = [p / total for p in probs]
    return random.choices(_REACTION_TYPES, weights=probs, k=1)[0]


# ---------------------------------------------------------------------------
# Category-level impact multiplier (hidden weight the miner uses internally)
# ---------------------------------------------------------------------------

_CATEGORY_MULTIPLIER: Dict[str, float] = {
    "economy":     1.30,
    "crisis":      1.25,
    "military":    1.10,
    "politics":    1.05,
    "diplomacy":   0.95,
    "health":      0.90,
    "social":      0.85,
    "technology":  0.80,
    "environment": 0.75,
}


# ---------------------------------------------------------------------------
# SynthSN50Miner
# ---------------------------------------------------------------------------

class SynthSN50Miner:
    """Simulates the UID100 miner on SYNTH SN50.

    Internally maintains a single persistent agent (IQ=100, neutral politics)
    whose state evolves with each prompt. HIGH asset signals are derived from
    the agent's financial_stability after processing.

    Thresholds (hidden from caller — these are what we reverse-engineer):
        HIGH    if composite_score > 0.58
        LOW     if composite_score < 0.42
        NEUTRAL otherwise
    """

    UID = 100
    IQ = 100

    # Signal thresholds (kept opaque — discovered via probing)
    _THRESHOLD_HIGH = 0.58
    _THRESHOLD_LOW = 0.42

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        # Persistent agent state
        self._state: Dict[str, float] = {
            "politics": 0.0,
            "optimism": 0.55,
            "trust_institutions": 0.50,
            "risk_aversion": 0.40,
            "financial_stability": 0.50,
        }
        self._history: List[MinerOutput] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def predict(self, prompt: MinerPrompt) -> MinerOutput:
        """Process one prompt and return an asset signal."""
        trust = _uid100_trust(
            agent_politics=self._state["politics"],
            institutional_trust=self._state["trust_institutions"],
            source_politics=prompt.source_politics,
            source_credibility=prompt.source_credibility,
        )

        reaction = _determine_reaction(
            agent_politics=self._state["politics"],
            source_politics=prompt.source_politics,
            trust_score=trust,
            impact=prompt.impact,
            risk_aversion=self._state["risk_aversion"],
            optimism=self._state["optimism"],
            iq=self.IQ,
        )

        cat_mult = _CATEGORY_MULTIPLIER.get(prompt.category, 1.0)
        eff_impact = float(np.clip(prompt.impact * cat_mult, 0.0, 1.0))
        base_impact = eff_impact * trust

        delta_stability = self._apply_reaction(reaction, base_impact)

        # Composite HIGH score = weighted mix of key agent metrics
        raw_score = self._composite_score(trust, prompt.impact, prompt.source_credibility)

        signal = self._threshold(raw_score)
        confidence = self._compute_confidence(raw_score)

        output = MinerOutput(
            signal=signal,
            confidence=round(confidence, 4),
            raw_score=round(raw_score, 6),
            trust_score=round(trust, 6),
            reaction=reaction,
            delta_stability=round(delta_stability, 6),
            agent_state=dict(self._state),
        )
        self._history.append(output)
        return output

    def predict_batch(self, prompts: List[MinerPrompt]) -> List[MinerOutput]:
        return [self.predict(p) for p in prompts]

    def reset_state(self):
        """Reset agent to initial state (call between independent probe runs)."""
        self._state = {
            "politics": 0.0,
            "optimism": 0.55,
            "trust_institutions": 0.50,
            "risk_aversion": 0.40,
            "financial_stability": 0.50,
        }
        self._history.clear()

    @property
    def history(self) -> List[MinerOutput]:
        return list(self._history)

    # ------------------------------------------------------------------
    # Internal mechanics (not exposed to reverse engineer)
    # ------------------------------------------------------------------

    def _apply_reaction(self, reaction: str, base_impact: float) -> float:
        """Update agent state based on reaction; return delta to financial_stability."""
        s = self._state
        prev_stability = s["financial_stability"]

        if reaction == "SUPPORT":
            s["optimism"] = float(np.clip(s["optimism"] + base_impact * 0.05, 0, 1))
            s["trust_institutions"] = float(np.clip(s["trust_institutions"] + base_impact * 0.03, 0, 1))
            s["financial_stability"] = float(np.clip(s["financial_stability"] + base_impact * 0.02, 0, 1))
        elif reaction == "OPPOSITION":
            s["optimism"] = float(np.clip(s["optimism"] - base_impact * 0.04, 0, 1))
            s["trust_institutions"] = float(np.clip(s["trust_institutions"] - base_impact * 0.05, 0, 1))
            shift = 0.02 * base_impact * (1 if s["politics"] > 0 else -1)
            s["politics"] = float(np.clip(s["politics"] + shift, -1.0, 1.0))
        elif reaction == "FEAR":
            s["optimism"] = float(np.clip(s["optimism"] - base_impact * 0.06, 0, 1))
            s["risk_aversion"] = float(np.clip(s["risk_aversion"] + base_impact * 0.04, 0, 1))
            s["financial_stability"] = float(np.clip(s["financial_stability"] - base_impact * 0.03, 0, 1))
        elif reaction == "CONFUSION":
            s["trust_institutions"] = float(np.clip(s["trust_institutions"] - base_impact * 0.03, 0, 1))
            s["optimism"] = float(np.clip(s["optimism"] - base_impact * 0.02, 0, 1))
        # APATHY: no state change

        return s["financial_stability"] - prev_stability

    def _composite_score(
        self,
        trust: float,
        impact: float,
        source_credibility: float,
    ) -> float:
        """Hidden composite formula used to determine HIGH/NEUTRAL/LOW.

        Combines trust, agent optimism, agent financial_stability, and
        source credibility with impact as an amplifier.

        This is exactly what the reverse engineer is trying to discover.
        """
        s = self._state
        score = (
            0.35 * trust
            + 0.25 * s["financial_stability"]
            + 0.20 * s["optimism"]
            + 0.15 * source_credibility
            + 0.05 * (1.0 - impact)   # low volatility adds a small positive bias
        )
        return float(np.clip(score, 0.0, 1.0))

    def _threshold(self, score: float) -> str:
        if score > self._THRESHOLD_HIGH:
            return "HIGH"
        if score < self._THRESHOLD_LOW:
            return "LOW"
        return "NEUTRAL"

    def _compute_confidence(self, score: float) -> float:
        """How far score is from the nearest threshold → confidence."""
        dist_high = abs(score - self._THRESHOLD_HIGH)
        dist_low = abs(score - self._THRESHOLD_LOW)
        nearest = min(dist_high, dist_low)
        # Normalise: max possible distance from midpoint (0.5) is 0.5
        return float(np.clip(nearest / 0.5, 0.0, 1.0))
