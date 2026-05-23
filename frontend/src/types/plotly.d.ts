declare module 'react-plotly.js/factory' {
  import { ComponentType } from 'react'
  export default function createPlotlyComponent(plotly: unknown): ComponentType<Record<string, unknown>>
}
declare module 'plotly.js-geo-dist' {
  const Plotly: unknown
  export default Plotly
}
