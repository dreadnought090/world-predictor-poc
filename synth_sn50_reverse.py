#!/usr/bin/env python3
"""SYNTH SN50 — UID100 HIGH Asset Formula Reverse Engineering Runner.

Usage:
    python synth_sn50_reverse.py              # full run (all probes)
    python synth_sn50_reverse.py --quick      # quick run (smaller dataset)
    python synth_sn50_reverse.py --out result.json  # save JSON output
"""

import argparse
import json
import sys
import time

from world_predictor.synth_sn50 import (
    SynthSN50Miner,
    MinerProbe,
    FormulaReverseEngineer,
)


BANNER = """
╔══════════════════════════════════════════════════════════════╗
║   SYNTH SN50  —  UID100  HIGH-Asset Formula Reverse Eng.    ║
╚══════════════════════════════════════════════════════════════╝
"""


def run(quick: bool = False, out_path: str | None = None, seed: int = 42):
    print(BANNER)

    # ------------------------------------------------------------------ #
    # 1. Instantiate miner (black box)
    # ------------------------------------------------------------------ #
    print("► [1/4] Initialising UID100 miner (IQ=100, politics=0.0, neutral)…")
    miner = SynthSN50Miner(seed=seed)
    print(f"        UID={miner.UID}  IQ={miner.IQ}")
    print(f"        initial state: {miner._state}")

    # ------------------------------------------------------------------ #
    # 2. Probe miner — collect (prompt, output) pairs
    # ------------------------------------------------------------------ #
    print("\n► [2/4] Probing miner with structured prompts…")
    probe = MinerProbe(miner, seed=seed)

    t0 = time.time()
    if quick:
        dataset = probe.run_full_probe(
            grid_steps=3, monte_carlo_n=300, oat_steps=15, cat_n=30
        )
    else:
        dataset = probe.run_full_probe(
            grid_steps=5, monte_carlo_n=2000, oat_steps=30, cat_n=100
        )
    elapsed = time.time() - t0
    print(f"        done in {elapsed:.1f}s — {len(dataset)} total observations")

    counts = dataset.signal_counts()
    total = len(dataset)
    print(
        f"        HIGH={counts['HIGH']} ({100*counts['HIGH']//total}%)  "
        f"NEUTRAL={counts['NEUTRAL']} ({100*counts['NEUTRAL']//total}%)  "
        f"LOW={counts['LOW']} ({100*counts['LOW']//total}%)"
    )

    # ------------------------------------------------------------------ #
    # 3. Reverse engineer the formula
    # ------------------------------------------------------------------ #
    print("\n► [3/4] Fitting reverse-engineer model…")
    engineer = FormulaReverseEngineer()
    formula = engineer.fit(dataset)

    # ------------------------------------------------------------------ #
    # 4. Report
    # ------------------------------------------------------------------ #
    print("\n► [4/4] Results\n")
    print("━" * 64)
    print(formula.formula_str())
    print("━" * 64)

    print("\nFeature importance ranking:")
    ranked = sorted(formula.coefficients, key=lambda x: -x.abs_importance)
    for rank, fc in enumerate(ranked, 1):
        bar = "█" * int(fc.abs_importance * 30)
        print(f"  {rank:2}. {fc.name:<22}  coeff={fc.coefficient:+.4f}  {bar}")

    print("\nCategory mean scores (HIGH signal strength per news category):")
    for cat, score in formula.category_scores.items():
        bar = "█" * int(score * 30)
        marker = " ← top" if score == max(formula.category_scores.values()) else ""
        print(f"  {cat:<14} {score:.4f}  {bar}{marker}")

    print("\nSensitivity (OAT, economy category only):")
    print(engineer.sensitivity_report(dataset))

    print("\nSignal distribution in probe dataset:")
    for sig, pct in formula.signal_distribution.items():
        print(f"  {sig:<8} {pct*100:.1f}%")

    # ------------------------------------------------------------------ #
    # 5. Plain-language summary of discovered formula
    # ------------------------------------------------------------------ #
    top2 = ranked[:2]
    print("\n" + "═" * 64)
    print("CONCLUSION — UID100 HIGH Asset Formula (Reverse Engineered)")
    print("═" * 64)
    print(
        f"""
The miner predicts HIGH when a composite score exceeds {formula.threshold_high:.4f}.

Dominant drivers (by coefficient magnitude):
  1. {top2[0].name:<22}  weight ≈ {top2[0].coefficient:+.4f}
  2. {top2[1].name:<22}  weight ≈ {top2[1].coefficient:+.4f}

Full formula (recovered):
  score = {formula.intercept:+.4f}
{chr(10).join(f"        {('+' if fc.coefficient >= 0 else '-')} {abs(fc.coefficient):.4f}·{fc.name}" for fc in ranked)}

Thresholds:
  HIGH    → score > {formula.threshold_high:.4f}
  LOW     → score < {formula.threshold_low:.4f}
  NEUTRAL → {formula.threshold_low:.4f} ≤ score ≤ {formula.threshold_high:.4f}

Model quality:
  R² (continuous score prediction) = {formula.r2_score_regression:.4f}
  Accuracy (3-class signal)        = {formula.accuracy_classification:.4f}
"""
    )

    # ------------------------------------------------------------------ #
    # 6. Optional JSON output
    # ------------------------------------------------------------------ #
    result = formula.to_dict()
    result["probe_records"] = len(dataset)
    result["elapsed_seconds"] = round(elapsed, 2)

    if out_path:
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"Results saved → {out_path}")

    return result


def main():
    parser = argparse.ArgumentParser(description="UID100 SYNTH SN50 reverse engineer")
    parser.add_argument("--quick", action="store_true", help="smaller probe set")
    parser.add_argument("--out", default=None, help="save JSON results to file")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed")
    args = parser.parse_args()
    run(quick=args.quick, out_path=args.out, seed=args.seed)


if __name__ == "__main__":
    main()
