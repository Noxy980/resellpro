import { useEffect, useState } from 'react'
import { Wand2, Copy, CheckCircle, ExternalLink, FileText } from 'lucide-react'
import { api, DraftListing } from '../api'

export default function ListingCreator() {
  const [form, setForm] = useState({
    brand: '', condition: 'Très bon état', size: '', category: 'Veste',
    extra_info: '', target_price: 0,
  })
  const [result, setResult] = useState<Record<string, unknown> | null>(null)
  const [drafts, setDrafts] = useState<DraftListing[]>([])
  const [loading, setLoading] = useState(false)
  const [copied, setCopied] = useState('')

  useEffect(() => { api.drafts().then(setDrafts).catch(() => {}) }, [])

  const generate = async () => {
    setLoading(true)
    try {
      const res = await api.createDraft(form)
      setResult(res)
      api.drafts().then(setDrafts)
    } finally { setLoading(false) }
  }

  const copy = (text: string, key: string) => {
    navigator.clipboard.writeText(text)
    setCopied(key)
    setTimeout(() => setCopied(''), 2000)
  }

  return (
    <div className="p-8 max-w-4xl mx-auto animate-fade-in">
      <div className="mb-8">
        <h1 className="page-title">Gestionnaire d'annonces</h1>
        <p className="page-subtitle">L'IA optimise chaque annonce pour maximiser vos ventes</p>
      </div>

      <div className="glass-card mb-6">
        <h3 className="font-medium mb-4">Créer une annonce</h3>
        <div className="grid grid-cols-2 gap-4">
          {(['brand', 'size', 'category', 'condition'] as const).map(f => (
            <div key={f}>
              <label className="text-xs font-medium text-gray-500 capitalize">{f === 'brand' ? 'Marque' : f === 'size' ? 'Taille' : f === 'category' ? 'Catégorie' : 'État'}</label>
              <input className="input mt-1" value={form[f]}
                onChange={e => setForm(p => ({ ...p, [f]: e.target.value }))} />
            </div>
          ))}
          <div>
            <label className="text-xs font-medium text-gray-500">Prix cible (€)</label>
            <input type="number" className="input mt-1" value={form.target_price || ''}
              onChange={e => setForm(p => ({ ...p, target_price: parseFloat(e.target.value) }))} />
          </div>
        </div>
        <div className="mt-3">
          <label className="text-xs font-medium text-gray-500">Détails supplémentaires</label>
          <textarea className="input mt-1 h-20 resize-none" value={form.extra_info}
            onChange={e => setForm(p => ({ ...p, extra_info: e.target.value }))}
            placeholder="Couleur, matière, particularités..." />
        </div>
        <button onClick={generate} disabled={loading || !form.brand} className="btn-primary mt-4">
          <Wand2 className="w-4 h-4" />{loading ? 'Génération IA...' : 'Générer l\'annonce optimisée'}
        </button>
      </div>

      {result && (
        <div className="space-y-4 mb-8 animate-fade-in">
          {(['title', 'description', 'keywords', 'recommended_price', 'selling_tips'] as const).map(key => {
            const val = String(result[key] || '')
            if (!val) return null
            const labels: Record<string, string> = {
              title: 'Titre optimisé', description: 'Description', keywords: 'Mots-clés',
              recommended_price: 'Prix recommandé', selling_tips: 'Conseils de vente',
            }
            return (
              <div key={key} className="glass-card">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-medium text-gray-900">{labels[key]}</h4>
                  <button onClick={() => copy(val, key)} className="btn-ghost text-xs">
                    {copied === key ? <CheckCircle className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
                    {copied === key ? 'Copié' : 'Copier'}
                  </button>
                </div>
                <p className="text-sm text-gray-700 whitespace-pre-wrap">{val}</p>
              </div>
            )
          })}
          {typeof result.publish_url === 'string' && (
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => {
                  const text = [
                    result.title, result.description, `Prix: €${result.recommended_price || form.target_price}`,
                  ].filter(Boolean).join('\n\n')
                  navigator.clipboard.writeText(text)
                  setCopied('publish')
                  setTimeout(() => setCopied(''), 2000)
                }}
                className="btn-secondary"
              >
                {copied === 'publish' ? <CheckCircle className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                {copied === 'publish' ? 'Copié !' : 'Copier pour Vinted'}
              </button>
              <button onClick={() => window.open(result.publish_url as string, '_blank')} className="btn-primary">
                <ExternalLink className="w-4 h-4" />Ouvrir Vinted pour publier
              </button>
            </div>
          )}
        </div>
      )}

      {drafts.length > 0 && (
        <div>
          <h3 className="font-medium mb-3 flex items-center gap-2"><FileText className="w-4 h-4" />Brouillons ({drafts.length})</h3>
          <div className="space-y-2">
            {drafts.map(d => (
              <div key={d.id} className="glass-card flex items-center justify-between py-3">
                <div>
                  <p className="text-sm font-medium">{d.title || d.brand}</p>
                  <p className="text-xs text-gray-400">€{d.price} · {d.status}</p>
                </div>
                <span className="text-xs text-gray-400">{new Date(d.created_at).toLocaleDateString('fr')}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
