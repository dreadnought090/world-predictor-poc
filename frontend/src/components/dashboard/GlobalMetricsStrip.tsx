import MetricCard from '../common/MetricCard'
import type { Prediction } from '../../types'

export default function GlobalMetricsStrip({ data }: { data: Record<string, Prediction> }) {
  const countries = Object.values(data)
  if (!countries.length) return null

  const avg = (key: keyof Prediction['metrics']) =>
    countries.reduce((s, c) => s + (c.metrics[key] ?? 0), 0) / countries.length

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
      <MetricCard label="Optimism" value={avg('average_optimism')} color="#60a5fa" />
      <MetricCard label="Trust" value={avg('social_cohesion')} color="#34d399" />
      <MetricCard label="Stability" value={avg('political_stability')} color="#a78bfa" />
      <MetricCard label="Rev. Risk" value={avg('revolution_risk')} color="#fbbf24" />
      <MetricCard label="Tension" value={avg('global_tension' as keyof Prediction['metrics']) || 0} color="#f87171" />
    </div>
  )
}
