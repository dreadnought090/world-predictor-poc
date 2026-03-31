import { useRef, useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useNewsArchive, useActiveEvents } from '../../api/queries'
import Badge from '../common/Badge'

interface WireItem {
  id: string
  type: 'news' | 'event' | 'alert'
  text: string
  detail?: string
  category?: string
  timestamp: number
}

function buildWireItems(
  news: { results: { title: string; source_name: string; category: string; impact: number }[] } | undefined,
  events: { active_events: { name: string; type: string; magnitude: number; days_remaining: number; affected: string[] }[] } | undefined,
): WireItem[] {
  const items: WireItem[] = []

  if (events?.active_events) {
    events.active_events.forEach((e, i) => {
      items.push({
        id: `event-${e.name}-${i}`,
        type: 'event',
        text: e.name,
        detail: `${e.affected.join(', ')} | Mag ${(e.magnitude * 100).toFixed(0)}% | ${e.days_remaining}d left`,
        category: e.type,
        timestamp: Date.now() - i * 60000,
      })
    })
  }

  if (news?.results) {
    news.results.slice(0, 15).forEach((n, i) => {
      items.push({
        id: `news-${i}-${n.title.slice(0, 20)}`,
        type: 'news',
        text: n.title,
        detail: `${n.source_name} | ${(n.impact * 100).toFixed(0)}% impact`,
        category: n.category,
        timestamp: Date.now() - (i + 10) * 60000,
      })
    })
  }

  return items.sort((a, b) => b.timestamp - a.timestamp)
}

const TYPE_COLORS = {
  news: '#3b82f6',
  event: '#ef4444',
  alert: '#f59e0b',
}

const TYPE_LABELS = {
  news: 'NEWS',
  event: 'EVENT',
  alert: 'ALERT',
}

export default function TheWire() {
  const { data: newsData } = useNewsArchive(15)
  const { data: eventsData } = useActiveEvents()
  const [paused, setPaused] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  const items = buildWireItems(newsData, eventsData)

  // Auto-scroll
  useEffect(() => {
    if (paused || !scrollRef.current) return
    const el = scrollRef.current
    const interval = setInterval(() => {
      if (el.scrollTop < el.scrollHeight - el.clientHeight) {
        el.scrollTop += 1
      } else {
        el.scrollTop = 0
      }
    }, 50)
    return () => clearInterval(interval)
  }, [paused])

  if (items.length === 0) {
    return (
      <div className="glass px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-slate-500 animate-pulse" />
          <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">The Wire</span>
          <span className="text-[10px] text-slate-600 ml-2">Waiting for intelligence... Fetch news to populate.</span>
        </div>
      </div>
    )
  }

  return (
    <div className="glass overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-2 border-b border-border/50">
        <div className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
        <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">The Wire</span>
        <span className="text-[10px] text-slate-600 font-mono ml-auto">{items.length} items</span>
      </div>

      {/* Scrolling feed */}
      <div
        ref={scrollRef}
        className="max-h-[180px] overflow-y-auto scrollbar-thin"
        onMouseEnter={() => setPaused(true)}
        onMouseLeave={() => setPaused(false)}
      >
        <AnimatePresence mode="popLayout">
          {items.map((item) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="flex items-start gap-2 px-4 py-2 border-b border-border/20 hover:bg-white/[0.02] transition-colors"
            >
              {/* Type indicator */}
              <div className="w-1 h-full min-h-[32px] rounded-full flex-shrink-0 mt-0.5" style={{ background: TYPE_COLORS[item.type] }} />

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span
                    className="text-[8px] font-bold tracking-widest px-1.5 py-0.5 rounded"
                    style={{ color: TYPE_COLORS[item.type], background: TYPE_COLORS[item.type] + '18' }}
                  >
                    {TYPE_LABELS[item.type]}
                  </span>
                  {item.category && <Badge category={item.category} />}
                </div>
                <div className="text-[11px] font-medium text-slate-300 mt-0.5 truncate">{item.text}</div>
                {item.detail && <div className="text-[9px] text-slate-500 font-mono mt-0.5">{item.detail}</div>}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  )
}
