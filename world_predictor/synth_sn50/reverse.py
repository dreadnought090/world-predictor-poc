"""FormulaReverseEngineer — derives UID100 HIGH asset formula from probe observations.

Approach:
1. Linear regression  → coefficient per feature (what multiplies what)
2. Logistic regression → decision boundary / thresholds
3. Feature importance  → ranking of which inputs matter most
4. Threshold estimation → empirical HIGH/LOW cutoffs from distribution

The output is a ReversedFormula that fully describes the miner's decision rule.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge
from sklearn.metrics import r2_score, accuracy_score
from sklearn.preprocessing import StandardScaler

from .probe import ProbeDataset

FEATURE_NAMES = [
    "impact",
    "source_credibility",
    "source_politics",
    "trust_score",
    "category_weight",
    "impact×credibility",
    "impact×trust",
    "credibility×trust",
]


# ---------------------------------------------------------------------------
# Result containers
# ---------------------------------------------------------------------------

@dataclass
class FeatureCoefficient:
    name: str
    coefficient: float
    abs_importance: float   # |coeff| normalised to sum=1


@dataclass
class ReversedFormula:
    """Human-readable recovered formula for UID100 HIGH asset prediction."""

    # Regression coefficients
    intercept: float
    coefficients: List[FeatureCoefficient]

    # Discovered thresholds
    threshold_high: float
    threshold_low: float

    # Model fit quality
    r2_score_regression: float
    accuracy_classification: float

    # Category multipliers learned
    category_scores: Dict[str, float] = field(default_factory=dict)

    # Signal distribution in probe data
    signal_distribution: Dict[str, float] = field(default_factory=dict)

    def formula_str(self) -> str:
        """Render the reverse-engineered formula as a readable string."""
        terms = []
        for fc in sorted(self.coefficients, key=lambda x: -abs(x.coefficient)):
            sign = "+" if fc.coefficient >= 0 else "-"
            terms.append(f"  {sign} {abs(fc.coefficient):.4f} × {fc.name}")
        body = "\n".join(terms)
        return (
            f"composite_score =\n"
            f"  {self.intercept:+.4f} (intercept)\n"
            f"{body}\n\n"
            f"signal:\n"
            f"  HIGH    if composite_score > {self.threshold_high:.4f}\n"
            f"  LOW     if composite_score < {self.threshold_low:.4f}\n"
            f"  NEUTRAL otherwise\n\n"
            f"fit quality:\n"
            f"  R² (regression)     = {self.r2_score_regression:.4f}\n"
            f"  accuracy (3-class)  = {self.accuracy_classification:.4f}"
        )

    def to_dict(self) -> dict:
        return {
            "intercept": self.intercept,
            "coefficients": [
                {"name": fc.name, "coefficient": fc.coefficient, "importance": fc.abs_importance}
                for fc in self.coefficients
            ],
            "threshold_high": self.threshold_high,
            "threshold_low": self.threshold_low,
            "r2_score": self.r2_score_regression,
            "accuracy": self.accuracy_classification,
            "category_scores": self.category_scores,
            "signal_distribution": self.signal_distribution,
            "formula_string": self.formula_str(),
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


# ---------------------------------------------------------------------------
# Reverse engineer
# ---------------------------------------------------------------------------

class FormulaReverseEngineer:
    """Fits UID100's HIGH asset formula from a ProbeDataset."""

    def __init__(self):
        self._scaler = StandardScaler()
        self._reg: Optional[Ridge] = None
        self._clf: Optional[LogisticRegression] = None

    def fit(self, dataset: ProbeDataset) -> ReversedFormula:
        if len(dataset) < 10:
            raise ValueError("Need at least 10 probe records to fit formula")

        X, y_score, y_sig = dataset.as_xy()

        # ---- Regression: predict raw_score from features ----
        X_scaled = self._scaler.fit_transform(X)
        reg = Ridge(alpha=0.01)
        reg.fit(X_scaled, y_score)
        self._reg = reg

        y_pred_score = reg.predict(X_scaled)
        r2 = float(r2_score(y_score, y_pred_score))

        # ---- Classification: predict signal (HIGH/NEUTRAL/LOW) ----
        clf = LogisticRegression(max_iter=500, C=10.0)
        try:
            clf.fit(X_scaled, y_sig)
            self._clf = clf
            acc = float(accuracy_score(y_sig, clf.predict(X_scaled)))
        except Exception:
            acc = 0.0

        # ---- Unscale coefficients to original feature space ----
        raw_coefs = reg.coef_ / self._scaler.scale_
        intercept = float(reg.intercept_ - np.dot(raw_coefs, self._scaler.mean_))
        abs_sum = float(np.sum(np.abs(raw_coefs))) or 1.0

        coefficients = [
            FeatureCoefficient(
                name=FEATURE_NAMES[i],
                coefficient=round(float(raw_coefs[i]), 6),
                abs_importance=round(abs(float(raw_coefs[i])) / abs_sum, 4),
            )
            for i in range(len(FEATURE_NAMES))
        ]

        # ---- Threshold estimation from observed score distribution ----
        high_scores = [r.raw_score for r in dataset.records if r.signal == "HIGH"]
        low_scores = [r.raw_score for r in dataset.records if r.signal == "LOW"]
        neutral_scores = [r.raw_score for r in dataset.records if r.signal == "NEUTRAL"]

        threshold_high = self._estimate_threshold_high(high_scores, neutral_scores)
        threshold_low = self._estimate_threshold_low(low_scores, neutral_scores)

        # ---- Category multipliers ----
        category_scores = self._estimate_category_scores(dataset)

        # ---- Signal distribution ----
        counts = dataset.signal_counts()
        total = max(len(dataset), 1)
        signal_dist = {k: round(v / total, 4) for k, v in counts.items()}

        return ReversedFormula(
            intercept=round(intercept, 6),
            coefficients=coefficients,
            threshold_high=round(threshold_high, 4),
            threshold_low=round(threshold_low, 4),
            r2_score_regression=round(r2, 4),
            accuracy_classification=round(acc, 4),
            category_scores=category_scores,
            signal_distribution=signal_dist,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _estimate_threshold_high(
        self,
        high_scores: List[float],
        neutral_scores: List[float],
    ) -> float:
        if not high_scores or not neutral_scores:
            return 0.58
        min_high = float(np.min(high_scores))
        max_neutral = float(np.max(neutral_scores)) if neutral_scores else min_high
        # Midpoint between max-neutral and min-high
        return (max_neutral + min_high) / 2.0

    def _estimate_threshold_low(
        self,
        low_scores: List[float],
        neutral_scores: List[float],
    ) -> float:
        if not low_scores or not neutral_scores:
            return 0.42
        max_low = float(np.max(low_scores))
        min_neutral = float(np.min(neutral_scores)) if neutral_scores else max_low
        return (max_low + min_neutral) / 2.0

    def _estimate_category_scores(self, dataset: ProbeDataset) -> Dict[str, float]:
        """Mean raw_score per category → reveals the category multiplier effect."""
        cat_scores: Dict[str, List[float]] = {}
        for r in dataset.records:
            cat_scores.setdefault(r.category, []).append(r.raw_score)
        return {
            cat: round(float(np.mean(scores)), 4)
            for cat, scores in sorted(cat_scores.items(), key=lambda x: -np.mean(x[1]))
        }

    def sensitivity_report(self, dataset: ProbeDataset) -> str:
        """Print partial derivatives (Δscore / Δinput) from OAT records."""
        oat_records = [r for r in dataset.records if r.category == "economy"]
        if len(oat_records) < 5:
            return "Not enough OAT records for sensitivity report."

        # Group by variable (approximate by checking which dim changes most)
        lines = ["OAT Sensitivity (Δscore per unit Δinput):"]

        for var, getter in [
            ("impact", lambda r: r.impact),
            ("source_credibility", lambda r: r.source_credibility),
            ("source_politics", lambda r: r.source_politics),
        ]:
            vals = [(getter(r), r.raw_score) for r in oat_records]
            if len(vals) < 2:
                continue
            vals.sort(key=lambda x: x[0])
            xs = np.array([v[0] for v in vals])
            ys = np.array([v[1] for v in vals])
            if xs.max() - xs.min() < 1e-6:
                continue
            slope, _ = np.polyfit(xs, ys, 1)
            lines.append(f"  d(score)/d({var}) ≈ {slope:+.4f}")

        return "\n".join(lines)
