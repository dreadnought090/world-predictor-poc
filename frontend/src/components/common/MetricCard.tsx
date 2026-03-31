import { motion, useSpring, useTransform } from 'framer-motion'
import { useEffect } from 'react'

interface Props {
  label: string
  value: number
  color: string
  format?: 'pct' | 'number'
  size?: 'sm' | 'md' | 'lg'
}

export default function MetricCard({ label, value, color, format = 'pct', size = 'md' }: Props) {
  const spring = useSpring(0, { stiffness: 60, damping: 20 })
  const display = useTransform(spring, (v) =>
    format === 'pct' ? `${(v * 100).toFixed(0)}%` : v.toFixed(0)
  )

  useEffect(() => { spring.set(value) }, [value, spring])

  const sizes = { sm: 'text-lg', md: 'text-2xl', lg: 'text-3xl' }

  return (
    <div className="relative overflow-hidden rounded-xl bg-surface border border-border p-3 text-center">
      <div className={`absolute top-0 left-0 right-0 h-[3px] rounded-t-xl`} style={{ background: `linear-gradient(90deg, ${color}, ${color}88)` }} />
      <motion.div className={`${sizes[size]} font-extrabold font-mono tracking-tight`} style={{ color }}>
        {display}
      </motion.div>
      <div className="text-[10px] text-slate-500 mt-1 font-semibold uppercase tracking-wider">{label}</div>
    </div>
  )
}
