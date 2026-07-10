import { useEffect, useState } from 'react'
import { Plus, Package, Pencil, Trash2, X, CheckCircle } from 'lucide-react'
import { api, InventoryItem } from '../api'

const STATUSES: Record<string, string> = {
  achete: 'Acheté',
  preparation: 'En préparation',
  publie: 'Publié',
  vendu: 'Vendu',
  envoye: 'Envoyé',
  termine: 'Terminé',
  in_stock: 'En stock',
  listed: 'En vente',
  sold: 'Vendu',
  shipped: 'Expédié',
}

const STATUS_OPTIONS = ['achete', 'preparation', 'publie', 'vendu', 'envoye', 'termine']

type FormData = {
  title: string; brand: string; model: string; size: string; condition: string
  purchase_price: number; planned_resale_price: number; notes: string; status: string
}

const emptyForm = (): FormData => ({
  title: '', brand: '', model: '', size: '', condition: '',
  purchase_price: 0, planned_resale_price: 0, notes: '', status: 'achete',
})

export default function Inventory() {
  const [items, setItems] = useState<InventoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<InventoryItem | null>(null)
  const [form, setForm] = useState<FormData>(emptyForm())

  const refresh = () => {
    setLoading(true)
    api.inventory().then(setItems).finally(() => setLoading(false))
  }
  useEffect(() => { refresh() }, [])

  const openCreate = () => {
    setEditing(null)
    setForm(emptyForm())
    setShowForm(true)
  }

  const openEdit = (item: InventoryItem) => {
    setEditing(item)
    setForm({
      title: item.title, brand: item.brand, model: item.model,
      size: item.size, condition: item.condition,
      purchase_price: item.purchase_price,
      planned_resale_price: item.planned_resale_price,
      notes: item.notes, status: item.status,
    })
    setShowForm(true)
  }

  const save = async () => {
    if (editing) {
      await api.updateInventory(editing.id, form)
    } else {
      await api.createInventory(form)
    }
    setShowForm(false)
    refresh()
  }

  const remove = async (item: InventoryItem) => {
    if (!confirm(`Supprimer « ${item.title} » ?`)) return
    await api.deleteInventory(item.id)
    refresh()
  }

  const markSold = async (item: InventoryItem) => {
    const price = prompt('Prix de vente réel (€) ?', String(item.planned_resale_price || ''))
    if (!price) return
    await api.updateInventory(item.id, {
      status: 'vendu', actual_sale_price: parseFloat(price),
    })
    refresh()
  }

  const soldStatuses = new Set(['vendu', 'sold', 'termine', 'completed'])
  const active = items.filter(i => !soldStatuses.has(i.status))
  const totalInvested = active.reduce((s, i) => s + i.purchase_price, 0)
  const totalProfit = items.filter(i => i.real_profit).reduce((s, i) => s + (i.real_profit || 0), 0)
  const avgRoi = items.filter(i => i.real_profit && i.purchase_price > 0)
    .reduce((s, i) => s + ((i.real_profit || 0) / i.purchase_price * 100), 0)
  const roiCount = items.filter(i => i.real_profit && i.purchase_price > 0).length

  return (
    <div className="p-8 max-w-5xl mx-auto animate-fade-in">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="page-title">Stock</h1>
          <p className="page-subtitle">Gestion complète de vos articles — achat, préparation, vente</p>
        </div>
        <button onClick={openCreate} className="btn-primary">
          <Plus className="w-4 h-4" />Ajouter
        </button>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="glass-card text-center py-4">
          <p className="text-xs text-gray-400">En stock</p>
          <p className="text-2xl font-bold">{active.length}</p>
        </div>
        <div className="glass-card text-center py-4">
          <p className="text-xs text-gray-400">Investi</p>
          <p className="text-2xl font-bold">€{totalInvested.toFixed(0)}</p>
        </div>
        <div className="glass-card text-center py-4">
          <p className="text-xs text-gray-400">Bénéfice réalisé</p>
          <p className="text-2xl font-bold text-emerald-600">€{totalProfit.toFixed(0)}</p>
        </div>
        <div className="glass-card text-center py-4">
          <p className="text-xs text-gray-400">ROI moyen</p>
          <p className="text-2xl font-bold text-violet-600">
            {roiCount ? `${(avgRoi / roiCount).toFixed(0)}%` : '—'}
          </p>
        </div>
      </div>

      {showForm && (
        <div className="glass-card mb-6 animate-fade-in">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-medium">{editing ? 'Modifier l\'article' : 'Nouvel article'}</h3>
            <button onClick={() => setShowForm(false)} className="btn-ghost p-1"><X className="w-4 h-4" /></button>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {(['title', 'brand', 'model', 'size', 'condition'] as const).map(f => (
              <div key={f}>
                <label className="text-xs text-gray-500 capitalize">{f === 'title' ? 'Titre' : f}</label>
                <input className="input mt-1" value={form[f]}
                  onChange={e => setForm(p => ({ ...p, [f]: e.target.value }))} />
              </div>
            ))}
            <div>
              <label className="text-xs text-gray-500">Prix d'achat €</label>
              <input type="number" className="input mt-1" value={form.purchase_price}
                onChange={e => setForm(p => ({ ...p, purchase_price: parseFloat(e.target.value) || 0 }))} />
            </div>
            <div>
              <label className="text-xs text-gray-500">Revente prévue €</label>
              <input type="number" className="input mt-1" value={form.planned_resale_price}
                onChange={e => setForm(p => ({ ...p, planned_resale_price: parseFloat(e.target.value) || 0 }))} />
            </div>
            <div>
              <label className="text-xs text-gray-500">Statut</label>
              <select className="input mt-1" value={form.status}
                onChange={e => setForm(p => ({ ...p, status: e.target.value }))}>
                {STATUS_OPTIONS.map(s => <option key={s} value={s}>{STATUSES[s]}</option>)}
              </select>
            </div>
            <div className="col-span-2">
              <label className="text-xs text-gray-500">Notes</label>
              <textarea className="input mt-1 min-h-[60px]" value={form.notes}
                onChange={e => setForm(p => ({ ...p, notes: e.target.value }))} />
            </div>
          </div>
          <div className="flex gap-2 mt-4">
            <button onClick={save} className="btn-primary">Enregistrer</button>
            <button onClick={() => setShowForm(false)} className="btn-secondary">Annuler</button>
          </div>
        </div>
      )}

      {loading ? <p className="text-center py-12 text-gray-400">Chargement...</p>
      : items.length === 0 ? (
        <div className="text-center py-16">
          <Package className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">Aucun article en stock</p>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map(item => {
            const margin = item.planned_resale_price > 0
              ? ((item.planned_resale_price - item.purchase_price) / item.purchase_price * 100) : null
            return (
              <div key={item.id} className="glass-card">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <p className="font-medium text-sm truncate">{item.title}</p>
                      <span className="badge bg-gray-100 text-gray-600 shrink-0">
                        {STATUSES[item.status] || item.status}
                      </span>
                    </div>
                    <p className="text-xs text-gray-400">{item.brand} {item.model && `· ${item.model}`} · {item.size}</p>
                    <div className="flex flex-wrap gap-4 mt-2 text-sm">
                      <span>Achat <strong>€{item.purchase_price.toFixed(0)}</strong></span>
                      {item.planned_resale_price > 0 && (
                        <span>Cible <strong className="text-emerald-600">€{item.planned_resale_price.toFixed(0)}</strong>
                          {margin != null && <span className="text-gray-400 ml-1">({margin.toFixed(0)}%)</span>}
                        </span>
                      )}
                      {item.real_profit != null && (
                        <span className="text-emerald-600 font-medium">
                          +€{item.real_profit.toFixed(0)} · ROI {item.margin_percent?.toFixed(0)}%
                        </span>
                      )}
                    </div>
                    {item.notes && <p className="text-xs text-gray-400 mt-2 italic">{item.notes}</p>}
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    {!soldStatuses.has(item.status) && (
                      <button onClick={() => markSold(item)} className="btn-success text-xs py-1.5">
                        <CheckCircle className="w-3 h-3" />Vendu
                      </button>
                    )}
                    <button onClick={() => openEdit(item)} className="btn-ghost p-2"><Pencil className="w-3.5 h-3.5" /></button>
                    <button onClick={() => remove(item)} className="btn-ghost p-2 text-red-500"><Trash2 className="w-3.5 h-3.5" /></button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
