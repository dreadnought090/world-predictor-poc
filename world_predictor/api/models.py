from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from world_predictor.data.news import VALID_CATEGORIES


NewsCategory = Literal[
    "ECONOMIC_POLICY",
    "POLITICAL",
    "SOCIAL",
    "MILITARY",
    "TECHNOLOGY",
    "ENVIRONMENTAL",
    "HEALTH",
    "TRADE",
    "GENERAL",
]


class StrictRequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class NewsRequest(BaseModel):
    sources: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)


class NewsSourceInput(StrictRequestModel):
    name: str = Field(default="Unknown", min_length=1, max_length=120)
    politics: float = Field(default=0.0, ge=-1.0, le=1.0)
    credibility: float = Field(default=0.5, ge=0.0, le=1.0)


class NewsItemInput(StrictRequestModel):
    title: str = Field(min_length=1, max_length=500)
    source: NewsSourceInput = Field(default_factory=NewsSourceInput)
    category: NewsCategory = "GENERAL"
    content: str = Field(default="", max_length=5000)
    url: str = Field(default="", max_length=1000)
    region: str = Field(default="Global", max_length=16)
    impact: float = Field(default=0.1, ge=0.0, le=1.0)

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category(cls, value):
        if value is None:
            return "GENERAL"
        normalized = str(value).strip().upper()
        if normalized not in VALID_CATEGORIES:
            raise ValueError(f"category must be one of {', '.join(VALID_CATEGORIES)}")
        return normalized

    @field_validator("region")
    @classmethod
    def normalize_region(cls, value: str) -> str:
        normalized = value.strip()
        if normalized.lower() == "global":
            return "Global"
        if len(normalized) == 2 and normalized.isalpha():
            return normalized.upper()
        raise ValueError("region must be an ISO alpha-2 country code or Global")


class PredictionResponse(BaseModel):
    country: str
    day: int
    agent_count: int
    metrics: Dict[str, float]


class AgentUpdate(BaseModel):
    id: str
    economic_stability: float
    optimism: float
    trust_institutions: float


class ReactionSummary(BaseModel):
    total_agents: int
    distribution: Dict[str, int]
    percentages: Dict[str, float]
    dominant: str


class CountrySimulationResult(BaseModel):
    country: str
    day: int
    metrics: Dict[str, float]
    consensus: Dict[str, Any]
    reactions: ReactionSummary
    agent_count: int


class SimulationResult(BaseModel):
    day: int
    metrics: Dict[str, float]
    consensus: Dict[str, Any]
    reactions: ReactionSummary
    agent_updates: List[AgentUpdate]
    all_countries: Dict[str, CountrySimulationResult] = Field(default_factory=dict)


class BatchSimulateRequest(BaseModel):
    days: int = Field(default=10, ge=1, le=365)


class NewsSearchRequest(BaseModel):
    category: Optional[str] = None
    region: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=200)


class MarketSignal(BaseModel):
    country: str
    currency: str
    exchange_rate: float
    strength: float


class MarketSignalsResponse(BaseModel):
    base_currency: str
    fetched_at: Optional[str]
    stale: bool
    signals: List[MarketSignal]


class HistoricalEventResponse(BaseModel):
    name: str
    country: str
    date: str
    type: str
    severity: str
    description: str = ""


class BacktestCountryDay(BaseModel):
    day: Optional[int] = None
    metrics: Dict[str, float] = Field(default_factory=dict)
    reactions: Optional[Dict[str, Any]] = None


class BacktestRequest(StrictRequestModel):
    event_name: str = Field(min_length=1)
    scenario_id: Optional[str] = Field(default=None, min_length=1)
    daily_results: Optional[List[Dict[str, BacktestCountryDay]]] = Field(default=None, min_length=1)
    lookback_days: int = Field(default=14, ge=1, le=365)


class ValidationResultResponse(BaseModel):
    event_name: str
    country: str
    predicted_risk_before: float
    predicted_risk_at_event: float
    actual_severity: str
    risk_increase_detected: bool
    days_of_warning: int
    score: float


class BacktestResponse(BaseModel):
    event: HistoricalEventResponse
    result: ValidationResultResponse
    summary: Dict[str, Any]
    source: str
    days_evaluated: int
