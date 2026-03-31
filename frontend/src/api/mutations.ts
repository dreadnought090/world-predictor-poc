import { useMutation, useQueryClient } from '@tanstack/react-query'
import client from './client'

export function useFetchNews() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => client.post('/fetch_news'),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['predictions'] })
      qc.invalidateQueries({ queryKey: ['events'] })
      qc.invalidateQueries({ queryKey: ['news'] })
      qc.invalidateQueries({ queryKey: ['history'] })
    },
  })
}

export function useSimulateBatch() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (days: number) => client.post(`/simulate/batch?days=${days}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['predictions'] })
      qc.invalidateQueries({ queryKey: ['history'] })
    },
  })
}

export function useInjectPresetEvent() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (name: string) => client.post(`/events/preset/${name}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['events'] })
    },
  })
}

export function useEnactPolicy() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ country, policy }: { country: string; policy: string }) =>
      client.post(`/policies/enact?country=${country}&policy_name=${policy}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['predictions'] })
    },
  })
}

export function useRunScenario() {
  return useMutation({
    mutationFn: (params: { name: string; description?: string; preset_event?: string; preset_policy?: string; policy_country?: string; days?: number }) =>
      client.post('/scenarios/run', null, { params }).then(r => r.data),
  })
}
