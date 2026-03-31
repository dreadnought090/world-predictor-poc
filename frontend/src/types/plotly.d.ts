declare module 'react-plotly.js/factory' {
  import { ComponentType } from 'react'
  export default function createPlotlyComponent(plotly: any): ComponentType<any>
}
declare module 'plotly.js-geo-dist' {
  const Plotly: any
  export default Plotly
}
