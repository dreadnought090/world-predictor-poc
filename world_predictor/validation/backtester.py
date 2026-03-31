"""Validation & Backtesting Framework.

Compare simulation predictions against historical events.
Provides accuracy metrics and calibration scoring.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class HistoricalEvent:
    """A known historical event for validation."""
    name: str
    country: str
    date: str
    event_type: str
    actual_impact: str        # "high", "medium", "low"
    description: str = ""


# Known historical events for validation
HISTORICAL_EVENTS = [
    HistoricalEvent("Arab Spring - Egypt", "EG", "2011-01-25", "CIVIL_UNREST", "high",
                    "Mass protests leading to Mubarak's resignation"),
    HistoricalEvent("Arab Spring - Tunisia", "TN", "2010-12-17", "CIVIL_UNREST", "high",
                    "Revolution leading to Ben Ali's overthrow"),
    HistoricalEvent("Brexit Vote", "GB", "2016-06-23", "ELECTION", "high",
                    "UK votes to leave European Union"),
    HistoricalEvent("2008 Financial Crisis", "US", "2008-09-15", "ECONOMIC_CRISIS", "high",
                    "Lehman Brothers collapse triggers global recession"),
    HistoricalEvent("COVID-19 Pandemic", "CN", "2020-01-23", "PANDEMIC", "high",
                    "Wuhan lockdown begins global pandemic"),
    HistoricalEvent("Russia-Ukraine War", "RU", "2022-02-24", "WAR", "high",
                    "Russia invades Ukraine"),
    HistoricalEvent("Myanmar Coup", "MM", "2021-02-01", "COUP", "high",
                    "Military seizes power from elected government"),
    HistoricalEvent("Sri Lanka Economic Crisis", "LK", "2022-04-12", "ECONOMIC_CRISIS", "high",
                    "Sovereign debt default and mass protests"),
    HistoricalEvent("Turkish Lira Crisis", "TR", "2018-08-10", "ECONOMIC_CRISIS", "medium",
                    "Currency lost 30% of value in days"),
    HistoricalEvent("US Capitol Riot", "US", "2021-01-06", "CIVIL_UNREST", "medium",
                    "Storming of US Capitol building"),
    HistoricalEvent("Hong Kong Protests", "CN", "2019-06-09", "CIVIL_UNREST", "medium",
                    "Mass pro-democracy protests"),
    HistoricalEvent("Indian Farmer Protests", "IN", "2020-11-26", "CIVIL_UNREST", "medium",
                    "Year-long protests against agricultural reform"),
    HistoricalEvent("Brazil Bolsonaro Riot", "BR", "2023-01-08", "CIVIL_UNREST", "medium",
                    "Supporters storm government buildings"),
    HistoricalEvent("French Yellow Vests", "FR", "2018-11-17", "CIVIL_UNREST", "medium",
                    "Nationwide protests against fuel tax"),
    HistoricalEvent("Japanese Yen Collapse", "JP", "2022-10-21", "ECONOMIC_CRISIS", "medium",
                    "Yen drops to 32-year low against dollar"),
]


@dataclass
class ValidationResult:
    """Result of validating predictions against actual outcomes."""
    event_name: str
    country: str
    predicted_risk_before: float     # revolution risk N days before event
    predicted_risk_at_event: float   # revolution risk on event day
    actual_severity: str
    risk_increase_detected: bool     # did the model see rising risk?
    days_of_warning: int             # how many days before did risk start rising?
    score: float                     # 0-1 accuracy score


class Backtester:
    """Run historical validation against known events."""

    def __init__(self):
        self.results: List[ValidationResult] = []

    def validate_scenario(
        self,
        scenario_results: Dict,
        event: HistoricalEvent,
        lookback_days: int = 14,
    ) -> ValidationResult:
        """Validate a scenario run against a known historical event.

        Checks if the simulation's revolution risk / instability metrics
        correctly predicted the event.
        """
        country = event.country
        daily = scenario_results.get("daily_results", [])

        # Get revolution risk trajectory
        risk_series = []
        for day_data in daily:
            if country in day_data:
                risk = day_data[country].get("metrics", {}).get("revolution_risk", 0)
                risk_series.append(risk)

        if not risk_series:
            return ValidationResult(
                event_name=event.name, country=country,
                predicted_risk_before=0, predicted_risk_at_event=0,
                actual_severity=event.actual_impact,
                risk_increase_detected=False, days_of_warning=0, score=0.0,
            )

        # Analyze risk trajectory
        final_risk = risk_series[-1]
        early_risk = risk_series[0] if risk_series else 0

        # Was there a rising trend?
        risk_increase = final_risk > early_risk + 0.05

        # How many days before the peak did risk start rising?
        warning_days = 0
        threshold = early_risk + 0.03
        for i, r in enumerate(risk_series):
            if r > threshold:
                warning_days = len(risk_series) - i
                break

        # Score: high-severity events should have high final risk
        severity_map = {"high": 0.6, "medium": 0.4, "low": 0.2}
        expected_min = severity_map.get(event.actual_impact, 0.3)

        if final_risk >= expected_min:
            score = min(1.0, final_risk / expected_min)
        else:
            score = final_risk / expected_min

        # Bonus for early warning
        if warning_days > 7:
            score = min(1.0, score + 0.1)

        result = ValidationResult(
            event_name=event.name, country=country,
            predicted_risk_before=round(early_risk, 4),
            predicted_risk_at_event=round(final_risk, 4),
            actual_severity=event.actual_impact,
            risk_increase_detected=risk_increase,
            days_of_warning=warning_days,
            score=round(score, 4),
        )
        self.results.append(result)
        return result

    def get_accuracy_summary(self) -> Dict[str, Any]:
        """Get overall accuracy metrics."""
        if not self.results:
            return {"total": 0, "average_score": 0}

        scores = [r.score for r in self.results]
        detected = sum(1 for r in self.results if r.risk_increase_detected)

        return {
            "total_events": len(self.results),
            "average_score": round(sum(scores) / len(scores), 4),
            "detection_rate": round(detected / len(self.results), 4),
            "high_severity_score": self._score_by_severity("high"),
            "medium_severity_score": self._score_by_severity("medium"),
            "results": [
                {
                    "event": r.event_name,
                    "country": r.country,
                    "score": r.score,
                    "detected": r.risk_increase_detected,
                    "warning_days": r.days_of_warning,
                }
                for r in self.results
            ],
        }

    def _score_by_severity(self, severity: str) -> float:
        filtered = [r for r in self.results if r.actual_severity == severity]
        if not filtered:
            return 0.0
        return round(sum(r.score for r in filtered) / len(filtered), 4)

    @staticmethod
    def get_historical_events() -> List[Dict]:
        """Get list of available historical events for validation."""
        return [
            {
                "name": e.name,
                "country": e.country,
                "date": e.date,
                "type": e.event_type,
                "severity": e.actual_impact,
            }
            for e in HISTORICAL_EVENTS
        ]
