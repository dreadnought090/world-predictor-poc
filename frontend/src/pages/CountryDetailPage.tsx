import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, LineChart, Line, ResponsiveContainer } from 'recharts'
import { useCountryProfile } from '../api/queries'
import { COUNTRIES, CHART_COLORS } from '../constants/countries'
import MetricCard from '../components/common/MetricCard'
import Badge from '../components/common/Badge'
import { SkeletonCard } from '../components/common/Skeleton'

const pct = (v: number) => `${(v * 100).toFixed(1)}%`
const $ = (v: number) => '$' + v.toLocaleString()

export default function CountryDetailPage() {
  const { code } = useParams<{ code: string }>()
  const { data: profile, isLoading } = useCountryProfile(code!)
  const country = COUNTRIES[code!]

  if (isLoading) return (
    <div className="grid grid-cols-3 gap-4 mt-4">{Array.from({ length: 9 }).map((_, i) => <SkeletonCard key={i} />)}</div>
  )
  if (!profile) return <div className="text-center text-slate-500 mt-12">Country not found</div>

  const { metrics: m, biometrics: bio, demographics: dem, institutions, relations, news, history, consensus } = profile

  const DemoPie = ({ data, title }: { data: { label: string; pct: number }[]; title: string }) => (
    <div className="bg-surface border border-border rounded-xl p-4">
      <h4 className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 mb-3">{title}</h4>
      <ResponsiveContainer width="100%" height={180}>
        <PieChart>
          <Pie data={data.slice(0, 8)} dataKey="pct" nameKey="label" cx="50%" cy="50%" outerRadius={70} innerRadius={35} strokeWidth={0}>
            {data.slice(0, 8).map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
          </Pie>
          <Tooltip formatter={(v: any) => `${Number(v).toFixed(1)}%`} contentStyle={{ background: '#1a2332', border: '1px solid #334155', borderRadius: 8, fontSize: 11 }} />
        </PieChart>
      </ResponsiveContainer>
      <div className="flex flex-wrap gap-1.5 mt-2">
        {data.slice(0, 6).map((d, i) => (
          <span key={i} className="text-[9px] flex items-center gap-1">
            <span className="w-2 h-2 rounded-full" style={{ background: CHART_COLORS[i % CHART_COLORS.length] }} />
            {d.label.replace(/_/g, ' ')} ({d.pct}%)
          </span>
        ))}
      </div>
    </div>
  )

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }} className="flex flex-col gap-4">
      {/* Back + Header */}
      <div className="flex items-center gap-4">
        <Link to="/" className="text-xs text-slate-500 hover:text-accent transition-colors">&larr; Dashboard</Link>
      </div>

      <div className="flex items-center gap-4 mb-2">
        <span className="text-4xl">{country?.flag}</span>
        <div>
          <h2 className="text-2xl font-bold">{country?.name || code}</h2>
          <span className="text-xs text-slate-500 font-mono">Day {profile.day} &middot; {profile.agent_count} agents</span>
        </div>
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <MetricCard label="Optimism" value={m.average_optimism} color="#60a5fa" />
        <MetricCard label="Trust" value={m.social_cohesion} color="#34d399" />
        <MetricCard label="Stability" value={m.political_stability} color="#a78bfa" />
        <MetricCard label="Rev. Risk" value={m.revolution_risk} color="#fbbf24" />
        <MetricCard label="Risk Aversion" value={m.average_risk_aversion} color="#f87171" />
        <MetricCard label="Agents" value={profile.agent_count} color="#e2e8f0" format="number" />
      </div>

      {/* Reaction Distribution */}
      {consensus?.reaction_distribution && (
        <div className="glass p-5">
          <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-3">Population Reaction</h3>
          <div className="flex gap-0.5 h-8 rounded-lg overflow-hidden">
            {Object.entries(consensus.reaction_distribution).map(([reaction, pct]) => {
              const colors: Record<string, string> = {
                SUPPORT: '#22c55e', OPPOSITION: '#f97316', FEAR: '#ef4444', CONFUSION: '#a855f7', APATHY: '#64748b',
              }
              const width = pct * 100
              if (width < 0.5) return null
              return (
                <div
                  key={reaction}
                  className="relative flex items-center justify-center transition-all duration-500"
                  style={{ width: `${width}%`, background: colors[reaction] || '#64748b' }}
                  title={`${reaction}: ${(pct * 100).toFixed(1)}%`}
                >
                  {width > 8 && (
                    <span className="text-[9px] font-bold text-white/90 truncate px-1">
                      {reaction} {(pct * 100).toFixed(0)}%
                    </span>
                  )}
                </div>
              )
            })}
          </div>
          <div className="flex flex-wrap gap-3 mt-2">
            {Object.entries(consensus.reaction_distribution).map(([reaction, pct]) => {
              const colors: Record<string, string> = {
                SUPPORT: '#22c55e', OPPOSITION: '#f97316', FEAR: '#ef4444', CONFUSION: '#a855f7', APATHY: '#64748b',
              }
              return (
                <span key={reaction} className="flex items-center gap-1 text-[10px]">
                  <span className="w-2 h-2 rounded-full" style={{ background: colors[reaction] || '#64748b' }} />
                  <span className="text-slate-400">{reaction}</span>
                  <span className="font-mono font-semibold" style={{ color: colors[reaction] }}>{(pct * 100).toFixed(1)}%</span>
                </span>
              )
            })}
          </div>
        </div>
      )}

      {/* Biometrics */}
      <div className="glass p-5">
        <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-4">Biometrics</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {[
            { label: 'Avg IQ', value: bio.iq.mean.toString(), sub: `std ${bio.iq.std} | ${bio.iq.min}-${bio.iq.max}` },
            { label: 'Median Income', value: $(bio.income.median), sub: `mean ${$(bio.income.mean)}` },
            { label: 'Avg Age', value: bio.age.mean.toFixed(1), sub: `${bio.age.min}-${bio.age.max}` },
            { label: 'Optimism', value: pct(bio.optimism.mean), sub: '' },
            { label: 'Trust', value: pct(bio.trust.mean), sub: '' },
            { label: 'Risk Aversion', value: pct(bio.risk_aversion.mean), sub: '' },
          ].map((b, i) => (
            <div key={i} className="bg-bg2 rounded-lg p-3">
              <div className="text-lg font-bold font-mono text-accent2">{b.value}</div>
              <div className="text-[9px] text-slate-500 uppercase mt-0.5">{b.label}</div>
              {b.sub && <div className="text-[9px] text-slate-600 font-mono mt-0.5">{b.sub}</div>}
            </div>
          ))}
        </div>
      </div>

      {/* Demographics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <DemoPie data={dem.race} title="Race / Ethnicity" />
        <DemoPie data={dem.religion} title="Religion" />
        <DemoPie data={dem.education} title="Education" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Age histogram */}
        <div className="bg-surface border border-border rounded-xl p-4">
          <h4 className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 mb-3">Age Distribution</h4>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={dem.age}>
              <XAxis dataKey="label" tick={{ fill: '#64748b', fontSize: 10 }} />
              <YAxis tick={{ fill: '#64748b', fontSize: 10 }} tickFormatter={v => `${v}%`} />
              <Tooltip contentStyle={{ background: '#1a2332', border: '1px solid #334155', borderRadius: 8, fontSize: 11 }} />
              <Bar dataKey="pct" radius={[4, 4, 0, 0]}>
                {dem.age.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Political spectrum */}
        <div className="bg-surface border border-border rounded-xl p-4">
          <h4 className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 mb-3">Political Leaning</h4>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={dem.politics} layout="vertical">
              <XAxis type="number" tick={{ fill: '#64748b', fontSize: 10 }} tickFormatter={v => `${v}%`} />
              <YAxis type="category" dataKey="label" tick={{ fill: '#94a3b8', fontSize: 10 }} width={70} />
              <Tooltip contentStyle={{ background: '#1a2332', border: '1px solid #334155', borderRadius: 8, fontSize: 11 }} />
              <Bar dataKey="pct" radius={[0, 4, 4, 0]}>
                {dem.politics.map((d, i) => {
                  const polColors: Record<string, string> = { far_left: '#3b82f6', left: '#60a5fa', center: '#94a3b8', right: '#f97316', far_right: '#ef4444' }
                  return <Cell key={i} fill={polColors[d.label] || '#64748b'} />
                })}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Institutions */}
      {institutions.length > 0 && (
        <div className="glass p-5">
          <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-4">Institutions</h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {institutions.map((inst, i) => (
              <div key={i} className="bg-bg2 rounded-lg p-3">
                <div className="font-semibold text-sm">{inst.name}</div>
                <div className="text-[9px] text-slate-500 uppercase font-semibold">{inst.type}</div>
                <div className="mt-2 text-[11px] space-y-0.5">
                  <div>Credibility: <span className="font-mono text-accent2">{pct(inst.credibility)}</span></div>
                  <div>Power: <span className="font-mono text-accent2">{pct(inst.power)}</span></div>
                  {inst.active_policies.length > 0 && (
                    <div className="text-warning">{inst.active_policies.length} active policies</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Relations */}
      <div className="glass p-5">
        <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-4">International Relations</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[
            { title: 'Trade Partners', data: relations.trade_partners, color: '#22d3ee' },
            { title: 'Allies', data: relations.allies, color: '#34d399' },
            { title: 'Rivals', data: relations.rivals, color: '#f87171' },
          ].map(({ title, data, color }) => (
            <div key={title}>
              <h5 className="text-[9px] font-bold uppercase tracking-wider mb-2" style={{ color }}>{title}</h5>
              <div className="space-y-1.5">
                {data.map((r, i) => (
                  <Link key={i} to={`/country/${r.country}`} className="flex items-center gap-2 bg-bg2 rounded-lg px-3 py-2 text-xs hover:bg-surface2 transition-colors">
                    <span>{COUNTRIES[r.country]?.flag}</span>
                    <span className="font-medium">{r.country}</span>
                    <span className="ml-auto font-mono text-slate-500">{pct(r.strength)}</span>
                  </Link>
                ))}
                {data.length === 0 && <div className="text-[10px] text-slate-600">None</div>}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Trend chart */}
      {history.length > 0 && (
        <div className="glass p-5">
          <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-4">Metric History</h3>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={history}>
              <XAxis dataKey="day" tick={{ fill: '#64748b', fontSize: 10 }} />
              <YAxis domain={[0, 1]} tickFormatter={v => `${(v * 100).toFixed(0)}%`} tick={{ fill: '#64748b', fontSize: 10 }} />
              <Tooltip contentStyle={{ background: '#1a2332', border: '1px solid #334155', borderRadius: 8, fontSize: 11 }} formatter={(v: any) => `${(Number(v) * 100).toFixed(1)}%`} />
              <Line dataKey="average_optimism" name="Optimism" stroke="#3b82f6" strokeWidth={2} dot={false} />
              <Line dataKey="social_cohesion" name="Trust" stroke="#10b981" strokeWidth={2} dot={false} />
              <Line dataKey="revolution_risk" name="Risk" stroke="#ef4444" strokeWidth={2} dot={false} />
              <Line dataKey="political_stability" name="Stability" stroke="#8b5cf6" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* News */}
      <div className="glass p-5">
        <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-4">
          News &mdash; {country?.name || code}
        </h3>
        {news.length > 0 ? (
          <div className="space-y-0 max-h-[400px] overflow-y-auto">
            {news.map((n, i) => (
              <div key={i} className="py-2 border-b border-border/30 last:border-0">
                <div className="text-xs font-medium leading-snug">{n.title}</div>
                <div className="flex items-center gap-1.5 mt-1">
                  <Badge category={n.category} />
                  <span className="text-[10px] text-slate-500">{n.source_name}</span>
                  <span className="text-[10px] text-slate-500 font-mono">{(n.impact * 100).toFixed(0)}% impact</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-xs text-slate-500 text-center py-6">No country-specific news. Fetch news first.</div>
        )}
      </div>
    </motion.div>
  )
}
