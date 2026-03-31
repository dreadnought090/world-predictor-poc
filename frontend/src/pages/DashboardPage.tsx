import { motion } from 'framer-motion'
import { useAllPredictions } from '../api/queries'
import ThreatLevel from '../components/dashboard/ThreatLevel'
import GlobalMetricsStrip from '../components/dashboard/GlobalMetricsStrip'
import TheWire from '../components/dashboard/TheWire'
import GlobeMap from '../components/dashboard/GlobeMap'
import CountryTable from '../components/dashboard/CountryTable'
import MarketSignals from '../components/dashboard/MarketSignals'
import SpilloverGraph from '../components/dashboard/SpilloverGraph'
import ActiveEventsList from '../components/events/ActiveEventsList'
import NewsFeed from '../components/news/NewsFeed'
import { SkeletonCard, SkeletonTable } from '../components/common/Skeleton'

export default function DashboardPage() {
  const { data, isLoading } = useAllPredictions()
  const predictions = data ?? {}
  const maxDay = Math.max(0, ...Object.values(predictions).map(p => p.day))

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-4"
    >
      {/* Threat Level */}
      <ThreatLevel />

      {/* Metrics strip */}
      {isLoading ? (
        <div className="grid grid-cols-5 gap-3">{Array.from({ length: 5 }).map((_, i) => <SkeletonCard key={i} />)}</div>
      ) : (
        <GlobalMetricsStrip data={predictions} />
      )}

      {/* The Wire */}
      <TheWire />

      {/* Globe + Events + News */}
      <div className="grid grid-cols-1 lg:grid-cols-[1.6fr_1fr] gap-4">
        <div className="glass p-4">
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Global Stability Map</h3>
            <span className="font-mono text-xs text-slate-500">Day {maxDay}</span>
          </div>
          {isLoading ? <div className="h-[380px] animate-pulse bg-surface2 rounded-xl" /> : <GlobeMap data={predictions} />}
        </div>
        <div className="flex flex-col gap-4">
          <div className="glass p-4 flex-1">
            <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-3">Active Events</h3>
            <ActiveEventsList />
          </div>
          <div className="glass p-4 flex-1">
            <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-3">News Feed</h3>
            <NewsFeed />
          </div>
        </div>
      </div>

      {/* Country table */}
      <div className="glass p-4">
        <div className="flex justify-between items-center mb-3">
          <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Country Dashboard</h3>
          <span className="font-mono text-xs text-slate-500">{Object.keys(predictions).length} countries</span>
        </div>
        {isLoading ? <SkeletonTable rows={10} /> : <CountryTable data={predictions} />}
      </div>

      {/* Spillover Network */}
      <SpilloverGraph />

      {/* Market Signals */}
      <MarketSignals />
    </motion.div>
  )
}
