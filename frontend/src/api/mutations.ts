import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import client from './client'

export function useFetchNews() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => client.post('/fetch_news'),
    onSuccess: () => {
      toast.success('News fetched & simulation updated')
      qc.invalidateQueries({ queryKey: ['predictions'] })
      qc.invalidateQueries({ queryKey: ['events'] })
      qc.invalidateQueries({ queryKey: ['news'] })
      qc.invalidateQueries({ queryKey: ['history'] })
      qc.invalidateQueries({ queryKey: ['global'] })
    },
    onError: () => toast.error('Failed to fetch news'),
  })
}

export function useSimulateBatch() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (days: number) => client.post(`/simulate/batch?days=${days}`),
    onSuccess: (_data, days) => {
      toast.success(`Simulated ${days} days`)
      qc.invalidateQueries({ queryKey: ['predictions'] })
      qc.invalidateQueries({ queryKey: ['history'] })
      qc.invalidateQueries({ queryKey: ['global'] })
    },
    onError: () => toast.error('Simulation failed'),
  })
}

export function useInjectPresetEvent() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (name: string) => client.post(`/events/preset/${name}`),
    onSuccess: (_data, name) => {
      toast.success(`Event injected: ${name.replace(/_/g, ' ')}`)
      qc.invalidateQueries({ queryKey: ['events'] })
      qc.invalidateQueries({ queryKey: ['predictions'] })
      qc.invalidateQueries({ queryKey: ['global'] })
    },
    onError: () => toast.error('Failed to inject event'),
  })
}

export function useEnactPolicy() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ country, policy }: { country: string; policy: string }) =>
      client.post(`/policies/enact?country=${country}&policy_name=${policy}`),
    onSuccess: (_data, { policy, country }) => {
      toast.success(`Policy enacted: ${policy.replace(/_/g, ' ')} in ${country}`)
      qc.invalidateQueries({ queryKey: ['predictions'] })
      qc.invalidateQueries({ queryKey: ['profile'] })
    },
    onError: () => toast.error('Failed to enact policy'),
  })
}

export function useRunScenario() {
  return useMutation({
    mutationFn: (params: { name: string; description?: string; preset_event?: string; preset_policy?: string; policy_country?: string; days?: number }) =>
      client.post('/scenarios/run', null, { params }).then(r => r.data),
    onSuccess: (_data, params) => {
      toast.success(`Scenario "${params.name}" completed`)
    },
    onError: () => toast.error('Scenario failed'),
  })
}
