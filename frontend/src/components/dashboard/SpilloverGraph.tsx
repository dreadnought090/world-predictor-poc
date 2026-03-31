import { useMemo, useRef, useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { COUNTRIES } from '../../constants/countries'
import { useAllPredictions } from '../../api/queries'

interface Relation {
  a: string
  b: string
  type: 'TRADE' | 'ALLIANCE' | 'RIVALRY'
  strength: number
}

// Hardcoded from intercountry.py DEFAULT_RELATIONS
const RELATIONS: Relation[] = [
  // Trade
  { a: 'US', b: 'CN', type: 'TRADE', strength: 0.8 },
  { a: 'US', b: 'MX', type: 'TRADE', strength: 0.7 },
  { a: 'US', b: 'JP', type: 'TRADE', strength: 0.6 },
  { a: 'US', b: 'DE', type: 'TRADE', strength: 0.6 },
  { a: 'US', b: 'GB', type: 'TRADE', strength: 0.6 },
  { a: 'US', b: 'KR', type: 'TRADE', strength: 0.5 },
  { a: 'CN', b: 'JP', type: 'TRADE', strength: 0.6 },
  { a: 'CN', b: 'KR', type: 'TRADE', strength: 0.6 },
  { a: 'CN', b: 'AU', type: 'TRADE', strength: 0.5 },
  { a: 'CN', b: 'BR', type: 'TRADE', strength: 0.5 },
  { a: 'CN', b: 'DE', type: 'TRADE', strength: 0.5 },
  { a: 'DE', b: 'FR', type: 'TRADE', strength: 0.7 },
  { a: 'DE', b: 'GB', type: 'TRADE', strength: 0.5 },
  { a: 'JP', b: 'KR', type: 'TRADE', strength: 0.5 },
  { a: 'IN', b: 'SA', type: 'TRADE', strength: 0.5 },
  { a: 'IN', b: 'US', type: 'TRADE', strength: 0.4 },
  { a: 'RU', b: 'CN', type: 'TRADE', strength: 0.5 },
  { a: 'RU', b: 'IN', type: 'TRADE', strength: 0.4 },
  { a: 'SA', b: 'CN', type: 'TRADE', strength: 0.5 },
  { a: 'ID', b: 'CN', type: 'TRADE', strength: 0.5 },
  { a: 'NG', b: 'GB', type: 'TRADE', strength: 0.4 },
  { a: 'TR', b: 'DE', type: 'TRADE', strength: 0.5 },
  // Alliances
  { a: 'US', b: 'GB', type: 'ALLIANCE', strength: 0.9 },
  { a: 'US', b: 'JP', type: 'ALLIANCE', strength: 0.8 },
  { a: 'US', b: 'KR', type: 'ALLIANCE', strength: 0.8 },
  { a: 'US', b: 'AU', type: 'ALLIANCE', strength: 0.7 },
  { a: 'US', b: 'DE', type: 'ALLIANCE', strength: 0.7 },
  { a: 'US', b: 'FR', type: 'ALLIANCE', strength: 0.7 },
  { a: 'US', b: 'TR', type: 'ALLIANCE', strength: 0.5 },
  { a: 'DE', b: 'FR', type: 'ALLIANCE', strength: 0.8 },
  { a: 'GB', b: 'AU', type: 'ALLIANCE', strength: 0.7 },
  { a: 'RU', b: 'CN', type: 'ALLIANCE', strength: 0.5 },
  { a: 'SA', b: 'US', type: 'ALLIANCE', strength: 0.5 },
  // Rivalries
  { a: 'US', b: 'CN', type: 'RIVALRY', strength: 0.6 },
  { a: 'US', b: 'RU', type: 'RIVALRY', strength: 0.7 },
  { a: 'IN', b: 'PK', type: 'RIVALRY', strength: 0.8 },
  { a: 'IN', b: 'CN', type: 'RIVALRY', strength: 0.5 },
  { a: 'JP', b: 'CN', type: 'RIVALRY', strength: 0.5 },
  { a: 'KR', b: 'CN', type: 'RIVALRY', strength: 0.3 },
  { a: 'SA', b: 'TR', type: 'RIVALRY', strength: 0.4 },
  { a: 'EG', b: 'TR', type: 'RIVALRY', strength: 0.4 },
]

const TYPE_COLORS = { TRADE: '#22d3ee', ALLIANCE: '#22c55e', RIVALRY: '#ef4444' }
const TYPE_DASH = { TRADE: '', ALLIANCE: '8 4', RIVALRY: '4 4' }

interface NodePos { x: number; y: number }

function layoutNodes(width: number, height: number): Record<string, NodePos> {
  const codes = Object.keys(COUNTRIES)
  const cx = width / 2, cy = height / 2
  const radius = Math.min(width, height) * 0.38
  const positions: Record<string, NodePos> = {}
  codes.forEach((code, i) => {
    const angle = (i / codes.length) * Math.PI * 2 - Math.PI / 2
    positions[code] = { x: cx + Math.cos(angle) * radius, y: cy + Math.sin(angle) * radius }
  })
  return positions
}

const FILTER_OPTIONS = ['ALL', 'TRADE', 'ALLIANCE', 'RIVALRY'] as const

export default function SpilloverGraph() {
  const svgRef = useRef<SVGSVGElement>(null)
  const [filter, setFilter] = useState<typeof FILTER_OPTIONS[number]>('ALL')
  const [hovered, setHovered] = useState<string | null>(null)
  const { data: predictions } = useAllPredictions()

  const width = 700, height = 500
  const positions = useMemo(() => layoutNodes(width, height), [])

  const filteredRelations = filter === 'ALL' ? RELATIONS : RELATIONS.filter(r => r.type === filter)
  const hoveredRelations = hovered
    ? filteredRelations.filter(r => r.a === hovered || r.b === hovered)
    : filteredRelations

  return (
    <div className="glass p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
          Inter-Country Relations Network
        </h3>
        <div className="flex gap-1">
          {FILTER_OPTIONS.map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className="px-2 py-1 rounded text-[9px] font-semibold transition-all"
              style={{
                background: filter === f ? 'rgba(59,130,246,0.2)' : 'rgba(100,116,139,0.1)',
                color: filter === f ? '#60a5fa' : '#64748b',
              }}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      <svg
        ref={svgRef}
        viewBox={`0 0 ${width} ${height}`}
        className="w-full"
        style={{ maxHeight: 500 }}
      >
        {/* Edges */}
        {hoveredRelations.map((r, i) => {
          const pa = positions[r.a], pb = positions[r.b]
          if (!pa || !pb) return null
          const isHighlighted = !hovered || r.a === hovered || r.b === hovered
          return (
            <line
              key={`edge-${i}`}
              x1={pa.x} y1={pa.y} x2={pb.x} y2={pb.y}
              stroke={TYPE_COLORS[r.type]}
              strokeWidth={r.strength * 3}
              strokeDasharray={TYPE_DASH[r.type]}
              opacity={isHighlighted ? 0.6 : 0.1}
            />
          )
        })}

        {/* Nodes */}
        {Object.entries(positions).map(([code, pos]) => {
          const risk = predictions?.[code]?.metrics?.revolution_risk ?? 0
          const nodeColor = risk > 0.5 ? '#ef4444' : risk > 0.3 ? '#f97316' : '#22c55e'
          const isHoveredNode = hovered === code
          const isConnected = !hovered || hovered === code || filteredRelations.some(r => (r.a === hovered && r.b === code) || (r.b === hovered && r.a === code))

          return (
            <g
              key={code}
              onMouseEnter={() => setHovered(code)}
              onMouseLeave={() => setHovered(null)}
              style={{ cursor: 'pointer' }}
              opacity={isConnected ? 1 : 0.2}
            >
              {/* Risk ring */}
              <circle cx={pos.x} cy={pos.y} r={isHoveredNode ? 22 : 18} fill="none" stroke={nodeColor} strokeWidth={2} opacity={0.4} />
              {/* Node */}
              <circle cx={pos.x} cy={pos.y} r={isHoveredNode ? 18 : 14} fill="#0f1724" stroke={nodeColor} strokeWidth={1.5} />
              {/* Flag/label */}
              <text x={pos.x} y={pos.y + 1} textAnchor="middle" dominantBaseline="middle" fill="#e2e8f0" fontSize={isHoveredNode ? 12 : 9} fontWeight="bold">
                {COUNTRIES[code]?.flag || code}
              </text>
              {/* Code label */}
              <text x={pos.x} y={pos.y + (isHoveredNode ? 32 : 28)} textAnchor="middle" fill="#94a3b8" fontSize={8} fontWeight="600">
                {code}
              </text>
            </g>
          )
        })}
      </svg>

      {/* Legend */}
      <div className="flex gap-4 mt-3 justify-center">
        {Object.entries(TYPE_COLORS).map(([type, color]) => (
          <span key={type} className="flex items-center gap-1.5 text-[10px]">
            <svg width="20" height="8"><line x1="0" y1="4" x2="20" y2="4" stroke={color} strokeWidth={2} strokeDasharray={TYPE_DASH[type as keyof typeof TYPE_DASH]} /></svg>
            <span className="text-slate-400">{type}</span>
          </span>
        ))}
        <span className="text-slate-600 text-[10px] ml-2">Hover a country to highlight its connections</span>
      </div>
    </div>
  )
}
