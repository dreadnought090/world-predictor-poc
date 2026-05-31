"""SYNTH SN50 Miner — UID100 Reverse Engineering Infrastructure.

Architecture:
  miner.py   - SynthSN50Miner (UID100 agent black-box predictor)
  probe.py   - MinerProbe (systematic prompt generator)
  reverse.py - FormulaReverseEngineer (fits formula from observations)
"""

from .miner import SynthSN50Miner, MinerPrompt, MinerOutput
from .probe import MinerProbe, ProbeDataset
from .reverse import FormulaReverseEngineer, ReversedFormula

__all__ = [
    "SynthSN50Miner",
    "MinerPrompt",
    "MinerOutput",
    "MinerProbe",
    "ProbeDataset",
    "FormulaReverseEngineer",
    "ReversedFormula",
]
