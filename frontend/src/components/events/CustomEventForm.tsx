import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import client from '../../api/client'
import { COUNTRIES } from '../../constants/countries'

const EVENT_TYPES = [
  'ELECTION', 'COUP', 'WAR', 'CIVIL_UNREST', 'PANDEMIC', 'NATURAL_DISASTER',
  'SANCTIONS', 'TRADE_WAR', 'ECONOMIC_CRISIS', 'TERROR_ATTACK', 'PEACE_DEAL', 'TECH_BREAKTHROUGH',
]

const EVENT_COLORS: Record<string, string> = {
  ELECTION: '#3b82f6', COUP: '#ef4444', WAR: '#dc2626', CIVIL_UNREST: '#f97316',
  PANDEMIC: '#a855f7', NATURAL_DISASTER: '#eab308', SANCTIONS: '#f59e0b',
  TRADE_WAR: '#f97316', ECONOMIC_CRISIS: '#ef4444', TERROR_ATTACK: '#dc2626',
  PEACE_DEAL: '#22c55e', TECH_BREAKTHROUGH: '#06b6d4',
}

export default function CustomEventForm({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient()
  const [eventType, setEventType] = useState('ECONOMIC_CRISIS')
  const [name, setName] = useState('')
  const [countries, setCountries] = useState<string[]>(['US'])
  const [magnitude, setMagnitude] = useState(0.7)
  const [duration, setDuration] = useState(14)

  const injectMutation = useMutation({
    mutationFn: () => client.post('/events/inject', null, {
      params: {
        event_type: eventType,
        name: name || `Custom ${eventType.replace(/_/g, ' ')}`,
        affected_countries: countries.join(','),
        magnitude,
        duration_days: duration,
      },
    }),
    onSuccess: () => {
      toast.success(`Custom event injected: ${name || eventType}`)
      qc.invalidateQueries({ queryKey: ['events'] })
      qc.invalidateQueries({ queryKey: ['predictions'] })
      qc.invalidateQueries({ queryKey: ['global'] })
      onClose()
    },
    onError: () => toast.error('Failed to inject event'),
  })

  const toggleCountry = (code: string) => {
    setCountries(prev => prev.includes(code) ? prev.filter(c => c !== code) : [...prev, code])
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        className="bg-[#0f1724] border border-border rounded-2xl p-6 w-full max-w-xl max-h-[85vh] overflow-y-auto"
      >
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-lg font-bold">Custom Event Injection</h3>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-300 text-lg">&times;</button>
        </div>

        <div className="flex flex-col gap-4">
          {/* Event Type */}
          <div>
            <label className="text-[10px] text-slate-500 uppercase font-semibold">Event Type</label>
            <div className="grid grid-cols-3 gap-1.5 mt-1.5">
              {EVENT_TYPES.map(t => (
                <button
                  key={t}
                  onClick={() => setEventType(t)}
                  className="px-2 py-1.5 rounded-lg text-[10px] font-semibold transition-all border"
                  style={{
                    borderColor: eventType === t ? EVENT_COLORS[t] : 'transparent',
                    background: eventType === t ? EVENT_COLORS[t] + '18' : 'rgba(100,116,139,0.1)',
                    color: eventType === t ? EVENT_COLORS[t] : '#94a3b8',
                  }}
                >
                  {t.replace(/_/g, ' ')}
                </button>
              ))}
            </div>
          </div>

          {/* Name */}
          <div>
            <label className="text-[10px] text-slate-500 uppercase font-semibold">Event Name</label>
            <input
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder={`e.g. ${eventType.replace(/_/g, ' ')} in selected countries`}
              className="mt-1 w-full bg-bg2 border border-border rounded-lg px-3 py-2 text-sm text-slate-200 focus:border-accent focus:outline-none"
            />
          </div>

          {/* Affected Countries */}
          <div>
            <label className="text-[10px] text-slate-500 uppercase font-semibold">
              Affected Countries <span className="text-slate-600">({countries.length} selected)</span>
            </label>
            <div className="grid grid-cols-5 gap-1 mt-1.5">
              {Object.values(COUNTRIES).map(c => (
                <button
                  key={c.code}
                  onClick={() => toggleCountry(c.code)}
                  className="px-2 py-1 rounded text-[10px] transition-all"
                  style={{
                    background: countries.includes(c.code) ? 'rgba(59,130,246,0.2)' : 'rgba(100,116,139,0.1)',
                    color: countries.includes(c.code) ? '#60a5fa' : '#64748b',
                    border: countries.includes(c.code) ? '1px solid rgba(59,130,246,0.3)' : '1px solid transparent',
                  }}
                >
                  {c.flag} {c.code}
                </button>
              ))}
            </div>
          </div>

          {/* Magnitude + Duration */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-[10px] text-slate-500 uppercase font-semibold">
                Magnitude: <span className="text-accent2 font-mono">{(magnitude * 100).toFixed(0)}%</span>
              </label>
              <input
                type="range" min={0.1} max={1} step={0.05} value={magnitude}
                onChange={e => setMagnitude(+e.target.value)}
                className="mt-2 w-full accent-accent"
              />
              <div className="flex justify-between text-[8px] text-slate-600 mt-0.5">
                <span>Minor</span><span>Moderate</span><span>Major</span>
              </div>
            </div>
            <div>
              <label className="text-[10px] text-slate-500 uppercase font-semibold">
                Duration: <span className="text-accent2 font-mono">{duration} days</span>
              </label>
              <input
                type="range" min={3} max={180} step={1} value={duration}
                onChange={e => setDuration(+e.target.value)}
                className="mt-2 w-full accent-accent"
              />
              <div className="flex justify-between text-[8px] text-slate-600 mt-0.5">
                <span>3d</span><span>90d</span><span>180d</span>
              </div>
            </div>
          </div>

          {/* Preview */}
          <div className="bg-bg2 rounded-lg p-3 text-[11px]">
            <span className="text-slate-500">Preview: </span>
            <span style={{ color: EVENT_COLORS[eventType] }}>{eventType.replace(/_/g, ' ')}</span>
            <span className="text-slate-400"> affecting </span>
            <span className="text-accent2">{countries.join(', ')}</span>
            <span className="text-slate-400"> at </span>
            <span className="text-accent2 font-mono">{(magnitude * 100).toFixed(0)}%</span>
            <span className="text-slate-400"> magnitude for </span>
            <span className="text-accent2 font-mono">{duration}</span>
            <span className="text-slate-400"> days</span>
          </div>

          {/* Submit */}
          <button
            onClick={() => injectMutation.mutate()}
            disabled={countries.length === 0 || injectMutation.isPending}
            className="w-full px-6 py-2.5 rounded-lg text-sm font-semibold bg-gradient-to-r from-red-600 to-orange-600 text-white hover:shadow-[0_0_20px_rgba(239,68,68,0.3)] transition-all disabled:opacity-50"
          >
            {injectMutation.isPending ? 'Injecting...' : 'Inject Event'}
          </button>
        </div>
      </motion.div>
    </motion.div>
  )
}
