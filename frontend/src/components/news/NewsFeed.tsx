import { useNewsArchive } from '../../api/queries'
import Badge from '../common/Badge'

export default function NewsFeed() {
  const { data } = useNewsArchive()
  const items = data?.results ?? []

  if (!items.length) return <div className="text-xs text-slate-500 text-center py-6">Click "Fetch & Simulate" for news.</div>

  return (
    <div className="space-y-0 max-h-[380px] overflow-y-auto">
      {items.map((n, i) => (
        <div key={i} className="py-2 border-b border-border/30 last:border-0">
          <div className="text-xs font-medium leading-snug">{n.title}</div>
          <div className="flex items-center gap-1.5 mt-1">
            <Badge category={n.category} />
            <span className="text-[10px] text-slate-500">{n.source_name}</span>
            <span className="text-[10px] text-slate-600">{n.region}</span>
          </div>
        </div>
      ))}
    </div>
  )
}
