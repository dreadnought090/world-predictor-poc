import { useParams, Link } from 'react-router-dom'
import { useState } from 'react'
import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { ScatterChart, Scatter, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import client from '../api/client'
import { COUNTRIES, CHART_COLORS } from '../constants/countries'
import { SkeletonCard } from '../components/common/Skeleton'

interface Agent {
  demographics: {
    race: string
    religion: string
    education: string
    age: number
    iq: number
    gender: string
  }
  economic: {
    income: number
    financial_stability: number
  }
  politics: number
  behavior: {
    optimism: number
    trust_institutions: number
    risk_aversion: number
  }
  dominant_reaction?: string
}

function useAgents(country: string, limit: number) {
  return useQuery<{ agents: Agent[]; count: number }>({
    queryKey: ['agents', country, limit],
    queryFn: () => client.get(`/agents/${country}?limit=${limit}`).then(r => r.data),
    enabled: !!country,
  })
}

const pct = (v: number) => `${(v * 100).toFixed(0)}%`
const polLabel = (p: number) => p < -0.5 ? 'Far Left' : p < -0.1 ? 'Left' : p < 0.1 ? 'Center' : p < 0.5 ? 'Right' : 'Far Right'
const polColor = (p: number) => p < -0.3 ? '#3b82f6' : p < 0 ? '#60a5fa' : p < 0.1 ? '#94a3b8' : p < 0.4 ? '#f97316' : '#ef4444'

const REACTION_COLORS: Record<string, string> = {
  SUPPORT: '#22c55e', OPPOSITION: '#f97316', FEAR: '#ef4444', CONFUSION: '#a855f7', APATHY: '#64748b',
}

export default function AgentExplorerPage() {
  const { code } = useParams<{ code: string }>()
  const [limit] = useState(100)
  const { data, isLoading } = useAgents(code!, limit)
  const country = COUNTRIES[code!]

  if (isLoading) return (
    <div className="grid grid-cols-3 gap-4 mt-4">{Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)}</div>
  )

  const agents = data?.agents ?? []
  if (agents.length === 0) return <div className="text-center text-slate-500 mt-12">No agents found</div>

  // Scatter plot data
  const scatterData = agents.map((a, i) => ({
    id: i,
    politics: +a.politics.toFixed(2),
    optimism: +(a.behavior.optimism * 100).toFixed(1),
    trust: +(a.behavior.trust_institutions * 100).toFixed(1),
    iq: a.demographics.iq,
    age: a.demographics.age,
    reaction: a.dominant_reaction || 'APATHY',
    education: a.demographics.education,
  }))

  // Stats
  const avgIQ = (agents.reduce((s, a) => s + a.demographics.iq, 0) / agents.length).toFixed(0)
  const avgIncome = (agents.reduce((s, a) => s + a.economic.income, 0) / agents.length).toFixed(0)
  const avgOptimism = (agents.reduce((s, a) => s + a.behavior.optimism, 0) / agents.length)
  const avgTrust = (agents.reduce((s, a) => s + a.behavior.trust_institutions, 0) / agents.length)

  // Education distribution
  const eduCounts: Record<string, number> = {}
  agents.forEach(a => { eduCounts[a.demographics.education] = (eduCounts[a.demographics.education] || 0) + 1 })

  // Religion distribution
  const relCounts: Record<string, number> = {}
  agents.forEach(a => { relCounts[a.demographics.religion] = (relCounts[a.demographics.religion] || 0) + 1 })

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col gap-4">
      {/* Back + Header */}
      <div className="flex items-center gap-4">
        <Link to={`/country/${code}`} className="text-xs text-slate-500 hover:text-accent transition-colors">&larr; Country Detail</Link>
      </div>

      <div className="flex items-center gap-4 mb-2">
        <span className="text-4xl">{country?.flag}</span>
        <div>
          <h2 className="text-2xl font-bold">{country?.name || code} — Agent Explorer</h2>
          <span className="text-xs text-slate-500 font-mono">{agents.length} agents sampled</span>
        </div>
      </div>

      {/* Quick stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: 'Avg IQ', value: avgIQ, color: '#60a5fa' },
          { label: 'Avg Income', value: `$${Number(avgIncome).toLocaleString()}`, color: '#34d399' },
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
              formatter={(v: any, name: string) => [name === 'Politics' ? (Number(v) > 0 ? 'Right ' : 'Left ') + Math.abs(Number(v)).toFixed(2) : `${v}%`, name]}
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
          {agents.slice(0, 30).map((a, i) => (
            <div key={i} className="bg-bg2 rounded-lg p-3 text-[10px]">
              <div className="flex items-center justify-between mb-1.5">
                <span className="font-bold text-xs">Agent #{i + 1}</span>
                <span className="px-1.5 py-0.5 rounded text-[8px] font-bold" style={{
                  color: polColor(a.politics),
                  background: polColor(a.politics) + '18',
                }}>{polLabel(a.politics)}</span>
              </div>
              <div className="space-y-0.5 text-slate-400">
                <div>Age: <span className="text-slate-300 font-mono">{a.demographics.age}</span> | IQ: <span className="text-slate-300 font-mono">{a.demographics.iq}</span></div>
                <div>Edu: <span className="text-slate-300">{a.demographics.education.replace(/_/g, ' ')}</span></div>
                <div>Income: <span className="text-slate-300 font-mono">${a.economic.income.toLocaleString()}</span></div>
                <div className="flex gap-2 mt-1">
                  <span>Opt: <span className="font-mono" style={{ color: '#fbbf24' }}>{pct(a.behavior.optimism)}</span></span>
                  <span>Trust: <span className="font-mono" style={{ color: '#34d399' }}>{pct(a.behavior.trust_institutions)}</span></span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  )
}
