"""Centralized configuration for World Predictor.

Loads from config.yaml if present, otherwise uses defaults.
All magic numbers live here — no hardcoded constants elsewhere.
"""

import os
from pathlib import Path
from typing import Any, Dict

import yaml

_CONFIG_PATH = Path(os.environ.get("WP_CONFIG_PATH", "config.yaml"))

# ---------------------------------------------------------------------------
# Defaults — used when config.yaml is missing or incomplete
# ---------------------------------------------------------------------------

DEFAULTS: Dict[str, Any] = {
    "simulation": {
        "agents_per_country": 1000,
        "countries": ["US", "CN", "IN", "BR", "RU"],
        "impact_weights": {
            "economic": 0.4,
            "social": 0.3,
            "political": 0.3,
        },
        "news_decay_rate": 0.92,
        "consensus_threshold": 0.6,
        "opinion_diffusion": {
            "enabled": True,
            "interactions_per_day": 5,
            "confidence_bound": 0.4,
            "shift_rate": 0.05,
        },
        "memory_decay": {
            "enabled": True,
            "optimism_decay": 0.02,
            "trust_decay": 0.01,
            "fear_decay": 0.03,
        },
        "revolution_risk": {
            "trust_weight": 0.3,
            "fear_weight": 0.25,
            "opposition_weight": 0.25,
            "polarization_weight": 0.2,
            "threshold": 0.7,
        },
    },
    "news": {
        "fetch_interval_hours": 6,
        "newsapi_categories": ["business", "technology", "science", "health", "general"],
        "max_items_per_fetch": 100,
        "classification_batch_size": 10,
        "classifier_model": "claude-haiku-4-5-20251001",
    },
    "database": {
        "path": "world_predictor.db",
        "snapshot_interval_days": 1,
        "max_history_days": 365,
    },
    "api": {
        "host": "0.0.0.0",
        "port": 8000,
        "cors_origins": ["*"],
        "max_agent_response": 500,
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base, preferring override values."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config() -> Dict[str, Any]:
    """Load configuration from YAML file, merged with defaults."""
    config = DEFAULTS.copy()
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH, "r") as f:
            user_config = yaml.safe_load(f) or {}
        config = _deep_merge(config, user_config)
    return config


# Singleton config instance
_config: Dict[str, Any] = {}


def get_config() -> Dict[str, Any]:
    """Get the global config (lazy-loaded)."""
    global _config
    if not _config:
        _config = load_config()
    return _config


def reload_config() -> Dict[str, Any]:
    """Force reload from disk."""
    global _config
    _config = load_config()
    return _config


# Convenience accessors
def sim_config() -> Dict[str, Any]:
    return get_config()["simulation"]


def news_config() -> Dict[str, Any]:
    return get_config()["news"]


def db_config() -> Dict[str, Any]:
    return get_config()["database"]


def api_config() -> Dict[str, Any]:
    return get_config()["api"]
