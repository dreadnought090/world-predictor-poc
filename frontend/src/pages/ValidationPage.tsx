import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import client from '../api/client'
import { COUNTRIES } from '../constants/countries'

interface HistEvent {
  name: string
  country: string
  date: string
  type: string
  severity: string
}

function useHistoricalEvents() {
  return useQuery<HistEvent[]>({
    queryKey: ['validation', 'events'],
    queryFn: () => client.get('/validation/events').then(r => r.data),
  })
}

const SEVERITY_COLORS: Record<string, string> = { high: '#ef4444', medium: '#f59e0b', low: '#22c55e' }
const TYPE_COLORS: Record<string, string> = {
  CIVIL_UNREST: '#f97316', ELECTION: '#3b82f6', ECONOMIC_CRISIS: '#ef4444',
  PANDEMIC: '#a855f7', WAR: '#dc2626', COUP: '#ef4444',
}

export default function ValidationPage() {
  const { data: events, isLoading } = useHistoricalEvents()

  if (isLoading) return <div className="text-slate-500 text-center mt-12">Loading historical events...</div>

  const list = events ?? []
  const highCount = list.filter(e => e.severity === 'high').length
  const medCount = list.filter(e => e.severity === 'medium').length

  // Group by decade
  const byDecade: Record<string, HistEvent[]> = {}
  list.forEach(e => {
    const decade = e.date.slice(0, 3) + '0s'
    if (!byDecade[decade]) byDecade[decade] = []
    byDecade[decade].push(e)
  })

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col gap-4">
      <h2 className="text-xl font-bold">Validation Framework</h2>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-3">
        <div className="glass p-4 text-center">
          <div className="text-2xl font-bold font-mono text-accent2">{list.length}</div>
          <div className="text-[9px] text-slate-500 uppercase mt-1">Historical Events</div>
        </div>
        <div className="glass p-4 text-center">
          <div className="text-2xl font-bold font-mono text-red-400">{highCount}</div>
          <div className="text-[9px] text-slate-500 uppercase mt-1">High Severity</div>
        </div>
        <div className="glass p-4 text-center">
          <div className="text-2xl font-bold font-mono text-yellow-400">{medCount}</div>
          <div className="text-[9px] text-slate-500 uppercase mt-1">Medium Severity</div>
        </div>
      </div>

      {/* How it works */}
      <div className="glass p-5">
        <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-3">How Validation Works</h3>
        <div className="text-xs text-slate-400 space-y-2">
          <p>The backtesting framework tests whether the simulation would have predicted known historical crises:</p>
          <ol className="list-decimal list-inside space-y-1 text-slate-500">
            <li>Run a scenario simulating conditions leading up to a known event</li>
            <li>Inject the event type into the simulation</li>
            <li>Measure if revolution risk / instability metrics rose appropriately</li>
            <li>Score based on: risk level achieved, early warning days, detection rate</li>
          </ol>
          <p className="text-slate-600 mt-2">Use the Scenario Builder to run what-if scenarios based on these historical events, then compare the predicted outcomes against actual severity.</p>
        </div>
      </div>

      {/* Event Timeline */}
      <div className="glass p-5">
        <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-4">Historical Event Database</h3>
        <div className="space-y-6">
          {Object.entries(byDecade).sort((a, b) => b[0].localeCompare(a[0])).map(([decade, events]) => (
            <div key={decade}>
              <h4 className="text-xs font-bold text-slate-400 mb-2">{decade}</h4>
              <div className="space-y-1.5">
                {events.sort((a, b) => b.date.localeCompare(a.date)).map((e, i) => (
                  <div key={i} className="flex items-center gap-3 bg-bg2 rounded-lg px-4 py-2.5 hover:bg-surface2 transition-colors">
                    {/* Date */}
                    <div className="text-[10px] font-mono text-slate-500 w-20 flex-shrink-0">{e.date}</div>

                    {/* Severity dot */}
                    <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: SEVERITY_COLORS[e.severity] }} />

                    {/* Country */}
                    <span className="text-sm flex-shrink-0">{COUNTRIES[e.country]?.flag || e.country}</span>

                    {/* Name */}
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-medium text-slate-200 truncate">{e.name}</div>
                    </div>

                    {/* Type badge */}
                    <span
                      className="text-[8px] font-bold tracking-wider px-2 py-0.5 rounded flex-shrink-0"
                      style={{ color: TYPE_COLORS[e.type] || '#64748b', background: (TYPE_COLORS[e.type] || '#64748b') + '18' }}
                    >
                      {e.type.replace(/_/g, ' ')}
                    </span>

                    {/* Severity */}
                    <span
                      className="text-[8px] font-bold uppercase px-2 py-0.5 rounded flex-shrink-0"
                      style={{ color: SEVERITY_COLORS[e.severity], background: SEVERITY_COLORS[e.severity] + '18' }}
                    >
                      {e.severity}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div className="flex gap-4 justify-center text-[10px] text-slate-500">
        {Object.entries(SEVERITY_COLORS).map(([sev, color]) => (
          <span key={sev} className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full" style={{ background: color }} />
            {sev} severity
          </span>
        ))}
      </div>
    </motion.div>
  )
}
