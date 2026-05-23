import { useQuery } from '@tanstack/react-query'
import client from './client'
import type {
  Prediction,
  CountryProfile,
  HistoryEntry,
  GeoEvent,
  NewsItem,
  PresetEvent,
  PresetPolicy,
  MarketSignal,
  RelationEdge,
  Relations,
  RelationKind,
} from '../types'

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value)

const toNumber = (value: unknown, fallback = 0) => {
  const parsed = typeof value === 'number'
    ? value
    : typeof value === 'string'
      ? Number(value.replace(/,/g, ''))
      : Number.NaN
  return Number.isFinite(parsed) ? parsed : fallback
}

const clamp01 = (value: number) => Math.max(0, Math.min(1, value))

function normalizeMarketSignal(countryKey: string | undefined, value: unknown): MarketSignal | null {
  if (!isRecord(value)) return null

  const country = String(value.country ?? countryKey ?? '').trim().toUpperCase()
  if (!country || country === 'ERROR') return null

  return {
    country,
    currency: String(value.currency ?? value.currency_code ?? 'USD').toUpperCase(),
    exchangeRate: toNumber(value.rate_to_usd ?? value.exchange_rate),
    strength: clamp01(toNumber(value.strength ?? value.currency_strength, 0.5)),
  }
}

function normalizeMarketSignals(payload: unknown): MarketSignal[] {
  if (isRecord(payload) && typeof payload.error === 'string') {
    throw new Error(payload.error)
  }

  const rows: Array<[string | undefined, unknown]> = []

  if (Array.isArray(payload)) {
    rows.push(...payload.map(item => [undefined, item] as [undefined, unknown]))
  } else if (isRecord(payload) && Array.isArray(payload.signals)) {
    rows.push(...payload.signals.map(item => [undefined, item] as [undefined, unknown]))
  } else if (isRecord(payload) && isRecord(payload.signals)) {
    rows.push(...Object.entries(payload.signals))
  } else if (isRecord(payload)) {
    rows.push(...Object.entries(payload))
  }

  return rows
    .map(([country, signal]) => normalizeMarketSignal(country, signal))
    .filter((signal): signal is MarketSignal => signal !== null)
}

const relationBuckets: Array<[keyof Relations, RelationKind]> = [
  ['trade_partners', 'TRADE'],
  ['allies', 'ALLIANCE'],
  ['rivals', 'RIVALRY'],
]

function normalizeRelations(country: string, payload: unknown): RelationEdge[] {
  if (!isRecord(payload)) return []

  const edges = new Map<string, RelationEdge>()
  relationBuckets.forEach(([bucket, type]) => {
    const rows = payload[bucket]
    if (!Array.isArray(rows)) return

    rows.forEach(row => {
      if (!isRecord(row)) return
      const partner = String(row.country ?? '').trim().toUpperCase()
      if (!partner || partner === country) return

      const [a, b] = [country, partner].sort()
      const key = `${type}:${a}:${b}`
      edges.set(key, {
        a,
        b,
        type,
        strength: clamp01(toNumber(row.strength, 0)),
      })
    })
  })

  return Array.from(edges.values())
}

export function useAllPredictions() {
  return useQuery<Record<string, Prediction>>({
    queryKey: ['predictions'],
    queryFn: () => client.get('/predictions').then(r => r.data),
    refetchInterval: 15000,
  })
}

export function useCountryProfile(code: string) {
  return useQuery<CountryProfile>({
    queryKey: ['profile', code],
    queryFn: () => client.get(`/country/${code}/profile`).then(r => r.data),
    enabled: !!code,
    refetchInterval: 20000,
  })
}

export function useHistory(country: string, days = 50) {
  return useQuery<{ country: string; days: number; history: HistoryEntry[] }>({
    queryKey: ['history', country, days],
    queryFn: () => client.get(`/history/${country}?days=${days}`).then(r => r.data),
    enabled: !!country,
  })
}

export function useActiveEvents() {
  return useQuery<{ active_events: GeoEvent[] }>({
    queryKey: ['events', 'active'],
    queryFn: () => client.get('/events/active').then(r => r.data),
    refetchInterval: 15000,
  })
}

export function useNewsArchive(limit = 25) {
  return useQuery<{ results: NewsItem[]; stats: Record<string, unknown> }>({
    queryKey: ['news', limit],
    queryFn: () => client.get(`/news/archive?limit=${limit}`).then(r => r.data),
    refetchInterval: 30000,
  })
}

export function useGlobalTension() {
  return useQuery<{ global_tension_index: number }>({
    queryKey: ['global', 'tension'],
    queryFn: () => client.get('/global/tension').then(r => r.data),
    refetchInterval: 15000,
  })
}

export function usePresetEvents() {
  return useQuery<Record<string, PresetEvent>>({
    queryKey: ['presets', 'events'],
    queryFn: () => client.get('/presets/events').then(r => r.data),
    staleTime: Infinity,
  })
}

export function usePresetPolicies() {
  return useQuery<Record<string, PresetPolicy>>({
    queryKey: ['presets', 'policies'],
    queryFn: () => client.get('/presets/policies').then(r => r.data),
    staleTime: Infinity,
  })
}

export function useMarketSignals() {
  return useQuery<MarketSignal[]>({
    queryKey: ['market', 'signals'],
    queryFn: () => client.get('/market/signals').then(r => normalizeMarketSignals(r.data)),
    refetchInterval: 60000,
    retry: false,
  })
}

export function useRelations(country: string) {
  return useQuery<Relations>({
    queryKey: ['relations', country],
    queryFn: () => client.get(`/relations/${country}`).then(r => r.data),
    enabled: !!country,
  })
}

export function useRelationsNetwork(countries: string[]) {
  const normalizedCountries = countries.map(country => country.toUpperCase()).sort()

  return useQuery<RelationEdge[]>({
    queryKey: ['relations', 'network', normalizedCountries],
    queryFn: async () => {
      const responses = await Promise.all(
        normalizedCountries.map(country =>
          client.get(`/relations/${country}`).then(r => [country, r.data] as const)
        )
      )

      const edges = new Map<string, RelationEdge>()
      responses.forEach(([country, payload]) => {
        normalizeRelations(country, payload).forEach(edge => {
          const key = `${edge.type}:${edge.a}:${edge.b}`
          edges.set(key, edge)
        })
      })
      return Array.from(edges.values())
    },
    enabled: normalizedCountries.length > 0,
    staleTime: 60000,
    retry: false,
  })
}
