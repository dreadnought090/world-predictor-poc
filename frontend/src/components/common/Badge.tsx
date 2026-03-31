import { CAT_COLORS } from '../../constants/countries'

export default function Badge({ category }: { category: string }) {
  const color = CAT_COLORS[category] || '#64748b'
  return (
    <span
      className="px-1.5 py-0.5 rounded text-[9px] font-bold tracking-wide"
      style={{ background: `${color}22`, color }}
    >
      {category}
    </span>
  )
}
