import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  TrendingUp, Package, Sparkles, Target, DollarSign, ArrowRight, Sun, Snowflake,
  RefreshCw, Zap, Camera, FileText, MessageSquare, ChevronRight, AlertCircle,
  Leaf, Cloud,
} from 'lucide-react'
import { api, Opportunity } from '../api'
import PageShell from '../components/PageShell'
import { StatCard, DashboardSkeleton } from '../components/StatCard'

const SEASON_ICON: Record<string, typeof Sun> = {
  été: Sun, hiver: Snowflake, printemps: Leaf, automne: Cloud,
}

const QUICK_ACTIONS = [
  { to: '/opportunities', icon: Zap, label: 'Scanner', desc: 'Trouver des deals', color: 'text-violet-600 bg-violet-50' },
  { to: '/ai', icon: MessageSquare, label: 'Assistant IA', desc: 'Conseils pro', color: 'text-blue-600 bg-blue-50' },
  { to: '/photos', icon: Camera, label: 'Photo Studio', desc: 'Améliorer photos', color: 'text-pink-600 bg-pink-50' },
  { to: '/listings', icon: FileText, label: 'Annonces', desc: 'Créer & publier', color: 'text-emerald-600 bg-emerald-50' },
]

export default function Dashboard() {
  const [data, setData] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [aiTip, setAiTip] = useState('')
  const [scanning, setScanning] = useState(false)

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const d = await api.dashboard()
      setData(d)
      api.dashboardAiTip().then(r => setAiTip(r.tip)).catch(() => {})
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Impossible de charger le dashboard')
      setData(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const scan = async () => {
    setScanning(true)
    try {
      await api.scan(true)
      await load()
    } finally {
      setScanning(false)
    }
  }

  if (loading) {
    return <PageShell><DashboardSkeleton /></PageShell>
  }

  if (error || !data) {
    return (
      <PageShell>
        <div className="hero-card text-center py-12 md:py-16">
          <AlertCircle className="w-12 h-12 mx-auto mb-4 opacity-80" />
          <h2 className="text-xl md:text-2xl font-bold mb-2">Connexion API requise</h2>
          <p className="text-violet-200 text-sm md:text-base max-w-md mx-auto mb-6">{error || 'Backend inaccessible'}</p>
          <button onClick={load} className="btn bg-white text-violet-700 hover:bg-violet-50">
            <RefreshCw className="w-4 h-4" /> Réessayer
          </button>
        </div>
        <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-3">
          {QUICK_ACTIONS.map(a => (
            <Link key={a.to} to={a.to} className="quick-action">
              <div className={`w-12 h-12 rounded-2xl ${a.color} flex items-center justify-center`}>
                <a.icon className="w-6 h-6" />
              </div>
              <span className="font-semibold text-sm text-slate-800">{a.label}</span>
            </Link>
          ))}
        </div>
      </PageShell>
    )
  }

  const season = String(data.season || 'été')
  const SeasonIcon = SEASON_ICON[season] || Sun
  const opps = (data.top_opportunities as Opportunity[]) || []
  const monitor = data.monitor as { status?: string; running?: boolean } | undefined
  const isEmpty = opps.length === 0 && Number(data.opportunity_count) === 0

  return (
    <PageShell>
      {/* Hero */}
      <div className="hero-card mb-6 md:mb-8 animate-slide-up">
        <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/4 animate-float" />
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-violet-400/20 rounded-full blur-2xl translate-y-1/2 -translate-x-1/4" />
        <div className="relative">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
            <div>
              <div className="inline-flex items-center gap-2 bg-white/15 backdrop-blur px-3 py-1.5 rounded-full text-xs font-semibold mb-4">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                {monitor?.running ? 'Bot actif' : 'Prêt à scanner'}
              </div>
              <h1 className="text-2xl md:text-4xl font-bold font-display tracking-tight mb-2">
                Bonjour, revendeur 👋
              </h1>
              <p className="text-violet-200 text-sm md:text-base max-w-lg">
                Saison <span className="text-white font-semibold capitalize">{season}</span>
                {' · '}Le bot cherche : {(data.season_keywords as string[])?.slice(0, 4).join(', ')}...
              </p>
            </div>
            <div className="flex flex-col sm:flex-row gap-3">
              <button onClick={scan} disabled={scanning} className="btn bg-white text-violet-700 hover:bg-violet-50 shadow-xl">
                <RefreshCw className={`w-4 h-4 ${scanning ? 'animate-spin' : ''}`} />
                {scanning ? 'Scan en cours...' : 'Lancer un scan'}
              </button>
              <Link to="/opportunities" className="btn border border-white/30 text-white hover:bg-white/10">
                Voir les deals <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4 mb-6 md:mb-8">
        <StatCard icon={Target} label="Opportunités" value={String(data.opportunity_count)} accent="violet"
          sub="Actives maintenant" />
        <StatCard icon={DollarSign} label="Profit potentiel" value={`€${data.potential_profit_today}`} accent="emerald"
          sub="Top 5 du jour" />
        <StatCard icon={Package} label="En stock" value={String(data.stock_count)} accent="blue"
          sub="Articles à vendre" />
        <StatCard icon={TrendingUp} label="Bénéfice total" value={`€${data.total_profit}`} accent="amber"
          sub={`${data.sold_count} ventes`} />
      </div>

      {/* Quick actions */}
      <div className="mb-6 md:mb-8">
        <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">Actions rapides</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {QUICK_ACTIONS.map(a => (
            <Link key={a.to} to={a.to} className="quick-action group">
              <div className={`w-12 h-12 rounded-2xl ${a.color} flex items-center justify-center group-hover:scale-110 transition-transform`}>
                <a.icon className="w-6 h-6" />
              </div>
              <span className="font-bold text-sm text-slate-800">{a.label}</span>
              <span className="text-[11px] text-slate-400">{a.desc}</span>
            </Link>
          ))}
        </div>
      </div>

      {/* AI tip */}
      <div className="glass-card mb-6 md:mb-8 border-violet-100/80 bg-gradient-to-br from-violet-50/80 to-white">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-violet-500 to-violet-700 flex items-center justify-center shrink-0 shadow-lg shadow-violet-500/30">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-bold text-slate-900 mb-1">Conseil IA du jour</p>
            <p className="text-sm text-slate-600 leading-relaxed">
              {aiTip || String(data.ai_recommendation)}
            </p>
            {!aiTip && (
              <p className="text-xs text-violet-400 mt-2 animate-pulse">Chargement conseil personnalisé...</p>
            )}
          </div>
          <SeasonIcon className="w-8 h-8 text-violet-300 shrink-0 hidden md:block" />
        </div>
      </div>

      {/* Opportunities */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg md:text-xl font-bold text-slate-900">Meilleures opportunités</h2>
          <Link to="/opportunities" className="text-sm font-semibold text-violet-600 hover:text-violet-700 flex items-center gap-1">
            Tout voir <ChevronRight className="w-4 h-4" />
          </Link>
        </div>

        {isEmpty ? (
          <div className="glass-card text-center py-12 md:py-16 border-dashed border-2 border-slate-200">
            <div className="w-20 h-20 mx-auto mb-5 rounded-3xl bg-gradient-to-br from-violet-100 to-violet-50 flex items-center justify-center">
              <Zap className="w-10 h-10 text-violet-500" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 mb-2">Aucune opportunité pour l'instant</h3>
            <p className="text-sm text-slate-500 max-w-sm mx-auto mb-6">
              Lancez un scan pour que le bot analyse Vinted et trouve les meilleures affaires de revente.
            </p>
            <button onClick={scan} disabled={scanning} className="btn-primary">
              <RefreshCw className={`w-4 h-4 ${scanning ? 'animate-spin' : ''}`} />
              {scanning ? 'Analyse en cours...' : 'Scanner Vinted maintenant'}
            </button>
          </div>
        ) : (
          <div className="grid gap-3 md:gap-4">
            {opps.map((o, i) => (
              <Link key={o.id} to="/opportunities"
                className="glass-card flex items-center gap-4 py-4 group hover:border-violet-100"
                style={{ animationDelay: `${i * 0.05}s` }}>
                <div className="w-16 h-16 md:w-20 md:h-20 rounded-2xl bg-slate-100 overflow-hidden shrink-0 ring-2 ring-white shadow-md">
                  {o.image_url
                    ? <img src={o.image_url} alt="" className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
                    : <div className="w-full h-full flex items-center justify-center text-slate-300"><Package className="w-8 h-8" /></div>}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-bold text-sm md:text-base text-slate-900 truncate">{o.title}</p>
                  <p className="text-xs md:text-sm text-slate-500 mt-0.5">{o.brand} · €{o.price} → €{o.estimated_resale}</p>
                  <div className="flex gap-2 mt-2">
                    <span className="badge-brand">{o.score}/100</span>
                    <span className="badge-high">+{o.profit_percent.toFixed(0)}%</span>
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <p className="text-lg md:text-xl font-bold text-emerald-600">+€{o.potential_profit.toFixed(0)}</p>
                  <ChevronRight className="w-5 h-5 text-slate-300 ml-auto mt-1 group-hover:text-violet-400 transition-colors" />
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </PageShell>
  )
}
