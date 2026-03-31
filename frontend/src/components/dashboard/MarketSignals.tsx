import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useMarketSignals } from '../../api/queries'
import { COUNTRIES } from '../../constants/countries'

interface Signal {
  country: string
  currency: string
  rate_to_usd: number
  strength: number
}

export default function MarketSignals() {
  const { data, isLoading } = useMarketSignals()
  const [expanded, setExpanded] = useState(false)

  if (isLoading) return null

  const signals: Signal[] = data?.signals ?? []
  if (signals.length === 0) return null

  const sorted = [...signals].sort((a, b) => b.strength - a.strength)

  const strengthColor = (s: number) => {
    if (s >= 0.7) return '#22c55e'
    if (s >= 0.4) return '#eab308'
    return '#ef4444'
  }

  return (
    <div className="glass overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-2 px-4 py-2.5 hover:bg-white/[0.02] transition-colors"
      >
        <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Market Signals</span>
        <span className="text-[10px] text-slate-600 font-mono">{signals.length} currencies</span>
        <motion.span
          className="ml-auto text-slate-500 text-xs"
          animate={{ rotate: expanded ? 180 : 0 }}
        >
          &#9660;
        </motion.span>
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 gap-1.5 px-4 pb-3">
              {sorted.map((s) => {
                const c = COUNTRIES[s.country]
                return (
                  <div
                    key={s.country}
                    className="flex items-center gap-2 bg-bg2 rounded-lg px-2.5 py-2"
                  >
                    <span className="text-sm">{c?.flag || ''}</span>
                    <div className="flex-1 min-w-0">
                      <div className="text-[10px] font-semibold">{s.country}</div>
                      <div className="text-[8px] text-slate-500 font-mono uppercase">{s.currency}</div>
                    </div>
                    <div className="text-right">
                      <div
                        className="text-xs font-bold font-mono"
                        style={{ color: strengthColor(s.strength) }}
                      >
                        {(s.strength * 100).toFixed(0)}%
                      </div>
                      <div className="w-10 h-1 rounded-full bg-surface2 overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-500"
                          style={{
                            width: `${s.strength * 100}%`,
                            background: strengthColor(s.strength),
                          }}
                        />
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
