import { useActiveEvents } from '../../api/queries'

export default function ActiveEventsList() {
  const { data } = useActiveEvents()
  const events = data?.active_events ?? []

  if (!events.length) return <div className="text-xs text-slate-500 text-center py-6">No active events. Inject one above.</div>

  return (
    <div className="space-y-2">
      {events.map((e, i) => (
        <div key={i} className="bg-surface border border-border rounded-lg p-3">
          <div className="text-[9px] font-bold uppercase tracking-wider text-warning">{e.type}</div>
          <div className="text-sm font-semibold mt-0.5">{e.name}</div>
          <div className="text-[10px] text-slate-500 mt-1 flex gap-3">
            <span>Mag: {(e.magnitude * 100).toFixed(0)}%</span>
            <span>{e.days_remaining}d left</span>
            <span>{e.affected.join(', ')}</span>
          </div>
        </div>
      ))}
    </div>
  )
}
