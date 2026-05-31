"""MinerProbe — systematic prompt generator for UID100 reverse engineering.

Strategy:
1. Grid sweep — exhaustive coverage of the input space
2. Random Monte Carlo — dense random sampling
3. Sensitivity sweep — one variable at a time (OAT)

All probe results are collected into a ProbeDataset for downstream analysis.
"""

from __future__ import annotations

import itertools
import random
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np

from .miner import MinerPrompt, MinerOutput, SynthSN50Miner, NEWS_CATEGORIES


# ---------------------------------------------------------------------------
# Dataset container
# ---------------------------------------------------------------------------

@dataclass
class ProbeRecord:
    """One (input, output) observation."""
    # Inputs
    category: str
    impact: float
    source_credibility: float
    source_politics: float
    region: str
    # Outputs
    signal: str
    confidence: float
    raw_score: float
    trust_score: float
    reaction: str
    delta_stability: float
    # Derived numeric label
    signal_num: int = 0   # HIGH=1, NEUTRAL=0, LOW=-1

    def __post_init__(self):
        self.signal_num = {"HIGH": 1, "NEUTRAL": 0, "LOW": -1}[self.signal]


@dataclass
class ProbeDataset:
    records: List[ProbeRecord] = field(default_factory=list)

    def append(self, prompt: MinerPrompt, output: MinerOutput):
        rec = ProbeRecord(
            category=prompt.category,
            impact=prompt.impact,
            source_credibility=prompt.source_credibility,
            source_politics=prompt.source_politics,
            region=prompt.region,
            signal=output.signal,
            confidence=output.confidence,
            raw_score=output.raw_score,
            trust_score=output.trust_score,
            reaction=output.reaction,
            delta_stability=output.delta_stability,
        )
        self.records.append(rec)

    def __len__(self) -> int:
        return len(self.records)

    def signal_counts(self) -> dict:
        counts: dict = {"HIGH": 0, "NEUTRAL": 0, "LOW": 0}
        for r in self.records:
            counts[r.signal] += 1
        return counts

    def as_xy(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Return (X_features, y_score, y_signal_num) arrays for regression."""
        X_rows = []
        y_score = []
        y_sig = []
        for r in self.records:
            # Encode category as ordinal economic_weight
            cat_weights = {
                "economy": 1.30, "crisis": 1.25, "military": 1.10,
                "politics": 1.05, "diplomacy": 0.95, "health": 0.90,
                "social": 0.85, "technology": 0.80, "environment": 0.75,
            }
            cat_w = cat_weights.get(r.category, 1.0)

            X_rows.append([
                r.impact,
                r.source_credibility,
                r.source_politics,
                r.trust_score,
                cat_w,
                r.impact * r.source_credibility,   # interaction
                r.impact * r.trust_score,           # interaction
                r.source_credibility * r.trust_score,
            ])
            y_score.append(r.raw_score)
            y_sig.append(r.signal_num)

        return (
            np.array(X_rows, dtype=np.float64),
            np.array(y_score, dtype=np.float64),
            np.array(y_sig, dtype=np.float64),
        )


# ---------------------------------------------------------------------------
# MinerProbe
# ---------------------------------------------------------------------------

REGIONS = ["US", "CN", "JP", "DE", "GB", "IN", "BR"]


class MinerProbe:
    """Sends structured prompts to a SynthSN50Miner and records observations."""

    def __init__(self, miner: SynthSN50Miner, seed: Optional[int] = 42):
        self.miner = miner
        self._rng = random.Random(seed)
        self._np_rng = np.random.default_rng(seed)

    # ------------------------------------------------------------------
    # Probe strategies
    # ------------------------------------------------------------------

    def grid_sweep(
        self,
        impact_steps: int = 5,
        credibility_steps: int = 5,
        politics_steps: int = 5,
        categories: Optional[List[str]] = None,
    ) -> ProbeDataset:
        """Exhaustive grid over impact × credibility × source_politics × category.

        Each combination is run with a fresh miner state so individual factor
        effects are isolated.
        """
        dataset = ProbeDataset()
        cats = categories or NEWS_CATEGORIES

        impacts = np.linspace(0.0, 1.0, impact_steps)
        creds = np.linspace(0.0, 1.0, credibility_steps)
        pols = np.linspace(-1.0, 1.0, politics_steps)

        for cat, imp, cred, pol in itertools.product(cats, impacts, creds, pols):
            self.miner.reset_state()
            prompt = MinerPrompt(
                category=cat,
                impact=round(float(imp), 3),
                source_credibility=round(float(cred), 3),
                source_politics=round(float(pol), 3),
                region="US",
                headline=f"grid:{cat}|imp={imp:.2f}|cred={cred:.2f}|pol={pol:.2f}",
            )
            output = self.miner.predict(prompt)
            dataset.append(prompt, output)

        return dataset

    def monte_carlo(self, n: int = 2000) -> ProbeDataset:
        """Dense random sampling across the entire input space."""
        dataset = ProbeDataset()
        cats = NEWS_CATEGORIES
        regions = REGIONS

        for _ in range(n):
            self.miner.reset_state()
            prompt = MinerPrompt(
                category=self._rng.choice(cats),
                impact=round(self._np_rng.uniform(0.0, 1.0), 4),
                source_credibility=round(self._np_rng.uniform(0.0, 1.0), 4),
                source_politics=round(self._np_rng.uniform(-1.0, 1.0), 4),
                region=self._rng.choice(regions),
            )
            output = self.miner.predict(prompt)
            dataset.append(prompt, output)

        return dataset

    def sensitivity_oat(self, base_prompt: Optional[MinerPrompt] = None, steps: int = 20) -> ProbeDataset:
        """One-At-a-Time sensitivity analysis.

        Holds all inputs at baseline and sweeps each factor independently.
        Perfect for isolating individual variable contributions.
        """
        dataset = ProbeDataset()
        if base_prompt is None:
            base_prompt = MinerPrompt(
                category="economy",
                impact=0.5,
                source_credibility=0.5,
                source_politics=0.0,
                region="US",
            )

        sweep_vars = {
            "impact": np.linspace(0.0, 1.0, steps),
            "source_credibility": np.linspace(0.0, 1.0, steps),
            "source_politics": np.linspace(-1.0, 1.0, steps),
        }

        for var_name, values in sweep_vars.items():
            for val in values:
                self.miner.reset_state()
                kwargs = {
                    "category": base_prompt.category,
                    "impact": base_prompt.impact,
                    "source_credibility": base_prompt.source_credibility,
                    "source_politics": base_prompt.source_politics,
                    "region": base_prompt.region,
                    "headline": f"oat:{var_name}={val:.3f}",
                }
                kwargs[var_name] = round(float(val), 4)
                prompt = MinerPrompt(**kwargs)
                output = self.miner.predict(prompt)
                dataset.append(prompt, output)

        return dataset

    def category_comparison(self, n_per_cat: int = 100) -> ProbeDataset:
        """Hold all inputs fixed, sweep across categories to measure category multiplier."""
        dataset = ProbeDataset()
        for cat in NEWS_CATEGORIES:
            for _ in range(n_per_cat):
                self.miner.reset_state()
                prompt = MinerPrompt(
                    category=cat,
                    impact=round(self._np_rng.uniform(0.3, 0.7), 4),
                    source_credibility=round(self._np_rng.uniform(0.4, 0.8), 4),
                    source_politics=round(self._np_rng.uniform(-0.3, 0.3), 4),
                    region="US",
                )
                output = self.miner.predict(prompt)
                dataset.append(prompt, output)
        return dataset

    def run_full_probe(
        self,
        grid_steps: int = 4,
        monte_carlo_n: int = 1500,
        oat_steps: int = 25,
        cat_n: int = 80,
    ) -> ProbeDataset:
        """Run all probe strategies and merge into one dataset."""
        print("[probe] grid sweep...")
        d1 = self.grid_sweep(grid_steps, grid_steps, grid_steps)
        print(f"        {len(d1)} records — signals: {d1.signal_counts()}")

        print("[probe] monte carlo...")
        d2 = self.monte_carlo(monte_carlo_n)
        print(f"        {len(d2)} records — signals: {d2.signal_counts()}")

        print("[probe] OAT sensitivity...")
        d3 = self.sensitivity_oat(steps=oat_steps)
        print(f"        {len(d3)} records — signals: {d3.signal_counts()}")

        print("[probe] category comparison...")
        d4 = self.category_comparison(cat_n)
        print(f"        {len(d4)} records — signals: {d4.signal_counts()}")

        merged = ProbeDataset()
        merged.records = d1.records + d2.records + d3.records + d4.records
        print(f"[probe] total: {len(merged)} records")
        return merged
