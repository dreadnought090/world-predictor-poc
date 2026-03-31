import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import { useFetchNews, useSimulateBatch, useInjectPresetEvent } from '../api/mutations'
import { useUIStore } from '../stores/uiStore'
import { COUNTRIES } from '../constants/countries'
import CustomEventForm from '../components/events/CustomEventForm'
import Fuse from 'fuse.js'

const fuse = new Fuse(Object.values(COUNTRIES), { keys: ['name', 'code'], threshold: 0.3 })

export default function Header() {
  const navigate = useNavigate()
  const { searchQuery, setSearch } = useUIStore()
  const [eventKey, setEventKey] = useState('')
  const fetchNews = useFetchNews()
  const simBatch = useSimulateBatch()
  const injectEvent = useInjectPresetEvent()
  const [searchOpen, setSearchOpen] = useState(false)
  const [showCustomEvent, setShowCustomEvent] = useState(false)

  const results = searchQuery ? fuse.search(searchQuery).map(r => r.item) : []

  return (
    <>
      <header className="sticky top-0 z-50 bg-[#06080f]/85 backdrop-blur-xl border-b border-white/[0.08] px-4 h-13 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-gradient-to-br from-accent to-purple rounded-lg flex items-center justify-center text-sm font-extrabold text-white">W</div>
            <h1 className="text-[15px] font-bold tracking-tight">
              <span className="bg-gradient-to-r from-accent2 to-cyan bg-clip-text text-transparent">WORLD</span>
              {' '}PREDICTOR
            </h1>
          </Link>
          {/* Nav links */}
          <nav className="hidden md:flex items-center gap-1 ml-2">
            <Link to="/" className="px-2 py-1 text-[10px] text-slate-500 hover:text-slate-300 font-semibold uppercase tracking-wider transition-colors">Dashboard</Link>
            <Link to="/scenarios" className="px-2 py-1 text-[10px] text-slate-500 hover:text-slate-300 font-semibold uppercase tracking-wider transition-colors">Scenarios</Link>
            <Link to="/policies" className="px-2 py-1 text-[10px] text-slate-500 hover:text-slate-300 font-semibold uppercase tracking-wider transition-colors">Policies</Link>
            <Link to="/validation" className="px-2 py-1 text-[10px] text-slate-500 hover:text-slate-300 font-semibold uppercase tracking-wider transition-colors">Validation</Link>
          </nav>
        </div>

        <div className="flex items-center gap-1.5">
          {/* Search */}
          <div className="relative">
            <input
              type="text"
              placeholder="Search countries..."
              value={searchQuery}
              onChange={e => { setSearch(e.target.value); setSearchOpen(true) }}
              onFocus={() => setSearchOpen(true)}
              onBlur={() => setTimeout(() => setSearchOpen(false), 200)}
              className="w-40 bg-surface border border-border rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder:text-slate-600 focus:border-accent focus:outline-none transition-colors"
            />
            {searchOpen && results.length > 0 && (
              <div className="absolute top-full mt-1 left-0 w-56 bg-surface border border-border rounded-lg shadow-xl z-50 py-1 max-h-60 overflow-y-auto">
                {results.map(c => (
                  <button
                    key={c.code}
                    onMouseDown={() => { navigate(`/country/${c.code}`); setSearch(''); setSearchOpen(false) }}
                    className="w-full text-left px-3 py-2 text-sm hover:bg-surface2 flex items-center gap-2"
                  >
                    <span className="text-base">{c.flag}</span>
                    <span>{c.name}</span>
                    <span className="text-slate-500 ml-auto font-mono text-xs">{c.code}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Event inject (preset) */}
          <select
            value={eventKey}
            onChange={e => setEventKey(e.target.value)}
            className="bg-surface border border-border rounded-lg px-2 py-1.5 text-xs text-slate-300 cursor-pointer"
          >
            <option value="">Inject Event</option>
            <option value="financial_crash">Financial Crash</option>
            <option value="pandemic_outbreak">Pandemic</option>
            <option value="ukraine_war">Armed Conflict</option>
            <option value="us_election">US Election</option>
            <option value="middle_east_peace">Peace Deal</option>
            <option value="ai_breakthrough">AI Breakthrough</option>
          </select>
          <button
            onClick={() => { if (eventKey) { injectEvent.mutate(eventKey); setEventKey('') } }}
            className="px-3 py-1.5 rounded-lg text-xs font-medium border border-danger/50 text-danger hover:bg-danger/10 transition-colors"
          >
            Inject
          </button>

          {/* Custom Event */}
          <button
            onClick={() => setShowCustomEvent(true)}
            className="px-3 py-1.5 rounded-lg text-xs font-medium border border-orange-500/50 text-orange-400 hover:bg-orange-500/10 transition-colors"
          >
            Custom
          </button>

          <button
            onClick={() => fetchNews.mutate()}
            disabled={fetchNews.isPending}
            className="px-3 py-1.5 rounded-lg text-xs font-medium bg-gradient-to-r from-accent to-blue-700 text-white hover:shadow-[0_0_20px_rgba(59,130,246,0.3)] transition-all disabled:opacity-50"
          >
            {fetchNews.isPending ? 'Loading...' : 'Fetch & Simulate'}
          </button>

          <button
            onClick={() => simBatch.mutate(10)}
            disabled={simBatch.isPending}
            className="px-3 py-1.5 rounded-lg text-xs font-medium bg-surface2 border border-border text-slate-300 hover:border-accent hover:bg-accent/10 transition-colors disabled:opacity-50"
          >
            +10 Days
          </button>
        </div>
      </header>

      {/* Custom Event Modal */}
      <AnimatePresence>
        {showCustomEvent && <CustomEventForm onClose={() => setShowCustomEvent(false)} />}
      </AnimatePresence>
    </>
  )
}
