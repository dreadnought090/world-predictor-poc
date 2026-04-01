import { motion } from 'framer-motion'
import { useGlobalTension, useAllPredictions } from '../../api/queries'

const LEVELS = [
  { label: 'STABLE', color: '#22c55e', bg: 'rgba(34,197,94,0.12)', threshold: 0 },
  { label: 'ELEVATED', color: '#eab308', bg: 'rgba(234,179,8,0.12)', threshold: 0.2 },
  { label: 'HIGH', color: '#f97316', bg: 'rgba(249,115,22,0.12)', threshold: 0.4 },
  { label: 'SEVERE', color: '#ef4444', bg: 'rgba(239,68,68,0.12)', threshold: 0.6 },
  { label: 'CRITICAL', color: '#dc2626', bg: 'rgba(220,38,38,0.18)', threshold: 0.8 },
] as const

function getLevel(score: number) {
  for (let i = LEVELS.length - 1; i >= 0; i--) {
    if (score >= LEVELS[i].threshold) return LEVELS[i]
  }
  return LEVELS[0]
}

export default function ThreatLevel() {
  const { data: tensionData } = useGlobalTension()
  const { data: predictions } = useAllPredictions()

  const tension = tensionData?.global_tension_index ?? 0
  const predValues = predictions ? Object.values(predictions) : []
  const avgRisk = predValues.length > 0
    ? predValues.reduce((s, p) => s + p.metrics.revolution_risk, 0) / predValues.length
    : 0
  const compositeScore = tension * 0.4 + avgRisk * 0.6
  const level = getLevel(compositeScore)
  const isHigh = compositeScore >= 0.4

  return (
    <motion.div
      className="glass flex items-center gap-4 px-5 py-3"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      {/* Pulsing dot */}
      <div className="relative flex items-center justify-center">
        {isHigh && (
          <motion.div
            className="absolute w-5 h-5 rounded-full"
            style={{ background: level.color }}
            animate={{ scale: [1, 1.8, 1], opacity: [0.6, 0, 0.6] }}
            transition={{ duration: 1.5, repeat: Infinity }}
          />
        )}
        <div className="w-3 h-3 rounded-full z-10" style={{ background: level.color }} />
      </div>

      {/* Level label */}
      <div className="flex items-center gap-3">
        <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Threat Level</span>
        <motion.span
          key={level.label}
          className="text-sm font-extrabold tracking-widest px-3 py-0.5 rounded-md"
          style={{ color: level.color, background: level.bg }}
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
        >
          {level.label}
        </motion.span>
      </div>

      {/* Score bars */}
      <div className="ml-auto flex items-center gap-3">
        <div className="flex items-center gap-1.5">
          <span className="text-[9px] text-slate-500 uppercase">Tension</span>
          <span className="font-mono text-xs font-bold" style={{ color: level.color }}>{(tension * 100).toFixed(0)}%</span>
        </div>
        <div className="w-px h-4 bg-border" />
        <div className="flex items-center gap-1.5">
          <span className="text-[9px] text-slate-500 uppercase">Avg Risk</span>
          <span className="font-mono text-xs font-bold" style={{ color: level.color }}>{(avgRisk * 100).toFixed(0)}%</span>
        </div>
        <div className="w-px h-4 bg-border" />
        <div className="flex gap-0.5">
          {LEVELS.map((l, i) => (
            <div
              key={i}
              className="w-6 h-2 rounded-sm transition-all duration-500"
              style={{
                background: compositeScore >= l.threshold ? l.color : 'rgba(100,116,139,0.2)',
                opacity: compositeScore >= l.threshold ? 1 : 0.3,
              }}
            />
          ))}
        </div>
      </div>
    </motion.div>
  )
}
