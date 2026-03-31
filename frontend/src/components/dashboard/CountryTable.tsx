import { useNavigate } from 'react-router-dom'
import { useUIStore } from '../../stores/uiStore'
import { COUNTRIES } from '../../constants/countries'
import ProgressBar from '../common/ProgressBar'
import type { Prediction } from '../../types'

const COLS = [
  { key: 'country', label: 'Country' },
  { key: 'day', label: 'Day' },
  { key: 'average_optimism', label: 'Optimism' },
  { key: 'social_cohesion', label: 'Trust' },
  { key: 'political_stability', label: 'Stability' },
  { key: 'revolution_risk', label: 'Revolution Risk' },
]

export default function CountryTable({ data }: { data: Record<string, Prediction> }) {
  const navigate = useNavigate()
  const { sortColumn, sortDir, setSort } = useUIStore()

  const entries = Object.entries(data).sort((a, b) => {
    const av = sortColumn === 'country' ? a[0] : sortColumn === 'day' ? a[1].day : (a[1].metrics as unknown as Record<string, number>)[sortColumn] ?? 0
    const bv = sortColumn === 'country' ? b[0] : sortColumn === 'day' ? b[1].day : (b[1].metrics as unknown as Record<string, number>)[sortColumn] ?? 0
    if (typeof av === 'string') return sortDir === 'asc' ? av.localeCompare(bv as string) : (bv as string).localeCompare(av)
    return sortDir === 'asc' ? (av as number) - (bv as number) : (bv as number) - (av as number)
  })

  const pct = (v: number) => `${(v * 100).toFixed(1)}%`

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr>
            {COLS.map(col => (
              <th
                key={col.key}
                onClick={() => setSort(col.key)}
                className="text-left px-3 py-2.5 text-slate-500 font-medium text-[10px] uppercase tracking-wider border-b border-border cursor-pointer hover:text-slate-300 select-none transition-colors"
              >
                {col.label}
                {sortColumn === col.key && <span className="ml-1">{sortDir === 'asc' ? '\u25B2' : '\u25BC'}</span>}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {entries.map(([code, pred]) => {
            const c = COUNTRIES[code]
            const m = pred.metrics
            const risk = m.revolution_risk ?? 0
            return (
              <tr
                key={code}
                onClick={() => navigate(`/country/${code}`)}
                className="border-b border-border/40 hover:bg-accent/[0.04] cursor-pointer transition-colors"
              >
                <td className="px-3 py-2.5">
                  <span className="text-base mr-1.5">{c?.flag}</span>
                  <span className="font-semibold text-[13px]">{code}</span>
                  <span className="text-slate-500 ml-1.5 hidden sm:inline">{c?.name}</span>
                </td>
                <td className="px-3 py-2.5 font-mono">{pred.day}</td>
                <td className="px-3 py-2.5 font-mono">{pct(m.average_optimism)}</td>
                <td className="px-3 py-2.5 font-mono">{pct(m.social_cohesion)}</td>
                <td className="px-3 py-2.5 font-mono">{pct(m.political_stability)}</td>
                <td className="px-3 py-2.5">
                  <div className="flex items-center gap-2">
                    <ProgressBar value={risk} />
                    <span className="font-mono">{pct(risk)}</span>
                  </div>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
