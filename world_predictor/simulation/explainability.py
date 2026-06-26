"""Explainability and workflow helpers for predictions and scenarios."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional

import numpy as np

from world_predictor.config import sim_config
from world_predictor.simulation.models import ReactionTypes


COUNTRY_NAMES: Dict[str, str] = {
    "US": "United States",
    "CN": "China",
    "IN": "India",
    "BR": "Brazil",
    "RU": "Russia",
    "JP": "Japan",
    "DE": "Germany",
    "GB": "United Kingdom",
    "FR": "France",
    "KR": "South Korea",
    "AU": "Australia",
    "MX": "Mexico",
    "ID": "Indonesia",
    "NG": "Nigeria",
    "EG": "Egypt",
    "SA": "Saudi Arabia",
    "TR": "Turkey",
    "PK": "Pakistan",
    "PH": "Philippines",
    "TH": "Thailand",
}

COUNTRY_ALIASES: Dict[str, List[str]] = {
    "US": ["united states", "usa", "u.s.", "us", "america"],
    "CN": ["china", "chinese", "beijing", "prc"],
    "IN": ["india", "indian", "delhi"],
    "BR": ["brazil", "brazilian"],
    "RU": ["russia", "russian", "moscow"],
    "JP": ["japan", "japanese", "tokyo"],
    "DE": ["germany", "german", "berlin"],
    "GB": ["united kingdom", "uk", "britain", "british", "london"],
    "FR": ["france", "french", "paris"],
    "KR": ["south korea", "korea", "korean", "seoul"],
    "AU": ["australia", "australian"],
    "MX": ["mexico", "mexican"],
    "ID": ["indonesia", "indonesian", "jakarta"],
    "NG": ["nigeria", "nigerian"],
    "EG": ["egypt", "egyptian"],
    "SA": ["saudi arabia", "saudi"],
    "TR": ["turkey", "turkish"],
    "PK": ["pakistan", "pakistani"],
    "PH": ["philippines", "philippine", "manila"],
    "TH": ["thailand", "thai"],
}

EVENT_KEYWORDS: Dict[str, List[str]] = {
    "WAR": ["war", "invasion", "missile", "attack", "armed conflict", "military strike"],
    "TRADE_WAR": ["tariff", "export ban", "import ban", "trade war", "sanction", "rare earth", "embargo"],
    "ECONOMIC_CRISIS": ["financial crash", "bank run", "debt crisis", "recession", "currency crisis", "market crash"],
    "PANDEMIC": ["pandemic", "virus", "outbreak", "lockdown", "epidemic"],
    "ELECTION": ["election", "presidential", "vote", "campaign"],
    "CIVIL_UNREST": ["protest", "riot", "civil unrest", "strike", "demonstration"],
    "NATURAL_DISASTER": ["earthquake", "flood", "hurricane", "wildfire", "disaster"],
    "PEACE_DEAL": ["peace deal", "ceasefire", "treaty", "normalization"],
    "TECH_BREAKTHROUGH": ["ai breakthrough", "chip breakthrough", "technology breakthrough", "quantum"],
}

SECTOR_KEYWORDS: Dict[str, List[str]] = {
    "energy": ["oil", "gas", "energy", "electricity", "opec"],
    "food": ["food", "grain", "rice", "wheat", "corn", "fertilizer"],
    "technology": ["ai", "chip", "semiconductor", "software", "rare earth", "data center"],
    "finance": ["bank", "market", "debt", "bond", "currency", "inflation", "rate"],
    "trade": ["tariff", "export", "import", "shipping", "supply chain", "sanction"],
    "health": ["pandemic", "health", "hospital", "vaccine", "virus"],
    "security": ["war", "military", "missile", "terror", "coup", "attack"],
    "climate": ["climate", "flood", "drought", "wildfire", "earthquake"],
}

PRESET_EVENT_HINTS = {
    "financial_crash": ["financial crash", "market crash", "bank run", "global recession"],
    "pandemic_outbreak": ["pandemic", "virus", "outbreak", "lockdown"],
    "ukraine_war": ["ukraine", "russia invades", "eastern europe war"],
    "us_election": ["us election", "u.s. election", "american election"],
    "middle_east_peace": ["middle east peace", "peace agreement", "ceasefire"],
    "ai_breakthrough": ["ai breakthrough", "artificial intelligence breakthrough"],
}

PRESET_POLICY_HINTS = {
    "rate_hike": ["rate hike", "interest rate hike", "tightening"],
    "rate_cut": ["rate cut", "interest rate cut", "easing"],
    "stimulus_package": ["stimulus", "fiscal package", "rescue package"],
    "austerity": ["austerity", "spending cuts"],
    "martial_law": ["martial law", "emergency rule"],
    "free_trade": ["free trade", "trade agreement"],
    "censorship": ["censorship", "internet ban", "social media ban"],
    "healthcare_reform": ["healthcare reform", "universal healthcare"],
}


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _keyword_score(text: str, keywords: Iterable[str]) -> int:
    return sum(1 for keyword in keywords if keyword in text)


def _level(score: float) -> str:
    if score >= 0.76:
        return "high"
    if score >= 0.52:
        return "medium"
    return "low"


def _direction(delta: float, lower_is_better: bool = False) -> str:
    if abs(delta) < 0.01:
        return "neutral"
    if lower_is_better:
        return "positive" if delta < 0 else "negative"
    return "positive" if delta > 0 else "negative"


def parse_scenario_text(text: str, available_countries: Optional[List[str]] = None) -> Dict[str, Any]:
    """Turn free-form scenario text into explicit, editable assumptions."""
    raw = text.strip()
    lowered = raw.lower()
    countries = available_countries or sim_config().get("countries", list(COUNTRY_NAMES))

    found: List[str] = []
    token_set = {token.upper() for token in re.findall(r"\b[A-Za-z]{2}\b", raw)}
    for code in countries:
        aliases = COUNTRY_ALIASES.get(code, [COUNTRY_NAMES.get(code, code).lower()])
        if code in token_set or any(alias in lowered for alias in aliases):
            found.append(code)

    if not found:
        found = ["Global"]

    event_scores = {
        event_type: _keyword_score(lowered, keywords)
        for event_type, keywords in EVENT_KEYWORDS.items()
    }
    event_type = max(event_scores, key=event_scores.get)
    if event_scores[event_type] == 0:
        event_type = "CIVIL_UNREST" if any(word in lowered for word in ["shock", "crisis", "instability"]) else "TRADE_WAR"

    sectors = [
        sector
        for sector, keywords in SECTOR_KEYWORDS.items()
        if _keyword_score(lowered, keywords) > 0
    ]
    if not sectors and event_type in {"WAR", "CIVIL_UNREST"}:
        sectors = ["security"]
    if not sectors and event_type in {"TRADE_WAR", "ECONOMIC_CRISIS"}:
        sectors = ["trade", "finance"]

    severity = "medium"
    magnitude = 0.55
    if any(word in lowered for word in ["catastrophic", "severe", "major", "blocks", "ban", "war", "crash"]):
        severity = "high"
        magnitude = 0.78
    if any(word in lowered for word in ["minor", "limited", "small", "temporary"]):
        severity = "low"
        magnitude = 0.32
    if any(word in lowered for word in ["global", "worldwide"]):
        magnitude = min(1.0, magnitude + 0.08)

    duration_days = 30
    match = re.search(r"\b(\d{1,3})\s*(day|days|d|week|weeks|month|months)\b", lowered)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        if unit.startswith("week"):
            duration_days = amount * 7
        elif unit.startswith("month"):
            duration_days = amount * 30
        else:
            duration_days = amount
    duration_days = max(1, min(365, duration_days))

    uncertainty = "medium"
    if any(word in lowered for word in ["rumor", "could", "may", "possible", "unconfirmed"]):
        uncertainty = "high"
    if any(word in lowered for word in ["confirmed", "announced", "declares", "declared", "official"]):
        uncertainty = "low"

    suggested_preset_event = None
    for preset, hints in PRESET_EVENT_HINTS.items():
        if any(hint in lowered for hint in hints):
            suggested_preset_event = preset
            break

    suggested_policy = None
    for policy, hints in PRESET_POLICY_HINTS.items():
        if any(hint in lowered for hint in hints):
            suggested_policy = policy
            break

    affected = [code for code in found if code != "Global"]
    secondary = _secondary_countries(affected, countries)
    title = raw[:90].strip() or "Custom Scenario"

    confidence = 0.45
    confidence += 0.12 if affected else 0
    confidence += 0.12 if sectors else 0
    confidence += 0.12 if event_scores.get(event_type, 0) > 0 else 0
    confidence += 0.08 if match else 0
    confidence -= 0.12 if uncertainty == "high" else 0
    confidence = round(_clamp(confidence), 2)

    return {
        "title": title,
        "event_type": event_type,
        "affected_countries": affected or list(countries[:5]),
        "secondary_countries": secondary,
        "sectors": sectors,
        "severity": severity,
        "magnitude": round(magnitude, 2),
        "duration_days": duration_days,
        "uncertainty": uncertainty,
        "confidence": {"score": confidence, "level": _level(confidence)},
        "suggested_preset_event": suggested_preset_event,
        "suggested_policy": suggested_policy,
        "summary": _assumption_summary(event_type, affected or list(countries[:5]), sectors, severity, duration_days),
    }


def _secondary_countries(affected: List[str], countries: List[str]) -> List[str]:
    if not affected:
        return []
    preferred = ["US", "CN", "DE", "JP", "GB", "FR", "IN", "KR", "AU", "ID"]
    ordered = [code for code in preferred if code in countries and code not in affected]
    return ordered[:5]


def _assumption_summary(
    event_type: str,
    countries: List[str],
    sectors: List[str],
    severity: str,
    duration_days: int,
) -> str:
    country_text = ", ".join(countries[:5])
    sector_text = ", ".join(sectors[:4]) if sectors else "general"
    return f"{severity} {event_type.lower().replace('_', ' ')} shock affecting {country_text} for {duration_days} days across {sector_text}."


def explain_country_state(country: str, country_engine, metrics: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """Explain the current risk posture for one country engine."""
    metrics = metrics or country_engine._calculate_metrics()
    reactions = country_engine.reaction_history.get(country_engine.current_day, {})
    components = risk_components(metrics, reactions, [agent.politics for agent in country_engine.agents])
    drivers = prediction_drivers(metrics, components)
    confidence = prediction_confidence(
        day=country_engine.current_day,
        agent_count=len(country_engine.agents),
        has_reactions=bool(reactions),
        has_global_tension="global_tension" in metrics,
    )

    return {
        "country": country,
        "day": country_engine.current_day,
        "confidence": confidence,
        "risk_components": components,
        "drivers": drivers,
        "watchlist": watchlist_from_metrics(metrics, components),
    }


def risk_components(
    metrics: Dict[str, float],
    reactions: Dict[str, str],
    politics_values: Optional[List[float]] = None,
) -> Dict[str, Dict[str, float]]:
    cfg = sim_config().get("revolution_risk", {})
    counts = Counter(reactions.values()) if reactions else Counter()
    total = max(len(reactions), 1)
    polarization = float(np.std(politics_values)) if politics_values else 0.0
    raw = {
        "low_trust": 1 - float(metrics.get("social_cohesion", 0.5)),
        "fear": counts.get(ReactionTypes.FEAR, 0) / total if reactions else 0.0,
        "opposition": counts.get(ReactionTypes.OPPOSITION, 0) / total if reactions else 0.0,
        "polarization": min(1.0, polarization / 0.5),
    }
    weights = {
        "low_trust": cfg.get("trust_weight", 0.3),
        "fear": cfg.get("fear_weight", 0.25),
        "opposition": cfg.get("opposition_weight", 0.25),
        "polarization": cfg.get("polarization_weight", 0.2),
    }
    return {
        key: {
            "value": round(_clamp(value), 4),
            "weight": round(float(weights[key]), 4),
            "contribution": round(_clamp(value) * float(weights[key]), 4),
        }
        for key, value in raw.items()
    }


def prediction_drivers(metrics: Dict[str, float], components: Dict[str, Dict[str, float]]) -> List[Dict[str, Any]]:
    candidates = [
        {
            "name": "Low institutional trust",
            "direction": "negative",
            "score": components["low_trust"]["contribution"],
            "detail": f"Social cohesion is {metrics.get('social_cohesion', 0.5) * 100:.1f}%.",
        },
        {
            "name": "Fear reaction load",
            "direction": "negative",
            "score": components["fear"]["contribution"],
            "detail": f"Fear reactions contribute {components['fear']['contribution'] * 100:.1f} risk points.",
        },
        {
            "name": "Opposition reaction load",
            "direction": "negative",
            "score": components["opposition"]["contribution"],
            "detail": f"Opposition reactions contribute {components['opposition']['contribution'] * 100:.1f} risk points.",
        },
        {
            "name": "Political polarization",
            "direction": "negative",
            "score": components["polarization"]["contribution"],
            "detail": f"Polarization component is {components['polarization']['value'] * 100:.1f}%.",
        },
        {
            "name": "Economic sentiment",
            "direction": "positive" if metrics.get("economic_sentiment", 0.5) >= 0.5 else "negative",
            "score": abs(metrics.get("economic_sentiment", 0.5) - 0.5),
            "detail": f"Economic sentiment is {metrics.get('economic_sentiment', 0.5) * 100:.1f}%.",
        },
    ]
    return sorted(candidates, key=lambda item: item["score"], reverse=True)[:4]


def prediction_confidence(day: int, agent_count: int, has_reactions: bool, has_global_tension: bool) -> Dict[str, Any]:
    score = 0.5
    reasons = []
    if agent_count >= 500:
        score += 0.12
        reasons.append("large agent sample")
    if day >= 3:
        score += 0.1
        reasons.append("multi-day state history")
    else:
        reasons.append("early-run state")
    if has_reactions:
        score += 0.12
        reasons.append("recent reaction data")
    else:
        score -= 0.08
        reasons.append("no current-day reactions")
    if has_global_tension:
        score += 0.04
        reasons.append("global tension included")
    score = round(_clamp(score), 2)
    return {"score": score, "level": _level(score), "reasons": reasons}


def watchlist_from_metrics(metrics: Dict[str, float], components: Dict[str, Dict[str, float]]) -> List[str]:
    watchlist = []
    if metrics.get("social_cohesion", 1) < 0.45:
        watchlist.append("institutional trust")
    if metrics.get("economic_sentiment", 1) < 0.45:
        watchlist.append("economic sentiment")
    if metrics.get("average_risk_aversion", 0) > 0.58:
        watchlist.append("fear/risk aversion")
    if components.get("polarization", {}).get("value", 0) > 0.55:
        watchlist.append("political polarization")
    if metrics.get("global_tension", 0) > 0.5:
        watchlist.append("global tension spillover")
    return watchlist or ["baseline drift"]


def scenario_deltas(
    baseline_state: Dict[str, Dict[str, float]],
    final_state: Dict[str, Dict[str, float]],
) -> Dict[str, Dict[str, Dict[str, float]]]:
    deltas: Dict[str, Dict[str, Dict[str, float]]] = {}
    for country, final_metrics in final_state.items():
        base_metrics = baseline_state.get(country, {})
        deltas[country] = {}
        for key, final_value in final_metrics.items():
            if not isinstance(final_value, (int, float)):
                continue
            base_value = float(base_metrics.get(key, 0.0))
            delta = float(final_value) - base_value
            deltas[country][key] = {
                "baseline": round(base_value, 4),
                "scenario": round(float(final_value), 4),
                "delta": round(delta, 4),
            }
    return deltas


def scenario_top_impacts(
    deltas: Dict[str, Dict[str, Dict[str, float]]],
    limit: int = 8,
) -> List[Dict[str, Any]]:
    rows = []
    for country, country_deltas in deltas.items():
        risk_delta = country_deltas.get("revolution_risk", {}).get("delta", 0.0)
        stability_delta = country_deltas.get("political_stability", {}).get("delta", 0.0)
        optimism_delta = country_deltas.get("average_optimism", {}).get("delta", 0.0)
        rows.append({
            "country": country,
            "risk_delta": round(risk_delta, 4),
            "stability_delta": round(stability_delta, 4),
            "optimism_delta": round(optimism_delta, 4),
            "severity": round(abs(risk_delta) + abs(stability_delta) * 0.5 + abs(optimism_delta) * 0.35, 4),
            "direction": _direction(risk_delta, lower_is_better=True),
        })
    return sorted(rows, key=lambda row: row["severity"], reverse=True)[:limit]


def scenario_country_explanations(
    deltas: Dict[str, Dict[str, Dict[str, float]]],
    limit: int = 5,
) -> List[Dict[str, Any]]:
    explanations = []
    for impact in scenario_top_impacts(deltas, limit=limit):
        country = impact["country"]
        country_deltas = deltas.get(country, {})
        driver_rows = []
        for metric, label, lower_is_better in [
            ("revolution_risk", "Revolution risk", True),
            ("political_stability", "Political stability", False),
            ("average_optimism", "Optimism", False),
            ("social_cohesion", "Institutional trust", False),
            ("economic_sentiment", "Economic sentiment", False),
        ]:
            row = country_deltas.get(metric)
            if not row:
                continue
            delta = row["delta"]
            if abs(delta) < 0.002:
                continue
            driver_rows.append({
                "metric": metric,
                "label": label,
                "delta": delta,
                "direction": _direction(delta, lower_is_better=lower_is_better),
            })
        explanations.append({
            "country": country,
            "drivers": sorted(driver_rows, key=lambda row: abs(row["delta"]), reverse=True)[:3],
            "summary": _scenario_summary(country, driver_rows),
        })
    return explanations


def _scenario_summary(country: str, drivers: List[Dict[str, Any]]) -> str:
    if not drivers:
        return f"{country} stays close to baseline."
    lead = max(drivers, key=lambda row: abs(row["delta"]))
    sign = "rises" if lead["delta"] > 0 else "falls"
    return f"{country}: {lead['label']} {sign} by {abs(lead['delta']) * 100:.1f} points versus baseline."
