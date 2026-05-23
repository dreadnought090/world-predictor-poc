import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { usePresetEvents, usePresetPolicies } from '../api/queries'
import { useParseScenario, useRunScenario } from '../api/mutations'
import { COUNTRIES } from '../constants/countries'
import ScenarioComparePage from './ScenarioComparePage'
import type { Metrics, ScenarioResult } from '../types'

const metricValue = (metrics: Partial<Metrics> | undefined, key: keyof Metrics) => {
  const value = metrics?.[key]
  return typeof value === 'number' && Number.isFinite(value) ? value : 0
}

const pct = (v: number) => `${(v * 100).toFixed(1)}%`
const deltaPct = (v: number) => `${v >= 0 ? '+' : ''}${(v * 100).toFixed(1)}pt`
const avg = (values: number[]) => values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : 0
const riskColor = (risk: number) => risk >= 0.6 ? '#ef4444' : risk >= 0.4 ? '#f59e0b' : '#22c55e'

export default function ScenariosPage() {
  const { data: events } = usePresetEvents()
  const { data: policies } = usePresetPolicies()
  const runScenario = useRunScenario()
  const parseScenario = useParseScenario()

  const [name, setName] = useState('')
  const [scenarioText, setScenarioText] = useState('')
  const [event, setEvent] = useState('')
  const [policy, setPolicy] = useState('')
  const [policyCountry, setPolicyCountry] = useState('US')
  const [days, setDays] = useState(30)
  const [history, setHistory] = useState<ScenarioResult[]>([])
  const [showCompare, setShowCompare] = useState(false)

  const handleAnalyze = () => {
    const text = scenarioText.trim()
    if (!text) return
    parseScenario.mutate(text, {
      onSuccess: (data) => {
        if (!name.trim()) setName(data.title)
        if (!event && data.suggested_preset_event) setEvent(data.suggested_preset_event)
        if (!policy && data.suggested_policy) setPolicy(data.suggested_policy)
        if (data.affected_countries[0]) setPolicyCountry(data.affected_countries[0])
        setDays(Math.max(5, Math.min(90, data.duration_days)))
      },
    })
  }

  const handleRun = () => {
    const text = scenarioText.trim()
    const scenarioName = name.trim() || parseScenario.data?.title || text.slice(0, 80)
    if (!scenarioName) return
    runScenario.mutate({
      name: scenarioName,
      description: parseScenario.data?.summary ?? `Event: ${event || 'none'}, Policy: ${policy || 'none'} in ${policyCountry}`,
      preset_event: event || undefined,
      preset_policy: policy || undefined,
      policy_country: policy ? policyCountry : undefined,
      scenario_text: text || undefined,
      days,
    }, {
      onSuccess: (data) => {
        setHistory(prev => [...prev, data])
      }
    })
  }

  const result = runScenario.data
  const resultRows = Object.entries(result?.final_state ?? {}).map(([code, metrics]) => {
    const risk = metricValue(metrics, 'revolution_risk')
    return {
      code,
      optimism: metricValue(metrics, 'average_optimism'),
      trust: metricValue(metrics, 'social_cohesion'),
      stability: metricValue(metrics, 'political_stability'),
      risk,
    }
  }).sort((left, right) => right.risk - left.risk)
  const averageRisk = avg(resultRows.map(row => row.risk))
  const averageOptimism = avg(resultRows.map(row => row.optimism))
  const highRiskCount = resultRows.filter(row => row.risk >= 0.4).length
  const peakRisk = resultRows[0]
  const assumptions = parseScenario.data ?? result?.assumptions ?? null

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">Scenario Builder</h2>
        {history.length >= 2 && (
          <button
            onClick={() => setShowCompare(!showCompare)}
            className="px-4 py-1.5 rounded-lg text-xs font-semibold transition-all"
            style={{
              background: showCompare ? 'rgba(168,85,247,0.2)' : 'rgba(59,130,246,0.2)',
              color: showCompare ? '#a855f7' : '#60a5fa',
            }}
          >
            {showCompare ? 'Hide Comparison' : `Compare (${history.length} scenarios)`}
          </button>
        )}
      </div>

      {runScenario.isError && (
        <div className="glass p-4 border border-red-500/30 text-sm text-red-300">
          {runScenario.error?.message || 'Scenario failed'}
        </div>
      )}

      <div className="glass p-5">
        <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-4">Configure What-If Scenario</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-3">
            <div className="flex items-center justify-between gap-3">
              <label className="text-[10px] text-slate-500 uppercase font-semibold">Scenario Brief</label>
              <button
                onClick={handleAnalyze}
                disabled={!scenarioText.trim() || parseScenario.isPending}
                className="px-3 py-1 rounded-md text-[10px] font-semibold uppercase tracking-wider bg-cyan/10 text-cyan hover:bg-cyan/20 transition-colors disabled:opacity-50"
              >
                {parseScenario.isPending ? 'Analyzing' : 'Analyze'}
              </button>
            </div>
            <textarea
              value={scenarioText}
              onChange={e => setScenarioText(e.target.value)}
              placeholder="China blocks rare earth exports to the US for 90 days"
              className="mt-1 w-full min-h-20 bg-bg2 border border-border rounded-lg px-3 py-2 text-sm text-slate-200 focus:border-accent focus:outline-none resize-y"
            />
          </div>
          <div>
            <label className="text-[10px] text-slate-500 uppercase font-semibold">Scenario Name</label>
            <input value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Pandemic Impact" className="mt-1 w-full bg-bg2 border border-border rounded-lg px-3 py-2 text-sm text-slate-200 focus:border-accent focus:outline-none" />
          </div>
          <div>
            <label className="text-[10px] text-slate-500 uppercase font-semibold">Event</label>
            <select value={event} onChange={e => setEvent(e.target.value)} className="mt-1 w-full bg-bg2 border border-border rounded-lg px-3 py-2 text-sm text-slate-300">
              <option value="">No event</option>
              {events && Object.entries(events).map(([k, v]) => <option key={k} value={k}>{v.name}</option>)}
            </select>
          </div>
          <div>
            <label className="text-[10px] text-slate-500 uppercase font-semibold">Policy</label>
            <select value={policy} onChange={e => setPolicy(e.target.value)} className="mt-1 w-full bg-bg2 border border-border rounded-lg px-3 py-2 text-sm text-slate-300">
              <option value="">No policy</option>
              {policies && Object.entries(policies).map(([k, v]) => <option key={k} value={k}>{v.name}</option>)}
            </select>
          </div>
          <div>
            <label className="text-[10px] text-slate-500 uppercase font-semibold">Policy Country</label>
            <select value={policyCountry} onChange={e => setPolicyCountry(e.target.value)} className="mt-1 w-full bg-bg2 border border-border rounded-lg px-3 py-2 text-sm text-slate-300">
              {Object.values(COUNTRIES).map(c => <option key={c.code} value={c.code}>{c.flag} {c.name}</option>)}
            </select>
          </div>
          <div>
            <label className="text-[10px] text-slate-500 uppercase font-semibold">Days: {days}</label>
            <input type="range" min={5} max={90} value={days} onChange={e => setDays(+e.target.value)} className="mt-2 w-full accent-accent" />
          </div>
          <div className="flex items-end">
            <button
              onClick={handleRun}
              disabled={(!name.trim() && !scenarioText.trim()) || runScenario.isPending}
              className="px-6 py-2.5 rounded-lg text-sm font-semibold bg-gradient-to-r from-accent to-blue-700 text-white hover:shadow-[0_0_20px_rgba(59,130,246,0.3)] transition-all disabled:opacity-50 w-full"
            >
              {runScenario.isPending ? 'Running...' : 'Run Scenario'}
            </button>
          </div>
        </div>
        {assumptions && (
          <div className="mt-4 grid grid-cols-2 md:grid-cols-6 gap-2">
            {[
              { label: 'Type', value: assumptions.event_type.replace(/_/g, ' ') },
              { label: 'Severity', value: assumptions.severity },
              { label: 'Duration', value: `${assumptions.duration_days}d` },
              { label: 'Confidence', value: assumptions.confidence.level },
              { label: 'Countries', value: assumptions.affected_countries.slice(0, 4).join(', ') },
              { label: 'Sectors', value: assumptions.sectors.slice(0, 3).join(', ') || 'general' },
            ].map(item => (
              <div key={item.label} className="bg-bg2 rounded-lg px-3 py-2 min-h-14">
                <div className="text-[9px] text-slate-500 uppercase">{item.label}</div>
                <div className="text-xs text-slate-200 font-semibold capitalize truncate">{item.value}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Scenario History */}
      {history.length > 0 && (
        <div className="glass p-4">
          <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-2">Scenario History</h3>
          <div className="flex flex-wrap gap-2">
            {history.map((s, i) => (
              <div key={s.scenario_id} className="bg-bg2 rounded-lg px-3 py-2 text-xs">
                <span className="font-semibold text-accent2">#{i + 1}</span>
                <span className="text-slate-300 ml-1.5">{s.name}</span>
                <span className="text-slate-500 ml-1.5">{s.days_simulated}d</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Comparison */}
      <AnimatePresence>
        {showCompare && history.length >= 2 && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}>
            <ScenarioComparePage scenarios={history} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Latest Result */}
      {result && !showCompare && (
        <div className="glass p-5">
          <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-4">
            Results: {result.name} ({result.days_simulated} days)
          </h3>
          {result.events_injected?.length > 0 && (
            <div className="text-xs text-warning mb-2">Events: {result.events_injected.join(', ')}</div>
          )}
          {result.policies_injected?.length > 0 && (
            <div className="text-xs text-purple2 mb-2">Policies: {result.policies_injected.join(', ')}</div>
          )}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
            {[
              { label: 'Avg Risk', value: pct(averageRisk), color: riskColor(averageRisk) },
              { label: 'Elevated Risk', value: `${highRiskCount}/${resultRows.length}`, color: highRiskCount > 0 ? '#f59e0b' : '#22c55e' },
              { label: 'Peak Risk', value: peakRisk ? `${peakRisk.code} ${pct(peakRisk.risk)}` : 'n/a', color: peakRisk ? riskColor(peakRisk.risk) : '#64748b' },
              { label: 'Avg Optimism', value: pct(averageOptimism), color: '#60a5fa' },
            ].map(item => (
              <div key={item.label} className="bg-bg2 rounded-lg p-3">
                <div className="text-lg font-bold font-mono" style={{ color: item.color }}>{item.value}</div>
                <div className="text-[9px] text-slate-500 uppercase mt-1">{item.label}</div>
              </div>
            ))}
          </div>
          {result.top_impacts && result.top_impacts.length > 0 && (
            <div className="mb-4">
              <h4 className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 mb-2">Baseline Delta</h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
                {result.top_impacts.slice(0, 4).map(impact => (
                  <div key={impact.country} className="bg-bg2 rounded-lg p-3">
                    <div className="flex items-center justify-between gap-2">
                      <div className="text-sm font-semibold text-slate-200">
                        <span className="mr-1">{COUNTRIES[impact.country]?.flag}</span>{impact.country}
                      </div>
                      <div className="font-mono text-sm font-bold" style={{ color: impact.risk_delta >= 0 ? '#ef4444' : '#22c55e' }}>
                        {deltaPct(impact.risk_delta)}
                      </div>
                    </div>
                    <div className="mt-2 grid grid-cols-2 gap-2 text-[10px] text-slate-500">
                      <span>Stab {deltaPct(impact.stability_delta)}</span>
                      <span>Opt {deltaPct(impact.optimism_delta)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          {result.explanations && result.explanations.length > 0 && (
            <div className="mb-4">
              <h4 className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 mb-2">Impact Drivers</h4>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-2">
                {result.explanations.slice(0, 4).map(explanation => (
                  <div key={explanation.country} className="bg-bg2 rounded-lg p-3">
                    <div className="text-xs text-slate-200 font-semibold mb-2">
                      <span className="mr-1">{COUNTRIES[explanation.country]?.flag}</span>{explanation.summary}
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {explanation.drivers.map(driver => (
                        <span
                          key={`${explanation.country}-${driver.metric}`}
                          className="px-2 py-1 rounded-md bg-black/20 text-[10px] font-mono"
                          style={{ color: driver.direction === 'negative' ? '#f87171' : '#34d399' }}
                        >
                          {driver.label} {deltaPct(driver.delta)}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          {resultRows.length === 0 ? (
            <div className="text-xs text-slate-500 text-center py-6">No country metrics returned.</div>
          ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr>
                  <th className="text-left px-3 py-2 text-slate-500 text-[10px] uppercase border-b border-border">Country</th>
                  <th className="text-left px-3 py-2 text-slate-500 text-[10px] uppercase border-b border-border">Optimism</th>
                  <th className="text-left px-3 py-2 text-slate-500 text-[10px] uppercase border-b border-border">Trust</th>
                  <th className="text-left px-3 py-2 text-slate-500 text-[10px] uppercase border-b border-border">Stability</th>
                  <th className="text-left px-3 py-2 text-slate-500 text-[10px] uppercase border-b border-border">Rev. Risk</th>
                </tr>
              </thead>
              <tbody>
                {resultRows.map(row => (
                  <tr key={row.code} className="border-b border-border/40">
                    <td className="px-3 py-2"><span className="mr-1">{COUNTRIES[row.code]?.flag}</span>{row.code}</td>
                    <td className="px-3 py-2 font-mono">{pct(row.optimism)}</td>
                    <td className="px-3 py-2 font-mono">{pct(row.trust)}</td>
                    <td className="px-3 py-2 font-mono">{pct(row.stability)}</td>
                    <td className="px-3 py-2 font-mono font-semibold" style={{ color: riskColor(row.risk) }}>{pct(row.risk)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          )}
        </div>
      )}
    </motion.div>
  )
}
