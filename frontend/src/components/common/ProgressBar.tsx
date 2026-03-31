export default function ProgressBar({ value, max = 1, color }: { value: number; max?: number; color?: string }) {
  const pct = Math.min(100, (value / max) * 100)
  const c = color || (pct > 60 ? '#ef4444' : pct > 35 ? '#f59e0b' : '#10b981')
  return (
    <div className="h-[7px] bg-surface2 rounded-full overflow-hidden w-24">
      <div
        className="h-full rounded-full transition-all duration-500"
        style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${c}, ${c}cc)` }}
      />
    </div>
  )
}
