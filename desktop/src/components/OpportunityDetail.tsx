import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import {
  X, ExternalLink, Heart, ShoppingCart, Sparkles,
  CheckCircle, AlertTriangle, MessageSquare,
} from 'lucide-react'
import { api, Opportunity } from '../api'
import MarkdownContent from './MarkdownContent'

interface Props {
  opportunity: Opportunity
  onClose: () => void
  onAction: () => void
}

export default function OpportunityDetail({ opportunity: opp, onClose, onAction }: Props) {
  const [aiRec, setAiRec] = useState('')
  const [loadingAi, setLoadingAi] = useState(false)

  useEffect(() => {
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => {
      document.body.style.overflow = prev
      window.removeEventListener('keydown', onKey)
    }
  }, [onClose])

  const action = async (type: string) => {
    await api.opportunityAction(opp.id, type)
    onAction()
  }

  const askAI = async () => {
    setLoadingAi(true)
    try {
      const res = await api.analyze(opp.id)
      setAiRec(res.analysis)
    } finally { setLoadingAi(false) }
  }

  return createPortal(
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-fade-in"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl"
        onClick={e => e.stopPropagation()}
      >
        <div className="p-6">
          <div className="flex items-start justify-between mb-5">
            <h2 className="font-semibold text-lg text-gray-900 pr-4">{opp.title}</h2>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600 shrink-0">
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="flex flex-col sm:flex-row gap-6">
            <div className="w-full sm:w-44 h-52 rounded-xl overflow-hidden bg-gray-100 shrink-0">
              {opp.image_url && <img src={opp.image_url} alt="" className="w-full h-full object-cover" />}
            </div>
            <div className="flex-1 space-y-3">
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div><span className="text-gray-400 text-xs">Marque</span><p className="font-medium">{opp.brand}</p></div>
                <div><span className="text-gray-400 text-xs">Modèle</span><p className="font-medium">{opp.model}</p></div>
                <div><span className="text-gray-400 text-xs">Taille</span><p className="font-medium">{opp.size}</p></div>
                <div><span className="text-gray-400 text-xs">État</span><p className="font-medium">{opp.condition}</p></div>
              </div>
              <div className="text-3xl font-bold text-gray-900">{opp.score}<span className="text-lg text-gray-400">/100</span></div>
              <div className="flex gap-5 text-sm">
                <div><span className="text-gray-400 text-xs">Achat</span><p className="font-bold text-lg">€{opp.price.toFixed(0)}</p></div>
                <div><span className="text-gray-400 text-xs">Revente</span><p className="font-bold text-lg text-emerald-600">€{opp.estimated_resale.toFixed(0)}</p></div>
                <div><span className="text-gray-400 text-xs">Profit</span><p className="font-bold text-lg text-emerald-600">+€{opp.potential_profit.toFixed(0)}</p></div>
              </div>
              <p className="text-sm text-gray-500">{opp.selling_speed} · {opp.quick_sale_probability.toFixed(0)}% vente rapide</p>
            </div>
          </div>

          <div className="mt-5 space-y-3">
            <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-4">
              <div className="flex items-center gap-2 text-emerald-700 text-sm font-medium mb-1">
                <CheckCircle className="w-4 h-4" />Pourquoi acheter
              </div>
              <p className="text-sm text-gray-700">{opp.why_buy}</p>
            </div>
            <div className="bg-amber-50 border border-amber-100 rounded-xl p-4">
              <div className="flex items-center gap-2 text-amber-700 text-sm font-medium mb-1">
                <AlertTriangle className="w-4 h-4" />Risque
              </div>
              <p className="text-sm text-gray-700">{opp.risk}</p>
            </div>
          </div>

          {aiRec && (
            <div className="mt-4 bg-violet-50 border border-violet-100 rounded-xl p-4">
              <div className="flex items-center gap-2 text-violet-700 text-sm font-medium mb-1">
                <Sparkles className="w-4 h-4" />Recommandation IA
              </div>
              <MarkdownContent content={aiRec} className="text-sm" />
            </div>
          )}

          <div className="flex flex-wrap gap-2 mt-5">
            <button onClick={() => window.open(opp.url, '_blank')} className="btn-primary">
              <ExternalLink className="w-4 h-4" />Voir sur Vinted
            </button>
            <button onClick={() => action('favorite')} className="btn-secondary"><Heart className="w-4 h-4" />Favori</button>
            <button onClick={() => action('purchased')} className="btn-success"><ShoppingCart className="w-4 h-4" />Acheté</button>
            <button onClick={() => action('rejected')} className="btn-danger"><X className="w-4 h-4" />Pas intéressant</button>
            <button onClick={askAI} disabled={loadingAi} className="btn-secondary">
              <MessageSquare className="w-4 h-4" />{loadingAi ? 'Analyse...' : 'Demander à l\'IA'}
            </button>
          </div>
        </div>
      </div>
    </div>,
    document.body,
  )
}
