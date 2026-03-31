import { useNavigate } from 'react-router-dom'
import { COUNTRIES } from '../../constants/countries'
import type { Prediction } from '../../types'

// Lazy-load Plotly to avoid blocking initial render
import createPlotlyComponentModule from 'react-plotly.js/factory'
import PlotlyModule from 'plotly.js-geo-dist'
const createPlotlyComponent = (createPlotlyComponentModule as any).default || createPlotlyComponentModule
const Plotly = (PlotlyModule as any).default || PlotlyModule
const Plot = createPlotlyComponent(Plotly)

export default function GlobeMap({ data }: { data: Record<string, Prediction> }) {
  const navigate = useNavigate()
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

  return (
    <Plot
      data={[{
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
      }]}
      layout={{
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
      }}
      config={{ responsive: true, displayModeBar: false }}
      onClick={(e: { points: Array<{ customdata: string }> }) => {
        const code = e.points[0]?.customdata
        if (code) navigate(`/country/${code}`)
      }}
      className="w-full"
    />
  )
}
