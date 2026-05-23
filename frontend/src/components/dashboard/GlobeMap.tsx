import { useEffect, useMemo, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { COUNTRIES } from '../../constants/countries'
import type { Prediction } from '../../types'
import PlotlyModule from 'plotly.js-geo-dist'

type PlotRecord = Record<string, unknown>
type PlotlyClickEvent = { points?: Array<{ customdata?: unknown }> }
type PlotlyElement = HTMLDivElement & {
  on?: (event: 'plotly_click', handler: (event: PlotlyClickEvent) => void) => void
  removeListener?: (event: 'plotly_click', handler: (event: PlotlyClickEvent) => void) => void
}
type PlotlyApi = {
  react: (
    element: HTMLElement,
    data: PlotRecord[],
    layout: PlotRecord,
    config: PlotRecord,
  ) => Promise<unknown> | void
  purge: (element: HTMLElement) => void
}

const Plotly = PlotlyModule as PlotlyApi
const PLOT_CONFIG: PlotRecord = { responsive: true, displayModeBar: false }

export default function GlobeMap({ data }: { data: Record<string, Prediction> }) {
  const navigate = useNavigate()
  const plotRef = useRef<PlotlyElement | null>(null)

  const figure = useMemo(() => {
    const entries = Object.entries(data)
    const lats: number[] = []
    const lons: number[] = []
    const texts: string[] = []
    const colors: number[] = []
    const sizes: number[] = []
    const ids: string[] = []

    entries.forEach(([code, pred]) => {
      const c = COUNTRIES[code]
      if (!c) return
      const risk = pred.metrics.revolution_risk ?? 0
      lats.push(c.coords[0])
      lons.push(c.coords[1])
      texts.push(`<b>${c.flag} ${c.name}</b><br>Risk: ${(risk * 100).toFixed(1)}%<br>Optimism: ${(pred.metrics.average_optimism * 100).toFixed(1)}%`)
      colors.push(risk)
      sizes.push(14 + risk * 26)
      ids.push(code)
    })

    return {
      data: [{
        type: 'scattergeo' as const,
        lat: lats,
        lon: lons,
        text: texts,
        customdata: ids,
        hoverinfo: 'text' as const,
        marker: {
          size: sizes,
          color: colors,
          colorscale: [[0, '#10b981'], [0.3, '#22d3ee'], [0.5, '#f59e0b'], [0.7, '#ef4444'], [1, '#7f1d1d']],
          cmin: 0,
          cmax: 1,
          colorbar: { title: { text: 'Risk', font: { color: '#94a3b8', size: 10 } }, tickformat: '.0%', len: 0.5, thickness: 10, outlinewidth: 0, bgcolor: 'transparent', tickfont: { color: '#64748b', size: 9 } },
          line: { width: 1.5, color: 'rgba(255,255,255,0.25)' },
          opacity: 0.9,
        },
        mode: 'markers' as const,
      }] satisfies PlotRecord[],
      layout: {
        geo: {
          scope: 'world' as const,
          showland: true,
          landcolor: '#1a2332',
          showocean: true,
          oceancolor: '#0c1120',
          showcountries: true,
          countrycolor: '#1e293b',
          showframe: false,
          bgcolor: 'transparent',
          projection: { type: 'natural earth' as const },
          coastlinecolor: '#1e293b',
          lonaxis: { range: [-140, 170] },
          lataxis: { range: [-55, 72] },
        },
        paper_bgcolor: 'transparent',
        margin: { l: 0, r: 0, t: 0, b: 0 },
        height: 380,
        font: { color: '#94a3b8' },
        hoverlabel: { bgcolor: '#1a2332', bordercolor: '#334155', font: { family: 'Inter', color: '#f1f5f9', size: 11 } },
      } satisfies PlotRecord,
    }
  }, [data])

  useEffect(() => {
    const element = plotRef.current
    if (!element) return

    const handleClick = (event: PlotlyClickEvent) => {
      const code = event.points?.[0]?.customdata
      if (typeof code === 'string') navigate(`/country/${code}`)
    }

    Promise.resolve(Plotly.react(element, figure.data, figure.layout, PLOT_CONFIG))
      .then(() => element.on?.('plotly_click', handleClick))

    return () => {
      element.removeListener?.('plotly_click', handleClick)
      Plotly.purge(element)
    }
  }, [figure, navigate])

  return <div ref={plotRef} className="w-full" style={{ height: 380 }} />
}
