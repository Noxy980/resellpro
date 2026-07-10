import { useEffect, useRef, useState } from 'react'
import { Search, RefreshCw, SlidersHorizontal, Sparkles, Zap, Square, Clock } from 'lucide-react'
import { api, Opportunity, ScanEvent } from '../api'
import { useOpportunities } from '../hooks'
import OpportunityDetail from '../components/OpportunityDetail'
import PageShell from '../components/PageShell'

const SCAN_DURATIONS = [
  { value: 5, label: '5 min' },
  { value: 15, label: '15 min' },
  { value: 30, label: '30 min' },
  { value: 60, label: '1 h' },
]

function ScoreBadge({ score }: { score: number }) {
  const cls = score >= 80 ? 'score-high' : score >= 70 ? 'score-mid' : 'score-low'
  return <div className={cls}>{score}</div>
}

function DemandBadge({ level }: { level: string }) {
  const cls = level === 'high' ? 'badge-high' : level === 'medium' ? 'badge-medium' : 'badge-low'
  const label = level === 'high' ? 'Forte' : level === 'medium' ? 'Moyenne' : 'Faible'
  return <span className={cls}>{label}</span>
}

function formatTime(seconds: number) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

function OppCard({ opp, onSelect }: { opp: Opportunity; onSelect: () => void }) {
  return (
    <div className="glass-card cursor-pointer group active:scale-[0.99]" onClick={onSelect}>
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
                    {opp.comparable_median != null && opp.comparable_median > 0 && (
                      <div><p className="text-[10px] text-slate-400 font-medium uppercase">Marché</p><p className="font-bold text-slate-600">€{opp.comparable_median.toFixed(0)}</p></div>
                    )}
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
  )
}

export default function Opportunities() {
  const [search, setSearch] = useState('')
  const [tab, setTab] = useState('active')
  const [selected, setSelected] = useState<Opportunity | null>(null)
  const [scanning, setScanning] = useState(false)
  const [scanDuration, setScanDuration] = useState(15)
  const [scanProgress, setScanProgress] = useState<ScanEvent | null>(null)
  const [liveFound, setLiveFound] = useState<Opportunity[]>([])
  const [scanMsg, setScanMsg] = useState('')
  const [showFilters, setShowFilters] = useState(false)
  const [filters, setFilters] = useState({ min_score: 0, brand: '', max_price: 0, min_profit: 0, category: '' })
  const stopScanRef = useRef<(() => void) | null>(null)

  const { data, loading, refresh } = useOpportunities({ status: tab, search, ...filters })

  useEffect(() => {
    api.settings().then(s => {
      const mins = Number(s.default_scan_minutes)
      if (mins >= 1) setScanDuration(mins)
    }).catch(() => {})
    return () => { stopScanRef.current?.() }
  }, [])

  const displayList = (() => {
    const ids = new Set(data.map(o => o.id))
    const extra = liveFound.filter(o => !ids.has(o.id))
    return [...extra, ...data]
  })()

  const startScan = () => {
    stopScanRef.current?.()
    setScanning(true)
    setLiveFound([])
    setScanProgress(null)
    setScanMsg(`Scan ${scanDuration} min en cours…`)

    const stop = api.scanStream(scanDuration, false, (evt: ScanEvent) => {
      if (evt.event === 'progress') {
        setScanProgress(evt)
      }
      if (evt.event === 'found' && evt.opportunity) {
        setLiveFound(prev => {
          if (prev.some(o => o.id === evt.opportunity!.id)) return prev
          return [evt.opportunity!, ...prev]
        })
      }
      if (evt.event === 'done') {
        setScanning(false)
        const count = evt.found_count ?? 0
        setScanMsg(`Scan terminé — ${count} opportunité(s) trouvée(s)`)
        refresh()
        setTimeout(() => setScanMsg(''), 12000)
      }
      if (evt.event === 'error') {
        setScanning(false)
        setScanMsg(evt.message || 'Erreur de scan')
        setTimeout(() => setScanMsg(''), 12000)
      }
    })
    stopScanRef.current = stop
  }

  const stopScan = () => {
    stopScanRef.current?.()
    stopScanRef.current = null
    setScanning(false)
    setScanMsg('Scan arrêté')
    refresh()
    setTimeout(() => setScanMsg(''), 5000)
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
        <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
          <div className="flex items-center gap-1 bg-white rounded-2xl p-1 border border-slate-200/80 shadow-soft">
            <Clock className="w-4 h-4 text-slate-400 ml-2 shrink-0" />
            {SCAN_DURATIONS.map(d => (
              <button
                key={d.value}
                onClick={() => setScanDuration(d.value)}
                disabled={scanning}
                className={`px-3 py-2 rounded-xl text-xs font-semibold transition-all ${
                  scanDuration === d.value ? 'bg-violet-600 text-white' : 'text-slate-500 hover:text-slate-900'
                }`}
              >{d.label}</button>
            ))}
          </div>
          {scanning ? (
            <button onClick={stopScan} className="btn-secondary w-full sm:w-auto">
              <Square className="w-4 h-4" />Arrêter
            </button>
          ) : (
            <button onClick={startScan} className="btn-primary w-full sm:w-auto">
              <RefreshCw className="w-4 h-4" />Scanner {scanDuration} min
            </button>
          )}
        </div>
      </div>

      {scanning && scanProgress && (
        <div className="sticky top-0 z-30 mb-4 px-4 py-3 rounded-2xl bg-violet-600 text-white shadow-lg">
          <div className="flex items-center justify-between gap-3 text-sm font-medium">
            <span className="flex items-center gap-2">
              <RefreshCw className="w-4 h-4 animate-spin" />
              Scan en direct — {liveFound.length} trouvée(s)
            </span>
            <span className="text-violet-200 text-xs shrink-0">
              {formatTime(scanProgress.elapsed_seconds || 0)} / {formatTime((scanProgress.remaining_seconds || 0) + (scanProgress.elapsed_seconds || 0))}
            </span>
          </div>
          <p className="text-xs text-violet-200 mt-1 truncate">
            {scanProgress.query} · {scanProgress.items_fetched || 0} annonces · {scanProgress.analyzed || 0} analysées
            {(scanProgress as { pepites_found?: number }).pepites_found
              ? ` · ${(scanProgress as { pepites_found?: number }).pepites_found} pépites`
              : ''}
          </p>
        </div>
      )}

      {scanMsg && !scanning && (
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

      {loading && !scanning ? (
        <div className="space-y-4">
          {[1, 2, 3].map(i => <div key={i} className="skeleton h-32 rounded-3xl" />)}
        </div>
      ) : displayList.length === 0 ? (
        <div className="glass-card text-center py-16 border-dashed border-2 border-slate-200">
          <div className="w-20 h-20 mx-auto mb-5 rounded-3xl bg-violet-50 flex items-center justify-center">
            <Zap className="w-10 h-10 text-violet-500" />
          </div>
          <p className="font-bold text-slate-900 text-lg">Aucune opportunité</p>
          <p className="text-sm text-slate-500 mt-2 mb-6">
            {scanning ? 'Recherche en cours… les résultats apparaissent ici en direct' : 'Lancez un scan pour découvrir les meilleures affaires'}
          </p>
          {!scanning && (
            <button onClick={startScan} className="btn-primary">
              <Sparkles className="w-4 h-4" /> Scanner maintenant
            </button>
          )}
        </div>
      ) : (
        <div className="grid gap-4">
          {displayList.map(opp => (
            <OppCard key={opp.id} opp={opp} onSelect={() => setSelected(opp)} />
          ))}
        </div>
      )}

      {selected && (
        <OpportunityDetail
          opportunity={selected}
          onClose={() => setSelected(null)}
          onAction={() => { setSelected(null); refresh() }}
        />
      )}
    </PageShell>
  )
}
