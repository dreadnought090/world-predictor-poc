import { useQuery } from '@tanstack/react-query'
import client from './client'
import type { Prediction, CountryProfile, HistoryEntry, GeoEvent, NewsItem, PresetEvent, PresetPolicy } from '../types'

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
  return useQuery<{ signals: { country: string; currency: string; rate_to_usd: number; strength: number }[] }>({
    queryKey: ['market', 'signals'],
    queryFn: () => client.get('/market/signals').then(r => r.data),
    refetchInterval: 60000,
    retry: false,
  })
}

export function useRelations(country: string) {
  return useQuery({
    queryKey: ['relations', country],
    queryFn: () => client.get(`/relations/${country}`).then(r => r.data),
    enabled: !!country,
  })
}
