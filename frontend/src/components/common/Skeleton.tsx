export function SkeletonLine({ width = '100%', height = '12px' }: { width?: string; height?: string }) {
  return <div className="animate-pulse bg-surface2 rounded" style={{ width, height }} />
}

export function SkeletonCard() {
  return (
    <div className="glass p-4 space-y-3 animate-pulse">
      <div className="h-3 bg-surface2 rounded w-1/3" />
      <div className="h-8 bg-surface2 rounded w-2/3" />
      <div className="h-3 bg-surface2 rounded w-1/2" />
    </div>
  )
}

export function SkeletonTable({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-2 animate-pulse">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-10 bg-surface2 rounded" />
      ))}
    </div>
  )
}
