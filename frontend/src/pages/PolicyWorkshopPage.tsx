import { useState } from 'react'
import { motion } from 'framer-motion'
import { usePresetPolicies } from '../api/queries'
import { useRunScenario } from '../api/mutations'
import { COUNTRIES } from '../constants/countries'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'

const pct = (v: number) => `${(v * 100).toFixed(1)}%`

interface PolicyResult {
  policy: string
  country: string
  final_state: Record<string, any>
}

export default function PolicyWorkshopPage() {
  const { data: policies } = usePresetPolicies()
  const runScenario = useRunScenario()

  const [country, setCountry] = useState('US')
  const [policyA, setPolicyA] = useState('')
  const [policyB, setPolicyB] = useState('')
  const [days, setDays] = useState(30)
  const [results, setResults] = useState<PolicyResult[]>([])
  const [running, setRunning] = useState(false)

  const handleCompare = async () => {
    if (!policyA || !policyB) return
    setRunning(true)
    setResults([])

    try {
      const resultA = await runScenario.mutateAsync({
        name: `Policy A: ${policyA}`,
        preset_policy: policyA,
        policy_country: country,
        days,
      })
      const resultB = await runScenario.mutateAsync({
        name: `Policy B: ${policyB}`,
        preset_policy: policyB,
        policy_country: country,
        days,
      })

      setResults([
        { policy: policyA, country, final_state: resultA.final_state },
        { policy: policyB, country, final_state: resultB.final_state },
      ])
    } catch {
      // toast error already handled by mutation's onError
    } finally {
      setRunning(false)
    }
  }

  const metricKeys = ['average_optimism', 'social_cohesion', 'political_stability', 'revolution_risk'] as const
  const metricLabels: Record<string, string> = {
    average_optimism: 'Optimism', social_cohesion: 'Trust',
    political_stability: 'Stability', revolution_risk: 'Rev. Risk',
  }
  const metricColors: Record<string, string> = {
    average_optimism: '#3b82f6', social_cohesion: '#22c55e',
    political_stability: '#a855f7', revolution_risk: '#ef4444',
  }

  // Build comparison bar data for the selected country
  const comparisonData = results.length === 2
    ? metricKeys.map(k => ({
        metric: metricLabels[k],
        [results[0].policy]: +(results[0].final_state[country]?.[k] * 100 || 0).toFixed(1),
        [results[1].policy]: +(results[1].final_state[country]?.[k] * 100 || 0).toFixed(1),
        color: metricColors[k],
      }))
    : []

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col gap-4">
      <h2 className="text-xl font-bold">Policy Workshop</h2>
      <p className="text-xs text-slate-500 -mt-2">Compare two policies head-to-head: which one stabilizes the country faster?</p>

      <div className="glass p-5">
        <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-4">Configure Comparison</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <div>
            <label className="text-[10px] text-slate-500 uppercase font-semibold">Country</label>
            <select value={country} onChange={e => setCountry(e.target.value)} className="mt-1 w-full bg-bg2 border border-border rounded-lg px-3 py-2 text-sm text-slate-300">
              {Object.values(COUNTRIES).map(c => <option key={c.code} value={c.code}>{c.flag} {c.name}</option>)}
            </select>
          </div>
          <div>
            <label className="text-[10px] text-blue-400 uppercase font-semibold">Policy A</label>
            <select value={policyA} onChange={e => setPolicyA(e.target.value)} className="mt-1 w-full bg-bg2 border border-blue-500/30 rounded-lg px-3 py-2 text-sm text-slate-300">
              <option value="">Select policy...</option>
              {policies && Object.entries(policies).map(([k, v]) => <option key={k} value={k}>{v.name}</option>)}
            </select>
          </div>
          <div>
            <label className="text-[10px] text-purple-400 uppercase font-semibold">Policy B</label>
            <select value={policyB} onChange={e => setPolicyB(e.target.value)} className="mt-1 w-full bg-bg2 border border-purple-500/30 rounded-lg px-3 py-2 text-sm text-slate-300">
              <option value="">Select policy...</option>
              {policies && Object.entries(policies).map(([k, v]) => <option key={k} value={k}>{v.name}</option>)}
            </select>
          </div>
          <div>
            <label className="text-[10px] text-slate-500 uppercase font-semibold">Days: {days}</label>
            <input type="range" min={5} max={90} value={days} onChange={e => setDays(+e.target.value)} className="mt-2 w-full accent-accent" />
          </div>
          <div className="flex items-end">
            <button
              onClick={handleCompare}
              disabled={!policyA || !policyB || policyA === policyB || running}
              className="w-full px-4 py-2.5 rounded-lg text-sm font-semibold bg-gradient-to-r from-accent to-purple text-white hover:shadow-[0_0_20px_rgba(59,130,246,0.3)] transition-all disabled:opacity-50"
            >
              {running ? 'Running...' : 'Compare Policies'}
            </button>
          </div>
        </div>
      </div>

      {/* Results */}
      {results.length === 2 && (
        <>
          {/* Bar chart comparison */}
          <div className="glass p-5">
            <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-3">
              {COUNTRIES[country]?.flag} {COUNTRIES[country]?.name} — After {days} Days
            </h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={comparisonData}>
                <XAxis dataKey="metric" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <YAxis tickFormatter={v => `${v}%`} tick={{ fill: '#64748b', fontSize: 10 }} />
                <Tooltip contentStyle={{ background: '#1a2332', border: '1px solid #334155', borderRadius: 8, fontSize: 11 }} formatter={(v: any) => `${v}%`} />
                <Bar dataKey={results[0].policy} fill="#3b82f6" radius={[4, 4, 0, 0]} />
                <Bar dataKey={results[1].policy} fill="#a855f7" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
            <div className="flex gap-4 justify-center mt-2 text-xs">
              <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-blue-500" /> {results[0].policy.replace(/_/g, ' ')}</span>
              <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-purple-500" /> {results[1].policy.replace(/_/g, ' ')}</span>
            </div>
          </div>

          {/* Winner card */}
          <div className="glass p-5">
            <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-3">Winner Analysis</h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {metricKeys.map(k => {
                const vA = results[0].final_state[country]?.[k] ?? 0
                const vB = results[1].final_state[country]?.[k] ?? 0
                // For revolution_risk, lower is better
                const aIsBetter = k === 'revolution_risk' ? vA < vB : vA > vB
                const winner = vA === vB ? 'Tie' : aIsBetter ? results[0].policy : results[1].policy
                const winnerColor = vA === vB ? '#64748b' : aIsBetter ? '#3b82f6' : '#a855f7'

                return (
                  <div key={k} className="bg-bg2 rounded-lg p-3 text-center">
                    <div className="text-[9px] text-slate-500 uppercase mb-1">{metricLabels[k]}</div>
                    <div className="text-xs font-bold" style={{ color: winnerColor }}>
                      {winner === 'Tie' ? 'Tie' : winner.replace(/_/g, ' ')}
                    </div>
                    <div className="flex justify-center gap-2 mt-1 text-[10px] font-mono">
                      <span className="text-blue-400">{pct(vA)}</span>
                      <span className="text-slate-600">vs</span>
                      <span className="text-purple-400">{pct(vB)}</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </>
      )}
    </motion.div>
  )
}
