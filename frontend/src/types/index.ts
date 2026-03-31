export interface Metrics {
  economic_sentiment: number
  social_cohesion: number
  political_stability: number
  average_optimism: number
  average_risk_aversion: number
  revolution_risk: number
  global_tension?: number
}

export interface Prediction {
  country: string
  day: number
  agent_count: number
  metrics: Metrics
}

export interface DemographicDist {
  label: string
  count: number
  pct: number
}

export interface Consensus {
  economic_policy_support: number
  government_trust: number
  future_optimism: number
  reaction_distribution?: Record<string, number>
}

export interface CountryProfile {
  country: string
  day: number
  agent_count: number
  metrics: Metrics
  consensus?: Consensus
  demographics: {
    race: DemographicDist[]
    religion: DemographicDist[]
    education: DemographicDist[]
    gender: DemographicDist[]
    age: DemographicDist[]
    politics: DemographicDist[]
  }
  biometrics: {
    iq: { mean: number; std: number; min: number; max: number }
    income: { mean: number; median: number; quintiles: number[] }
    age: { mean: number; median: number; min: number; max: number }
    optimism: { mean: number }
    trust: { mean: number }
    risk_aversion: { mean: number }
  }
  institutions: Institution[]
  relations: Relations
  news: NewsItem[]
  history: HistoryEntry[]
}

export interface Institution {
  name: string
  type: string
  politics: number
  credibility: number
  power: number
  active_policies: string[]
}

export interface Relation {
  country: string
  strength: number
}

export interface Relations {
  trade_partners: Relation[]
  allies: Relation[]
  rivals: Relation[]
}

export interface NewsItem {
  title: string
  source_name: string
  source_politics?: number
  source_credibility?: number
  category: string
  region: string
  impact: number
  url?: string
}

export interface HistoryEntry {
  day: number
  economic_sentiment: number
  social_cohesion: number
  political_stability: number
  average_optimism: number
  average_risk_aversion: number
  revolution_risk: number
  dominant_reaction?: string
}

export interface GeoEvent {
  name: string
  type: string
  affected: string[]
  magnitude: number
  days_remaining: number
}

export interface PresetEvent {
  type: string
  name: string
  affected: string[]
  magnitude: number
}

export interface PresetPolicy {
  name: string
  category: string
  magnitude: number
  duration_days: number
}
