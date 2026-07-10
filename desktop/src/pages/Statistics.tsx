import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, Area, AreaChart } from 'recharts'
import { DollarSign, Package, TrendingUp, Target, Percent } from 'lucide-react'
import { api, Stats } from '../api'

function StatCard({ icon: Icon, label, value, sub, color = 'gray' }: {
  icon: React.ElementType; label: string; value: string; sub?: string; color?: string
}) {
  const colors: Record<string, string> = {
    gray: 'bg-gray-100 text-gray-700',
    green: 'bg-emerald-100 text-emerald-700',
    violet: 'bg-violet-100 text-violet-700',
    amber: 'bg-amber-100 text-amber-700',
  }
  return (
    <div className="glass-card">
      <div className="flex items-center gap-3">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${colors[color]}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <p className="text-xs text-gray-400">{label}</p>
          <p className="text-xl font-bold text-gray-900">{value}</p>
          {sub && <p className="text-xs text-gray-400">{sub}</p>}
        </div>
      </div>
    </div>
  )
}

export default function Statistics() {
  const [stats, setStats] = useState<Stats | null>(null)
  useEffect(() => { api.statistics().then(setStats).catch(() => {}) }, [])

  if (!stats) return <div className="p-8 text-gray-400">Chargement...</div>

  const roi = stats.total_items_sold > 0 && stats.avg_profit > 0
    ? ((stats.avg_profit / (stats.avg_profit + stats.avg_margin)) * 100).toFixed(0) : '0'

  return (
    <div className="p-8 max-w-5xl mx-auto animate-fade-in">
      <div className="mb-8">
        <h1 className="page-title">Statistiques</h1>
        <p className="page-subtitle">Performance et évolution de votre activité</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
        <StatCard icon={DollarSign} label="Bénéfice total" value={`€${stats.total_profit.toFixed(0)}`} color="green" />
        <StatCard icon={Package} label="Ventes" value={String(stats.total_items_sold)} color="gray" />
        <StatCard icon={TrendingUp} label="Profit moyen" value={`€${stats.avg_profit.toFixed(0)}`} sub={`${stats.avg_margin.toFixed(0)}% marge`} color="violet" />
        <StatCard icon={Target} label="Taux de succès" value={`${stats.success_rate.toFixed(0)}%`} color="amber" />
        <StatCard icon={Percent} label="ROI moyen" value={`${roi}%`} color="green" />
      </div>

      {stats.best_brands.length > 0 && (
        <div className="glass-card mb-6">
          <h3 className="font-medium mb-4 text-gray-900">Meilleures marques</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={stats.best_brands}>
              <XAxis dataKey="brand" tick={{ fill: '#9ca3af', fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#9ca3af', fontSize: 12 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: 12, boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }} />
              <Bar dataKey="profit" fill="#111827" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {stats.profit_timeline.length > 0 && (
        <div className="glass-card">
          <h3 className="font-medium mb-4 text-gray-900">Évolution des bénéfices</h3>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={stats.profit_timeline}>
              <defs>
                <linearGradient id="profitGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#10b981" stopOpacity={0.2} />
                  <stop offset="100%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="date" tick={{ fill: '#9ca3af', fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#9ca3af', fontSize: 12 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: 12 }} />
              <Area type="monotone" dataKey="profit" stroke="#10b981" fill="url(#profitGrad)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {stats.total_items_sold === 0 && (
        <div className="text-center py-12 text-gray-400">
          <p>Marquez des articles comme vendus dans Stock pour voir vos statistiques</p>
        </div>
      )}
    </div>
  )
}
