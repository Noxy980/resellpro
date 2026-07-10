import { useState } from 'react'
import { Sparkles, Globe, ArrowRight, Shield } from 'lucide-react'
import { api } from '../api'

export default function ConnectScreen({ backendDown = false }: { backendDown?: boolean }) {
  const [country, setCountry] = useState('fr')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const connect = async () => {
    setLoading(true)
    setError('')
    try {
      await api.connectVinted(country)
      window.location.reload()
    } catch {
      setError('Connexion échouée. Vérifiez que le backend est lancé (python backend/run.py).')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-[#f8f9fc] relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-violet-100/40 via-white to-blue-100/30" />
      <div className="absolute top-20 left-20 w-72 h-72 bg-violet-200/30 rounded-full blur-3xl" />
      <div className="absolute bottom-20 right-20 w-96 h-96 bg-blue-200/20 rounded-full blur-3xl" />

      <div className="glass-card max-w-md w-full mx-4 relative animate-fade-in">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-gray-900 rounded-2xl flex items-center justify-center mx-auto mb-5 shadow-lg">
            <Sparkles className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-semibold text-gray-900">Bienvenue sur ResellPro</h1>
          <p className="text-gray-500 text-sm mt-2 leading-relaxed">
            Votre assistant professionnel d'achat-revente.<br />
            Connectez Vinted pour commencer.
          </p>
        </div>

        <div className="mb-5">
          <label className="text-xs font-medium text-gray-500 mb-1.5 block">Pays Vinted</label>
          <div className="relative">
            <Globe className="absolute left-3.5 top-3 w-4 h-4 text-gray-400" />
            <select className="input pl-10" value={country} onChange={e => setCountry(e.target.value)}>
              <option value="fr">France — vinted.fr</option>
              <option value="de">Allemagne — vinted.de</option>
              <option value="co.uk">Royaume-Uni — vinted.co.uk</option>
              <option value="es">Espagne — vinted.es</option>
              <option value="it">Italie — vinted.it</option>
              <option value="nl">Pays-Bas — vinted.nl</option>
              <option value="be">Belgique — vinted.be</option>
            </select>
          </div>
        </div>

        {backendDown && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 mb-4 text-sm text-amber-800">
            ⚠️ Backend non détecté. Lancez d'abord : <code className="bg-amber-100 px-1 rounded">python backend/run.py</code>
          </div>
        )}

        {error && <p className="text-red-500 text-sm mb-4 text-center">{error}</p>}

        <button onClick={connect} disabled={loading} className="btn-primary w-full py-3 text-base">
          {loading ? 'Connexion...' : 'Connecter mon compte Vinted'}
          {!loading && <ArrowRight className="w-4 h-4" />}
        </button>

        <div className="flex items-center justify-center gap-2 mt-5 text-xs text-gray-400">
          <Shield className="w-3.5 h-3.5" />
          Session sécurisée — vos identifiants ne sont jamais stockés
        </div>
      </div>
    </div>
  )
}
