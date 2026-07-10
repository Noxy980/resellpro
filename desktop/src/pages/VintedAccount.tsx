import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  User, Package, Star, ExternalLink, RefreshCw, Heart, Clock, TrendingUp, LogIn,
} from 'lucide-react'
import { api, VintedProfile, InventoryItem, Opportunity, VintedSale } from '../api'

type Tab = 'annonces' | 'ventes' | 'favoris' | 'attente' | 'stats'

export default function VintedAccount() {
  const [profile, setProfile] = useState<VintedProfile | null>(null)
  const [listings, setListings] = useState<Record<string, unknown>[]>([])
  const [vintedSales, setVintedSales] = useState<VintedSale[]>([])
  const [inventory, setInventory] = useState<InventoryItem[]>([])
  const [favorites, setFavorites] = useState<Opportunity[]>([])
  const [tab, setTab] = useState<Tab>('annonces')
  const [loading, setLoading] = useState(true)

  const refresh = async () => {
    setLoading(true)
    try {
      const [p, l, sales, inv, fav] = await Promise.all([
        api.vintedProfile(),
        api.vintedListings(),
        api.vintedSales(),
        api.inventory(),
        api.opportunities({ status: 'favorite' }),
      ])
      setProfile(p)
      setListings(l.listings || [])
      setVintedSales(sales.sales || [])
      setInventory(inv)
      setFavorites(fav)
    } finally { setLoading(false) }
  }

  useEffect(() => { refresh() }, [])

  const ventesInv = inventory.filter(i => ['vendu', 'sold', 'termine'].includes(i.status))
  const attente = inventory.filter(i => ['achete', 'preparation', 'in_stock'].includes(i.status))
  const profitInv = ventesInv.reduce((s, i) => s + (i.real_profit || 0), 0)
  const profitVinted = vintedSales.reduce((s, v) => s + v.price, 0)

  const tabs: { id: Tab; label: string; count: number }[] = [
    { id: 'annonces', label: 'Mes annonces', count: listings.length },
    { id: 'ventes', label: 'Mes ventes', count: vintedSales.length || ventesInv.length },
    { id: 'favoris', label: 'Mes favoris', count: favorites.length },
    { id: 'attente', label: 'En attente', count: attente.length },
    { id: 'stats', label: 'Statistiques', count: 0 },
  ]

  return (
    <div className="p-8 max-w-5xl mx-auto animate-fade-in">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="page-title">Mon Vinted</h1>
          <p className="page-subtitle">Annonces, ventes, favoris et statistiques</p>
        </div>
        <div className="flex gap-2">
          <Link to="/vinted/connect" className="btn-secondary text-xs">
            <LogIn className="w-3.5 h-3.5" />Connexion
          </Link>
          <button onClick={refresh} className="btn-secondary">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />Synchroniser
          </button>
        </div>
      </div>

      {profile && (
        <div className="glass-card mb-6 flex items-center gap-5">
          <div className="w-16 h-16 rounded-2xl bg-gray-100 flex items-center justify-center overflow-hidden">
            {profile.photo
              ? <img src={profile.photo} alt="" className="w-full h-full object-cover" />
              : <User className="w-7 h-7 text-gray-400" />}
          </div>
          <div className="flex-1">
            <h2 className="font-semibold text-lg">{profile.login || 'Compte connecté'}</h2>
            <div className="flex gap-4 mt-1 text-sm text-gray-500">
              <span>{profile.item_count || 0} articles</span>
              {profile.positive_feedback != null && (
                <span className="flex items-center gap-1">
                  <Star className="w-3.5 h-3.5 text-amber-400" />{profile.positive_feedback} avis positifs
                </span>
              )}
            </div>
          </div>
          <div className={`px-3 py-1 rounded-full text-xs font-medium ${
            profile.is_connected ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-600'
          }`}>{profile.is_connected ? 'Connecté' : 'Déconnecté'}</div>
        </div>
      )}

      <div className="flex gap-1 mb-6 overflow-x-auto">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`px-4 py-2 rounded-xl text-sm font-medium whitespace-nowrap transition-all ${
              tab === t.id ? 'bg-gray-900 text-white' : 'text-gray-500 hover:bg-white/80'
            }`}>
            {t.label}{t.count > 0 && ` (${t.count})`}
          </button>
        ))}
      </div>

      {tab === 'annonces' && (
        listings.length === 0 ? (
          <EmptyState icon={Package} text="Aucune annonce — connectez-vous avec vos cookies Vinted" />
        ) : (
          <ListingGrid listings={listings} />
        )
      )}

      {tab === 'ventes' && (
        vintedSales.length > 0 ? (
          <div className="space-y-3">
            <p className="text-xs text-slate-500 mb-2">Ventes synchronisées depuis votre compte Vinted</p>
            {vintedSales.map(v => (
              <div key={v.id} className="glass-card flex items-center gap-4">
                <div className="w-14 h-14 rounded-lg bg-gray-100 overflow-hidden shrink-0">
                  {v.image_url && <img src={v.image_url} alt="" className="w-full h-full object-cover" />}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm truncate">{v.title}</p>
                  <p className="text-xs text-gray-400">{v.brand} · €{v.price.toFixed(0)}</p>
                </div>
                {v.url && (
                  <button onClick={() => window.open(v.url, '_blank')} className="btn-ghost text-xs">
                    <ExternalLink className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            ))}
          </div>
        ) : ventesInv.length === 0 ? (
          <EmptyState icon={TrendingUp} text="Aucune vente — connectez vos cookies Vinted pour synchroniser" />
        ) : (
          <div className="space-y-3">
            <p className="text-xs text-slate-500 mb-2">Ventes enregistrées dans ResellPro</p>
            {ventesInv.map(v => (
              <div key={v.id} className="glass-card flex justify-between">
                <div>
                  <p className="font-medium text-sm">{v.title}</p>
                  <p className="text-xs text-gray-400">{v.brand}</p>
                </div>
                <p className="text-emerald-600 font-bold">+€{(v.real_profit || 0).toFixed(0)}</p>
              </div>
            ))}
          </div>
        )
      )}

      {tab === 'favoris' && (
        favorites.length === 0 ? (
          <EmptyState icon={Heart} text="Aucun favori — marquez des opportunités" />
        ) : (
          <div className="space-y-3">
            {favorites.map(f => (
              <div key={f.id} className="glass-card flex items-center gap-4">
                <div className="w-14 h-14 rounded-lg bg-gray-100 overflow-hidden shrink-0">
                  {f.image_url && <img src={f.image_url} alt="" className="w-full h-full object-cover" />}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm truncate">{f.title}</p>
                  <p className="text-xs text-gray-400">€{f.price} · Score {f.score}/100</p>
                </div>
                <button onClick={() => window.open(f.url, '_blank')} className="btn-ghost text-xs">
                  <ExternalLink className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        )
      )}

      {tab === 'attente' && (
        attente.length === 0 ? (
          <EmptyState icon={Clock} text="Aucun article en attente de préparation" />
        ) : (
          <div className="space-y-3">
            {attente.map(a => (
              <div key={a.id} className="glass-card flex justify-between">
                <div>
                  <p className="font-medium text-sm">{a.title}</p>
                  <p className="text-xs text-gray-400">Achat €{a.purchase_price}</p>
                </div>
                <span className="badge bg-amber-100 text-amber-700">À préparer</span>
              </div>
            ))}
          </div>
        )
      )}

      {tab === 'stats' && (
        <div className="grid grid-cols-3 gap-4">
          <div className="glass-card text-center py-6">
            <p className="text-xs text-gray-400">Ventes Vinted</p>
            <p className="text-3xl font-bold">{vintedSales.length || ventesInv.length}</p>
          </div>
          <div className="glass-card text-center py-6">
            <p className="text-xs text-gray-400">Chiffre d'affaires</p>
            <p className="text-3xl font-bold text-emerald-600">€{(profitVinted || profitInv).toFixed(0)}</p>
          </div>
          <div className="glass-card text-center py-6">
            <p className="text-xs text-gray-400">Annonces actives</p>
            <p className="text-3xl font-bold">{listings.length}</p>
          </div>
        </div>
      )}
    </div>
  )
}

function EmptyState({ icon: Icon, text }: { icon: typeof Package; text: string }) {
  return (
    <div className="glass-card text-center py-12 text-gray-400">
      <Icon className="w-8 h-8 mx-auto mb-2 opacity-40" />
      <p>{text}</p>
    </div>
  )
}

function ListingGrid({ listings }: { listings: Record<string, unknown>[] }) {
  return (
    <div className="grid gap-3">
      {listings.map((item, i) => (
        <div key={i} className="glass-card flex items-center gap-4">
          <div className="w-16 h-16 rounded-xl bg-gray-100 overflow-hidden shrink-0">
            {typeof item.image_url === 'string' && <img src={item.image_url} alt="" className="w-full h-full object-cover" />}
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-medium text-sm truncate">{String(item.title)}</p>
            <p className="text-xs text-gray-400">{String(item.brand)} · €{Number(item.price).toFixed(0)}</p>
          </div>
          {typeof item.url === 'string' && (
            <button onClick={() => window.open(item.url as string, '_blank')} className="btn-ghost text-xs">
              <ExternalLink className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      ))}
    </div>
  )
}
