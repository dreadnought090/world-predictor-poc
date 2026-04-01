import { motion } from 'framer-motion'
import { COUNTRIES } from '../constants/countries'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, RadarChart, PolarGrid, PolarAngleAxis, Radar, Legend } from 'recharts'

const pct = (v: number) => `${(v * 100).toFixed(1)}%`
const delta = (a: number, b: number) => {
  const d = (b - a) * 100
  const sign = d > 0 ? '+' : ''
  return { text: `${sign}${d.toFixed(1)}%`, color: d > 0 ? '#22c55e' : d < 0 ? '#ef4444' : '#64748b' }
}

interface ScenarioResult {
  name: string
  scenario_id: string
  days_simulated: number
  events_injected: string[]
  policies_injected: string[]
  final_state: Record<string, any>
}

export default function ScenarioComparePage({ scenarios }: { scenarios: ScenarioResult[] }) {
  if (scenarios.length < 2) {
    return (
      <div className="glass p-8 text-center">
        <p className="text-slate-400 text-sm">Run at least 2 scenarios to compare them.</p>
        <p className="text-slate-500 text-xs mt-2">Go to the Scenario Builder above and run different what-if scenarios.</p>
      </div>
    )
  }

  const a = scenarios[scenarios.length - 2]
  const b = scenarios[scenarios.length - 1]
  const countries = Object.keys(a.final_state || {}).filter(c => b.final_state?.[c])

  const metrics = ['average_optimism', 'social_cohesion', 'political_stability', 'revolution_risk'] as const
  const metricLabels: Record<string, string> = {
    average_optimism: 'Optimism',
    social_cohesion: 'Trust',
    political_stability: 'Stability',
    revolution_risk: 'Rev. Risk',
  }

  // Radar data: average across all countries per metric
  const n = countries.length || 1
  const radarData = metrics.map(m => ({
    metric: metricLabels[m],
    [a.name]: +(countries.reduce((s, c) => s + (a.final_state[c]?.[m] || 0), 0) / n * 100).toFixed(1),
    [b.name]: +(countries.reduce((s, c) => s + (b.final_state[c]?.[m] || 0), 0) / n * 100).toFixed(1),
  }))

  // Delta bar chart: show revolution risk delta per country
  const deltaData = countries.map(c => {
    const riskA = a.final_state[c]?.revolution_risk || 0
    const riskB = b.final_state[c]?.revolution_risk || 0
    return { country: c, flag: COUNTRIES[c]?.flag || '', delta: +((riskB - riskA) * 100).toFixed(1) }
  }).sort((x, y) => y.delta - x.delta)

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col gap-4">
      {/* Header */}
      <div className="glass p-5">
        <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-4">Scenario Comparison</h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-bg2 rounded-lg p-3">
            <div className="text-xs font-bold text-blue-400">A: {a.name}</div>
            <div className="text-[9px] text-slate-500 mt-1">{a.days_simulated} days | Events: {a.events_injected?.join(', ') || 'none'} | Policies: {a.policies_injected?.join(', ') || 'none'}</div>
          </div>
          <div className="bg-bg2 rounded-lg p-3">
            <div className="text-xs font-bold text-purple-400">B: {b.name}</div>
            <div className="text-[9px] text-slate-500 mt-1">{b.days_simulated} days | Events: {b.events_injected?.join(', ') || 'none'} | Policies: {b.policies_injected?.join(', ') || 'none'}</div>
          </div>
        </div>
      </div>

      {/* Radar Chart */}
      <div className="glass p-5">
        <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-3">Global Average Comparison</h3>
        <ResponsiveContainer width="100%" height={300}>
          <RadarChart data={radarData}>
            <PolarGrid stroke="#334155" />
            <PolarAngleAxis dataKey="metric" tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <Radar name={a.name} dataKey={a.name} stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.15} strokeWidth={2} />
            <Radar name={b.name} dataKey={b.name} stroke="#a855f7" fill="#a855f7" fillOpacity={0.15} strokeWidth={2} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            <Tooltip contentStyle={{ background: '#1a2332', border: '1px solid #334155', borderRadius: 8, fontSize: 11 }} />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Revolution Risk Delta */}
      <div className="glass p-5">
        <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-3">
          Revolution Risk Change (B vs A)
        </h3>
        <ResponsiveContainer width="100%" height={Math.max(200, deltaData.length * 28)}>
          <BarChart data={deltaData} layout="vertical" margin={{ left: 50 }}>
            <XAxis type="number" tickFormatter={v => `${v > 0 ? '+' : ''}${v}%`} tick={{ fill: '#64748b', fontSize: 10 }} />
            <YAxis type="category" dataKey="country" tick={{ fill: '#94a3b8', fontSize: 10 }} width={40} />
            <Tooltip
              contentStyle={{ background: '#1a2332', border: '1px solid #334155', borderRadius: 8, fontSize: 11 }}
              formatter={(v: any) => [`${Number(v) > 0 ? '+' : ''}${Number(v).toFixed(1)}%`, 'Risk Change']}
            />
            <Bar dataKey="delta" radius={[0, 4, 4, 0]}>
              {deltaData.map((d, i) => <Cell key={i} fill={d.delta > 0 ? '#ef4444' : '#22c55e'} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Detail Table */}
      <div className="glass p-5">
        <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-3">Detail by Country</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr>
                <th className="text-left px-2 py-2 text-slate-500 text-[10px] uppercase border-b border-border">Country</th>
                {metrics.map(m => (
                  <th key={m} colSpan={3} className="text-center px-1 py-2 text-slate-500 text-[10px] uppercase border-b border-border">{metricLabels[m]}</th>
                ))}
              </tr>
              <tr>
                <th className="border-b border-border/50" />
                {metrics.map(m => (
                  <React.Fragment key={m}>
                    <th className="text-center px-1 py-1 text-[8px] text-blue-400 border-b border-border/50">A</th>
                    <th className="text-center px-1 py-1 text-[8px] text-purple-400 border-b border-border/50">B</th>
                    <th className="text-center px-1 py-1 text-[8px] text-slate-500 border-b border-border/50">Δ</th>
                  </React.Fragment>
                ))}
              </tr>
            </thead>
            <tbody>
              {countries.map(c => (
                <tr key={c} className="border-b border-border/20 hover:bg-white/[0.02]">
                  <td className="px-2 py-1.5">{COUNTRIES[c]?.flag} {c}</td>
                  {metrics.map(m => {
                    const va = a.final_state[c]?.[m] || 0
                    const vb = b.final_state[c]?.[m] || 0
                    const d = delta(va, vb)
                    return (
                      <React.Fragment key={m}>
                        <td className="text-center px-1 py-1.5 font-mono text-blue-300">{pct(va)}</td>
                        <td className="text-center px-1 py-1.5 font-mono text-purple-300">{pct(vb)}</td>
                        <td className="text-center px-1 py-1.5 font-mono font-bold" style={{ color: d.color }}>{d.text}</td>
                      </React.Fragment>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </motion.div>
  )
}

// Need React import for fragments
import React from 'react'
