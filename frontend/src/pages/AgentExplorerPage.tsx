import { useParams, Link } from 'react-router-dom'
import { useState } from 'react'
import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { ScatterChart, Scatter, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import client from '../api/client'
import { COUNTRIES } from '../constants/countries'
import { SkeletonCard } from '../components/common/Skeleton'

type NumericValue = number | string

interface Agent {
  id?: string
  demographics: {
    race?: string
    religion?: string
    education?: string
    age?: NumericValue
    iq?: NumericValue
    gender?: string
  }
  economic: {
    income?: NumericValue
    financial_stability?: NumericValue
  }
  politics?: NumericValue
  behavior: {
    optimism?: NumericValue
    trust_institutions?: NumericValue
    risk_aversion?: NumericValue
  }
  iq?: NumericValue
  dominant_reaction?: string
}

function useAgents(country: string, limit: number) {
  return useQuery<{ agents: Agent[]; count: number }>({
    queryKey: ['agents', country, limit],
    queryFn: () => client.get(`/agents/${country}?limit=${limit}`).then(r => r.data),
    enabled: !!country,
  })
}

const parseNumber = (value: unknown): number | null => {
  const parsed = typeof value === 'number'
    ? value
    : typeof value === 'string'
      ? Number(value.replace(/,/g, ''))
      : Number.NaN
  return Number.isFinite(parsed) ? parsed : null
}
const toNumber = (value: unknown, fallback = 0) => parseNumber(value) ?? fallback
const clamp01 = (v: number) => Math.max(0, Math.min(1, v))
const pct = (v: unknown) => `${(clamp01(toNumber(v)) * 100).toFixed(0)}%`
const avg = (values: number[]) => values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : 0
const rounded = (value: number, digits = 1) => +value.toFixed(digits)
const label = (value: unknown) => String(value ?? 'unknown').replace(/_/g, ' ')
const whole = (value: unknown) => {
  const parsed = parseNumber(value)
  return parsed === null ? 'n/a' : parsed.toFixed(0)
}
const polLabel = (p: number) => p < -0.5 ? 'Far Left' : p < -0.1 ? 'Left' : p < 0.1 ? 'Center' : p < 0.5 ? 'Right' : 'Far Right'
const polColor = (p: number) => p < -0.3 ? '#3b82f6' : p < 0 ? '#60a5fa' : p < 0.1 ? '#94a3b8' : p < 0.4 ? '#f97316' : '#ef4444'

const REACTION_COLORS: Record<string, string> = {
  SUPPORT: '#22c55e', OPPOSITION: '#f97316', FEAR: '#ef4444', CONFUSION: '#a855f7', APATHY: '#64748b',
}

export default function AgentExplorerPage() {
  const { code } = useParams<{ code: string }>()
  const [limit] = useState(100)
  const selectedCode = code ?? ''
  const { data, isLoading } = useAgents(selectedCode, limit)
  const country = COUNTRIES[selectedCode]

  if (isLoading) return (
    <div className="grid grid-cols-3 gap-4 mt-4">{Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)}</div>
  )

  const agents = data?.agents ?? []
  if (agents.length === 0) return <div className="text-center text-slate-500 mt-12">No agents found</div>

  // Scatter plot data
  const scatterData = agents.map((a, i) => ({
    id: i,
    politics: rounded(toNumber(a.politics), 2),
    optimism: rounded(clamp01(toNumber(a.behavior.optimism)) * 100),
    trust: rounded(clamp01(toNumber(a.behavior.trust_institutions)) * 100),
    iq: toNumber(a.iq ?? a.demographics.iq),
    age: toNumber(a.demographics.age),
    reaction: a.dominant_reaction || 'APATHY',
    education: label(a.demographics.education),
  }))

  // Stats
  const avgIQ = avg(agents.map(a => toNumber(a.iq ?? a.demographics.iq)))
  const avgIncome = avg(agents.map(a => toNumber(a.economic.income)))
  const avgOptimism = avg(agents.map(a => clamp01(toNumber(a.behavior.optimism))))
  const avgTrust = avg(agents.map(a => clamp01(toNumber(a.behavior.trust_institutions))))

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col gap-4">
      {/* Back + Header */}
      <div className="flex items-center gap-4">
        <Link to={`/country/${selectedCode}`} className="text-xs text-slate-500 hover:text-accent transition-colors">&larr; Country Detail</Link>
      </div>

      <div className="flex items-center gap-4 mb-2">
        <span className="text-4xl">{country?.flag}</span>
        <div>
          <h2 className="text-2xl font-bold">{country?.name || selectedCode} - Agent Explorer</h2>
          <span className="text-xs text-slate-500 font-mono">{agents.length} agents sampled</span>
        </div>
      </div>

      {/* Quick stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: 'Avg IQ', value: avgIQ.toFixed(0), color: '#60a5fa' },
          { label: 'Avg Income', value: `$${avgIncome.toLocaleString(undefined, { maximumFractionDigits: 0 })}`, color: '#34d399' },
          { label: 'Avg Optimism', value: pct(avgOptimism), color: '#fbbf24' },
          { label: 'Avg Trust', value: pct(avgTrust), color: '#a78bfa' },
        ].map((s, i) => (
          <div key={i} className="glass p-4 text-center">
            <div className="text-lg font-bold font-mono" style={{ color: s.color }}>{s.value}</div>
            <div className="text-[9px] text-slate-500 uppercase mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Scatter: Politics vs Optimism */}
      <div className="glass p-5">
        <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-3">
          Political Position vs Optimism
          <span className="text-slate-600 normal-case ml-2">(colored by dominant reaction)</span>
        </h3>
        <ResponsiveContainer width="100%" height={350}>
          <ScatterChart>
            <XAxis
              dataKey="politics" name="Politics" type="number" domain={[-1, 1]}
              tick={{ fill: '#64748b', fontSize: 10 }}
              label={{ value: 'Left ← Politics → Right', position: 'bottom', fill: '#64748b', fontSize: 10, offset: -5 }}
            />
            <YAxis
              dataKey="optimism" name="Optimism" unit="%"
              tick={{ fill: '#64748b', fontSize: 10 }}
              label={{ value: 'Optimism %', angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 10 }}
            />
            <Tooltip
              contentStyle={{ background: '#1a2332', border: '1px solid #334155', borderRadius: 8, fontSize: 11 }}
              formatter={(v: unknown, name: unknown): [string, string] => {
                const metric = String(name)
                const value = toNumber(v)
                return [
                  metric === 'Politics'
                    ? `${value > 0 ? 'Right' : value < 0 ? 'Left' : 'Center'} ${Math.abs(value).toFixed(2)}`
                    : `${value.toFixed(1)}%`,
                  metric,
                ]
              }}
              labelFormatter={() => ''}
            />
            <Scatter data={scatterData}>
              {scatterData.map((d, i) => (
                <Cell key={i} fill={REACTION_COLORS[d.reaction] || '#64748b'} fillOpacity={0.7} />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
        <div className="flex flex-wrap gap-3 mt-2">
          {Object.entries(REACTION_COLORS).map(([r, c]) => (
            <span key={r} className="flex items-center gap-1 text-[10px]">
              <span className="w-2 h-2 rounded-full" style={{ background: c }} />
              <span className="text-slate-400">{r}</span>
            </span>
          ))}
        </div>
      </div>

      {/* Agent Cards Grid */}
      <div className="glass p-5">
        <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-3">Individual Agents (first 30)</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2 max-h-[500px] overflow-y-auto">
          {agents.slice(0, 30).map((a, i) => {
            const politics = toNumber(a.politics)
            return (
              <div key={a.id ?? i} className="bg-bg2 rounded-lg p-3 text-[10px]">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="font-bold text-xs">Agent #{i + 1}</span>
                  <span className="px-1.5 py-0.5 rounded text-[8px] font-bold" style={{
                    color: polColor(politics),
                    background: polColor(politics) + '18',
                  }}>{polLabel(politics)}</span>
                </div>
                <div className="space-y-0.5 text-slate-400">
                  <div>Age: <span className="text-slate-300 font-mono">{whole(a.demographics.age)}</span> | IQ: <span className="text-slate-300 font-mono">{whole(a.iq ?? a.demographics.iq)}</span></div>
                  <div>Edu: <span className="text-slate-300">{label(a.demographics.education)}</span></div>
                  <div>Income: <span className="text-slate-300 font-mono">${toNumber(a.economic.income).toLocaleString(undefined, { maximumFractionDigits: 0 })}</span></div>
                  <div className="flex gap-2 mt-1">
                    <span>Opt: <span className="font-mono" style={{ color: '#fbbf24' }}>{pct(a.behavior.optimism)}</span></span>
                    <span>Trust: <span className="font-mono" style={{ color: '#34d399' }}>{pct(a.behavior.trust_institutions)}</span></span>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </motion.div>
  )
}
