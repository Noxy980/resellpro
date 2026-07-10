import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  TrendingUp, Package, Sparkles, Target, DollarSign, ArrowRight, Sun, Snowflake,
} from 'lucide-react'
import { api, Opportunity } from '../api'

const SEASON_ICON: Record<string, typeof Sun> = {
  été: Sun, hiver: Snowflake, printemps: Sun, automne: Sun,
}

export default function Dashboard() {
  const [data, setData] = useState<Record<string, unknown> | null>(null)

  useEffect(() => {
    api.dashboard().then(setData).catch(() => setData(null))
  }, [])

  if (!data) return <div className="p-8 text-gray-400">Chargement du tableau de bord...</div>

  const season = String(data.season || '')
  const SeasonIcon = SEASON_ICON[season] || Sun
  const opps = (data.top_opportunities as Opportunity[]) || []

  return (
    <div className="p-8 max-w-6xl mx-auto animate-fade-in">
      <div className="mb-8">
        <h1 className="page-title">Tableau de bord</h1>
        <p className="page-subtitle">Vue d'ensemble de votre activité de revente</p>
      </div>

      <div className="glass-card mb-6 flex items-center gap-4 bg-gradient-to-r from-violet-50 to-blue-50 border-violet-100">
        <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center shadow-sm">
          <SeasonIcon className="w-6 h-6 text-violet-600" />
        </div>
        <div className="flex-1">
          <p className="font-semibold text-gray-900 capitalize">Saison : {season}</p>
          <p className="text-sm text-gray-500">
            Le bot recherche : {(data.season_keywords as string[])?.join(', ')}
          </p>
        </div>
        <Link to="/opportunities" className="btn-primary text-xs">Voir opportunités</Link>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {[
          { icon: Target, label: 'Opportunités', value: String(data.opportunity_count), iconBg: 'bg-violet-100', iconColor: 'text-violet-600' },
          { icon: DollarSign, label: 'Profit potentiel', value: `€${data.potential_profit_today}`, iconBg: 'bg-emerald-100', iconColor: 'text-emerald-600' },
          { icon: Package, label: 'En stock', value: String(data.stock_count), iconBg: 'bg-gray-100', iconColor: 'text-gray-600' },
          { icon: TrendingUp, label: 'Bénéfice total', value: `€${data.total_profit}`, iconBg: 'bg-emerald-100', iconColor: 'text-emerald-600' },
        ].map(({ icon: Icon, label, value, iconBg, iconColor }) => (
          <div key={label} className="glass-card">
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${iconBg}`}>
                <Icon className={`w-5 h-5 ${iconColor}`} />
              </div>
              <div>
                <p className="text-xs text-gray-400">{label}</p>
                <p className="text-xl font-bold">{value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {Boolean(data.ai_recommendation) && (
        <div className="glass-card mb-6 border-violet-100 bg-violet-50/50">
          <div className="flex items-start gap-3">
            <Sparkles className="w-5 h-5 text-violet-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-sm text-violet-900">Conseil IA du jour</p>
              <p className="text-sm text-gray-700 mt-1">{String(data.ai_recommendation)}</p>
            </div>
          </div>
        </div>
      )}

      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-gray-900">Meilleures opportunités</h2>
          <Link to="/opportunities" className="text-sm text-gray-500 hover:text-gray-900 flex items-center gap-1">
            Tout voir <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
        {opps.length === 0 ? (
          <div className="glass-card text-center py-10 text-gray-400">
            Aucune opportunité — lancez un scan
          </div>
        ) : (
          <div className="grid gap-3">
            {opps.map(o => (
              <div key={o.id} className="glass-card flex items-center gap-4 py-3">
                <div className="w-14 h-14 rounded-lg bg-gray-100 overflow-hidden shrink-0">
                  {o.image_url && <img src={o.image_url} alt="" className="w-full h-full object-cover" />}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm truncate">{o.title}</p>
                  <p className="text-xs text-gray-400">{o.brand} · €{o.price} → €{o.estimated_resale}</p>
                </div>
                <div className="text-right shrink-0">
                  <p className="font-bold text-emerald-600">+€{o.potential_profit.toFixed(0)}</p>
                  <p className="text-xs text-gray-400">{o.score}/100</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
