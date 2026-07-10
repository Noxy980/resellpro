import { useState } from 'react'
import { Search, RefreshCw, SlidersHorizontal, Sparkles, Zap } from 'lucide-react'
import { api, Opportunity } from '../api'
import { useOpportunities } from '../hooks'
import OpportunityDetail from '../components/OpportunityDetail'
import PageShell from '../components/PageShell'

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
  const [scanMsg, setScanMsg] = useState('')
  const [showFilters, setShowFilters] = useState(false)
  const [filters, setFilters] = useState({ min_score: 0, brand: '', max_price: 0, min_profit: 0, category: '' })

  const { data, loading, refresh } = useOpportunities({ status: tab, search, ...filters })

  const scan = async () => {
    setScanning(true)
    setScanMsg('Recherche sur Vinted... (peut prendre 2-3 minutes)')
    try {
      const res = await api.scan(false)
      const s = res.stats as Record<string, unknown>
      const errors = (s.error_samples as string[]) || []
      if (res.found > 0) {
        setScanMsg(`${res.found} opportunité(s) trouvée(s) !`)
      } else if (Number(s.items_fetched) === 0 && Number(s.errors) > 0) {
        setScanMsg(
          `Vinted inaccessible depuis le serveur. ${errors[0] || 'Erreur réseau'} — Redéployez Render après la mise à jour.`
        )
      } else {
        setScanMsg(
          `Scan terminé — ${s.items_fetched || 0} annonces vues, ${s.analyzed || 0} analysées, ${s.passed || 0} validées.`
        )
      }
      refresh()
    } catch (e) {
      setScanMsg(e instanceof Error ? e.message : 'Erreur de scan — attendez que Render se réveille.')
    } finally {
      setScanning(false)
      setTimeout(() => setScanMsg(''), 12000)
    }
  }

  const tabs = [
    { id: 'active', label: 'Actives' },
    { id: 'favorite', label: 'Favoris' },
    { id: 'purchased', label: 'Achetées' },
    { id: 'rejected', label: 'Refusées' },
  ]

  return (
    <PageShell>
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-6 md:mb-8">
        <div>
          <h1 className="page-title">Opportunités</h1>
          <p className="page-subtitle">Les meilleures affaires sélectionnées par l'IA</p>
        </div>
        <button onClick={scan} disabled={scanning} className="btn-primary w-full sm:w-auto">
          <RefreshCw className={`w-4 h-4 ${scanning ? 'animate-spin' : ''}`} />
          {scanning ? 'Scan en cours...' : 'Scanner Vinted'}
        </button>
      </div>
      {scanMsg && (
        <div className="mb-4 px-4 py-3 rounded-2xl bg-violet-50 border border-violet-100 text-sm text-violet-800 font-medium">
          {scanMsg}
        </div>
      )}

      <div className="flex flex-col sm:flex-row flex-wrap items-stretch sm:items-center gap-3 mb-6">
        <div className="relative flex-1 min-w-0">
          <Search className="absolute left-4 top-3.5 w-4 h-4 text-slate-400" />
          <input className="input pl-11" placeholder="Rechercher une marque, un modèle..." value={search}
            onChange={e => setSearch(e.target.value)} />
        </div>
        <div className="flex gap-1 bg-white rounded-2xl p-1 border border-slate-200/80 shadow-soft overflow-x-auto">
          {tabs.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`px-4 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                tab === t.id ? 'bg-violet-600 text-white shadow-md' : 'text-slate-500 hover:text-slate-900'
              }`}>{t.label}</button>
          ))}
        </div>
        <button onClick={() => setShowFilters(!showFilters)} className="btn-secondary text-xs shrink-0">
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
        <div className="space-y-4">
          {[1, 2, 3].map(i => <div key={i} className="skeleton h-32 rounded-3xl" />)}
        </div>
      ) : data.length === 0 ? (
        <div className="glass-card text-center py-16 border-dashed border-2 border-slate-200">
          <div className="w-20 h-20 mx-auto mb-5 rounded-3xl bg-violet-50 flex items-center justify-center">
            <Zap className="w-10 h-10 text-violet-500" />
          </div>
          <p className="font-bold text-slate-900 text-lg">Aucune opportunité</p>
          <p className="text-sm text-slate-500 mt-2 mb-6">Lancez un scan pour découvrir les meilleures affaires</p>
          <button onClick={scan} disabled={scanning} className="btn-primary">
            <Sparkles className="w-4 h-4" /> Scanner maintenant
          </button>
        </div>
      ) : (
        <div className="grid gap-4">
          {data.map(opp => (
            <div key={opp.id} className="glass-card cursor-pointer group active:scale-[0.99]" onClick={() => setSelected(opp)}>
              <div className="flex gap-4 md:gap-5">
                <div className="w-20 h-20 md:w-28 md:h-28 rounded-2xl overflow-hidden bg-slate-100 shrink-0 ring-2 ring-white shadow-md">
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
                  <div className="flex flex-wrap items-center gap-3 md:gap-5 mt-3">
                    <div><p className="text-[10px] text-slate-400 font-medium uppercase">Achat</p><p className="font-bold">€{opp.price.toFixed(0)}</p></div>
                    <div className="text-slate-300 hidden sm:block">→</div>
                    <div><p className="text-[10px] text-slate-400 font-medium uppercase">Revente</p><p className="font-bold text-emerald-600">€{opp.estimated_resale.toFixed(0)}</p></div>
                    <div><p className="text-[10px] text-slate-400 font-medium uppercase">Profit</p><p className="font-bold text-emerald-600">+€{opp.potential_profit.toFixed(0)}</p></div>
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
    </PageShell>
  )
}
