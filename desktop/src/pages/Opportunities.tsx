import { useState } from 'react'
import { Search, RefreshCw, SlidersHorizontal, Sparkles } from 'lucide-react'
import { api, Opportunity } from '../api'
import { useOpportunities } from '../hooks'
import OpportunityDetail from '../components/OpportunityDetail'

function ScoreBadge({ score }: { score: number }) {
  const cls = score >= 80 ? 'score-high' : score >= 70 ? 'score-mid' : 'score-low'
  return <div className={cls}>{score}</div>
}

function DemandBadge({ level }: { level: string }) {
  const cls = level === 'high' ? 'badge-high' : level === 'medium' ? 'badge-medium' : 'badge-low'
  const label = level === 'high' ? 'Forte' : level === 'medium' ? 'Moyenne' : 'Faible'
  return <span className={cls}>{label}</span>
}

export default function Opportunities() {
  const [search, setSearch] = useState('')
  const [tab, setTab] = useState('active')
  const [selected, setSelected] = useState<Opportunity | null>(null)
  const [scanning, setScanning] = useState(false)
  const [showFilters, setShowFilters] = useState(false)
  const [filters, setFilters] = useState({ min_score: 0, brand: '', max_price: 0, min_profit: 0, category: '' })

  const { data, loading, refresh } = useOpportunities({ status: tab, search, ...filters })

  const scan = async () => {
    setScanning(true)
    try { await api.scan(); refresh() } finally { setScanning(false) }
  }

  const tabs = [
    { id: 'active', label: 'Actives' },
    { id: 'favorite', label: 'Favoris' },
    { id: 'purchased', label: 'Achetées' },
    { id: 'rejected', label: 'Refusées' },
  ]

  return (
    <div className="p-8 max-w-6xl mx-auto animate-fade-in">
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="page-title">Opportunités</h1>
          <p className="page-subtitle">Les meilleures affaires sélectionnées par l'IA</p>
        </div>
        <button onClick={scan} disabled={scanning} className="btn-primary">
          <RefreshCw className={`w-4 h-4 ${scanning ? 'animate-spin' : ''}`} />
          {scanning ? 'Analyse...' : 'Scanner'}
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-3 mb-6">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3.5 top-3 w-4 h-4 text-gray-400" />
          <input className="input pl-10" placeholder="Rechercher..." value={search}
            onChange={e => setSearch(e.target.value)} />
        </div>
        <div className="flex gap-1 bg-white/60 rounded-xl p-1 border border-gray-100">
          {tabs.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                tab === t.id ? 'bg-gray-900 text-white shadow-sm' : 'text-gray-500 hover:text-gray-900'
              }`}>{t.label}</button>
          ))}
        </div>
        <button onClick={() => setShowFilters(!showFilters)} className="btn-secondary text-xs">
          <SlidersHorizontal className="w-3.5 h-3.5" />Filtres
        </button>
      </div>

      {showFilters && (
        <div className="glass-card mb-6 grid grid-cols-2 md:grid-cols-5 gap-3 animate-fade-in">
          <div>
            <label className="text-xs text-gray-500">Score min</label>
            <input type="number" className="input mt-1" value={filters.min_score}
              onChange={e => setFilters(f => ({ ...f, min_score: +e.target.value }))} />
          </div>
          <div>
            <label className="text-xs text-gray-500">Marque</label>
            <input className="input mt-1" value={filters.brand}
              onChange={e => setFilters(f => ({ ...f, brand: e.target.value }))} />
          </div>
          <div>
            <label className="text-xs text-gray-500">Prix max €</label>
            <input type="number" className="input mt-1" value={filters.max_price || ''}
              onChange={e => setFilters(f => ({ ...f, max_price: +e.target.value }))} />
          </div>
          <div>
            <label className="text-xs text-gray-500">Profit min €</label>
            <input type="number" className="input mt-1" value={filters.min_profit || ''}
              onChange={e => setFilters(f => ({ ...f, min_profit: +e.target.value }))} />
          </div>
          <div>
            <label className="text-xs text-gray-500">Catégorie</label>
            <input className="input mt-1" value={filters.category}
              onChange={e => setFilters(f => ({ ...f, category: e.target.value }))} />
          </div>
        </div>
      )}

      {loading ? (
        <div className="text-center py-20 text-gray-400">Chargement...</div>
      ) : data.length === 0 ? (
        <div className="text-center py-20">
          <Sparkles className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">Aucune opportunité pour le moment</p>
          <p className="text-sm text-gray-400 mt-1">Cliquez sur Scanner pour trouver des affaires</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {data.map(opp => (
            <div key={opp.id} className="glass-card cursor-pointer group" onClick={() => setSelected(opp)}>
              <div className="flex gap-5">
                <div className="w-28 h-28 rounded-xl overflow-hidden bg-gray-100 shrink-0">
                  {opp.image_url
                    ? <img src={opp.image_url} alt="" className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
                    : <div className="w-full h-full flex items-center justify-center text-gray-300 text-xs">Photo</div>}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-medium text-gray-900 truncate">{opp.title}</p>
                      <p className="text-xs text-gray-400 mt-0.5">{opp.brand} · {opp.model} · {opp.size}</p>
                    </div>
                    <ScoreBadge score={opp.score} />
                  </div>
                  <div className="flex items-center gap-5 mt-3">
                    <div><p className="text-[11px] text-gray-400">Achat</p><p className="font-semibold">€{opp.price.toFixed(0)}</p></div>
                    <div className="text-gray-300">→</div>
                    <div><p className="text-[11px] text-gray-400">Revente</p><p className="font-semibold text-emerald-600">€{opp.estimated_resale.toFixed(0)}</p></div>
                    <div><p className="text-[11px] text-gray-400">Profit</p><p className="font-semibold text-emerald-600">+€{opp.potential_profit.toFixed(0)}</p></div>
                    <div><p className="text-[11px] text-gray-400">Vitesse</p><p className="text-sm">{opp.selling_speed}</p></div>
                  </div>
                  <div className="flex items-center gap-2 mt-2.5">
                    <DemandBadge level={opp.demand_level} />
                    <span className="text-xs text-gray-400 flex items-center gap-1">
                      <Sparkles className="w-3 h-3 text-violet-400" />{opp.quick_sale_probability.toFixed(0)}% vente rapide
                    </span>
                  </div>
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-3 line-clamp-1 border-t border-gray-100 pt-3">{opp.why_buy}</p>
            </div>
          ))}
        </div>
      )}

      {selected && <OpportunityDetail opportunity={selected} onClose={() => setSelected(null)} onAction={() => { setSelected(null); refresh() }} />}
    </div>
  )
}
