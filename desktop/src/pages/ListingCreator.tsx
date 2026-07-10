import { useEffect, useRef, useState } from 'react'
import { Wand2, Copy, CheckCircle, ExternalLink, FileText, Upload, Image, Euro, Sparkles } from 'lucide-react'
import { api, DraftListing } from '../api'
import MarkdownContent from '../components/MarkdownContent'

const CATEGORIES = ['Veste', 'T-shirt', 'Polo', 'Pantalon', 'Jean', 'Sweat', 'Hoodie', 'Short', 'Sneakers', 'Pull', 'Manteau', 'Accessoire']
const CONDITIONS = ['Neuf avec étiquette', 'Neuf sans étiquette', 'Très bon état', 'Bon état', 'Satisfaisant']

export default function ListingCreator() {
  const [form, setForm] = useState({
    brand: '', condition: 'Très bon état', size: '', category: 'Veste',
    color: '', defects: '', extra_info: '', target_price: 0, purchase_price: 0,
  })
  const [photos, setPhotos] = useState<File[]>([])
  const [previews, setPreviews] = useState<string[]>([])
  const [result, setResult] = useState<Record<string, unknown> | null>(null)
  const [drafts, setDrafts] = useState<DraftListing[]>([])
  const [loading, setLoading] = useState(false)
  const [copied, setCopied] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => { api.drafts().then(setDrafts).catch(() => {}) }, [])

  const handlePhotos = (files: FileList | null) => {
    if (!files) return
    const arr = Array.from(files).slice(0, 8)
    setPhotos(arr)
    setPreviews(arr.map(f => URL.createObjectURL(f)))
  }

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

  const resultFields: { key: string; label: string; icon?: typeof Sparkles }[] = [
    { key: 'title', label: 'Titre optimisé' },
    { key: 'description', label: 'Description professionnelle' },
    { key: 'keywords', label: 'Mots-clés SEO' },
    { key: 'recommended_price', label: 'Prix idéal', icon: Euro },
    { key: 'min_price', label: 'Prix minimum acceptable', icon: Euro },
    { key: 'estimated_margin', label: 'Marge estimée', icon: Euro },
    { key: 'selling_tips', label: 'Conseils de vente' },
    { key: 'photo_tips', label: 'Conseils photo' },
  ]

  return (
    <div className="p-4 md:p-8 max-w-5xl mx-auto animate-fade-in">
      <div className="mb-8">
        <h1 className="page-title">Générateur d'annonces IA</h1>
        <p className="page-subtitle">Titres, descriptions et prix optimisés pour Vinted</p>
      </div>

      <div className="grid lg:grid-cols-5 gap-6">
        {/* Form */}
        <div className="lg:col-span-2 space-y-4">
          <div className="glass-card">
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <Image className="w-4 h-4 text-violet-500" />Photos du vêtement
            </h3>
            <div
              className="border-2 border-dashed border-slate-200 rounded-2xl p-6 text-center cursor-pointer hover:border-violet-300 transition-colors"
              onClick={() => inputRef.current?.click()}
            >
              <Upload className="w-8 h-8 text-slate-300 mx-auto mb-2" />
              <p className="text-sm text-slate-500">Ajouter des photos (max 8)</p>
              <input ref={inputRef} type="file" accept="image/*" multiple className="hidden"
                onChange={e => handlePhotos(e.target.files)} />
            </div>
            {previews.length > 0 && (
              <div className="grid grid-cols-4 gap-2 mt-3">
                {previews.map((src, i) => (
                  <img key={i} src={src} alt="" className="w-full aspect-square object-cover rounded-xl" />
                ))}
              </div>
            )}
          </div>

          <div className="glass-card">
            <h3 className="font-semibold mb-4">Détails de l'article</h3>
            <div className="space-y-3">
              <div>
                <label className="text-xs font-medium text-slate-500">Marque *</label>
                <input className="input mt-1" value={form.brand}
                  onChange={e => setForm(p => ({ ...p, brand: e.target.value }))} placeholder="Nike, Carhartt..." />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-slate-500">Taille</label>
                  <input className="input mt-1" value={form.size}
                    onChange={e => setForm(p => ({ ...p, size: e.target.value }))} placeholder="M, L, 42..." />
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-500">Couleur</label>
                  <input className="input mt-1" value={form.color}
                    onChange={e => setForm(p => ({ ...p, color: e.target.value }))} placeholder="Noir, bleu..." />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-slate-500">Catégorie</label>
                  <select className="input mt-1" value={form.category}
                    onChange={e => setForm(p => ({ ...p, category: e.target.value }))}>
                    {CATEGORIES.map(c => <option key={c}>{c}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-500">État</label>
                  <select className="input mt-1" value={form.condition}
                    onChange={e => setForm(p => ({ ...p, condition: e.target.value }))}>
                    {CONDITIONS.map(c => <option key={c}>{c}</option>)}
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-slate-500">Prix d'achat €</label>
                  <input type="number" className="input mt-1" value={form.purchase_price || ''}
                    onChange={e => setForm(p => ({ ...p, purchase_price: parseFloat(e.target.value) || 0 }))} />
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-500">Prix cible €</label>
                  <input type="number" className="input mt-1" value={form.target_price || ''}
                    onChange={e => setForm(p => ({ ...p, target_price: parseFloat(e.target.value) || 0 }))} />
                </div>
              </div>
              <div>
                <label className="text-xs font-medium text-slate-500">Défauts éventuels</label>
                <input className="input mt-1" value={form.defects}
                  onChange={e => setForm(p => ({ ...p, defects: e.target.value }))}
                  placeholder="Petite tache, usure légère..." />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-500">Détails supplémentaires</label>
                <textarea className="input mt-1 h-20 resize-none" value={form.extra_info}
                  onChange={e => setForm(p => ({ ...p, extra_info: e.target.value }))}
                  placeholder="Matière, coupe, particularités..." />
              </div>
            </div>
            <button onClick={generate} disabled={loading || !form.brand} className="btn-primary w-full mt-4">
              <Wand2 className="w-4 h-4" />
              {loading ? 'Génération IA en cours...' : 'Générer l\'annonce optimisée'}
            </button>
          </div>
        </div>

        {/* Results */}
        <div className="lg:col-span-3">
          {!result ? (
            <div className="glass-card text-center py-20 border-dashed border-2 border-slate-200">
              <Sparkles className="w-12 h-12 text-violet-300 mx-auto mb-4" />
              <p className="font-semibold text-slate-700">Remplissez le formulaire</p>
              <p className="text-sm text-slate-500 mt-1">L'IA génère titre, description, prix et conseils</p>
            </div>
          ) : (
            <div className="space-y-4 animate-fade-in">
              {resultFields.map(({ key, label }) => {
                const val = String(result[key] || '')
                if (!val) return null
                return (
                  <div key={key} className="glass-card">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-sm font-semibold text-slate-900">{label}</h4>
                      <button onClick={() => copy(val, key)} className="btn-ghost text-xs">
                        {copied === key ? <CheckCircle className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
                        {copied === key ? 'Copié' : 'Copier'}
                      </button>
                    </div>
                    {key === 'description' || key === 'selling_tips' || key === 'photo_tips'
                      ? <MarkdownContent content={val} className="text-sm" />
                      : <p className="text-sm text-slate-700">{val}</p>}
                  </div>
                )
              })}
              {typeof result.publish_url === 'string' && (
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => {
                      const text = [
                        result.title, result.description,
                        `Prix: €${result.recommended_price || form.target_price}`,
                        `Min: €${result.min_price || ''}`,
                      ].filter(Boolean).join('\n\n')
                      copy(text, 'publish')
                    }}
                    className="btn-secondary"
                  >
                    {copied === 'publish' ? <CheckCircle className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                    {copied === 'publish' ? 'Copié !' : 'Copier tout pour Vinted'}
                  </button>
                  <button onClick={() => window.open(result.publish_url as string, '_blank')} className="btn-primary">
                    <ExternalLink className="w-4 h-4" />Publier sur Vinted
                  </button>
                </div>
              )}
            </div>
          )}

          {drafts.length > 0 && (
            <div className="mt-8">
              <h3 className="font-medium mb-3 flex items-center gap-2">
                <FileText className="w-4 h-4" />Brouillons ({drafts.length})
              </h3>
              <div className="space-y-2">
                {drafts.map(d => (
                  <div key={d.id} className="glass-card flex items-center justify-between py-3">
                    <div>
                      <p className="text-sm font-medium">{d.title || d.brand}</p>
                      <p className="text-xs text-slate-400">€{d.price} · {d.status}</p>
                    </div>
                    <span className="text-xs text-slate-400">{new Date(d.created_at).toLocaleDateString('fr')}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
