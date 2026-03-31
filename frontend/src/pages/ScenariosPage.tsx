import { useState } from 'react'
import { motion } from 'framer-motion'
import { usePresetEvents, usePresetPolicies } from '../api/queries'
import { useRunScenario } from '../api/mutations'
import { COUNTRIES } from '../constants/countries'

const pct = (v: number) => `${(v * 100).toFixed(1)}%`

export default function ScenariosPage() {
  const { data: events } = usePresetEvents()
  const { data: policies } = usePresetPolicies()
  const runScenario = useRunScenario()

  const [name, setName] = useState('')
  const [event, setEvent] = useState('')
  const [policy, setPolicy] = useState('')
  const [policyCountry, setPolicyCountry] = useState('US')
  const [days, setDays] = useState(30)

  const handleRun = () => {
    if (!name) return
    runScenario.mutate({
      name,
      description: `Event: ${event || 'none'}, Policy: ${policy || 'none'} in ${policyCountry}`,
      preset_event: event || undefined,
      preset_policy: policy || undefined,
      policy_country: policyCountry,
      days,
    })
  }

  const result = runScenario.data

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col gap-4">
      <h2 className="text-xl font-bold">Scenario Builder</h2>

      <div className="glass p-5">
        <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-4">Configure What-If Scenario</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
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
              disabled={!name || runScenario.isPending}
              className="px-6 py-2.5 rounded-lg text-sm font-semibold bg-gradient-to-r from-accent to-blue-700 text-white hover:shadow-[0_0_20px_rgba(59,130,246,0.3)] transition-all disabled:opacity-50 w-full"
            >
              {runScenario.isPending ? 'Running...' : 'Run Scenario'}
            </button>
          </div>
        </div>
      </div>

      {/* Results */}
      {result && (
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
                {Object.entries(result.final_state || {}).map(([code, m]: [string, any]) => (
                  <tr key={code} className="border-b border-border/40">
                    <td className="px-3 py-2"><span className="mr-1">{COUNTRIES[code]?.flag}</span>{code}</td>
                    <td className="px-3 py-2 font-mono">{pct(m.average_optimism || 0)}</td>
                    <td className="px-3 py-2 font-mono">{pct(m.social_cohesion || 0)}</td>
                    <td className="px-3 py-2 font-mono">{pct(m.political_stability || 0)}</td>
                    <td className="px-3 py-2 font-mono">{pct(m.revolution_risk || 0)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </motion.div>
  )
}
