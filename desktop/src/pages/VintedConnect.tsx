import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { LogIn, Globe, Shield, Sparkles, Cookie, Info } from 'lucide-react'
import { api } from '../api'

export default function VintedConnect() {
  const [country, setCountry] = useState('fr')
  const [cookies, setCookies] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const connect = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await api.connectVinted(country, cookies.trim() || undefined)
      if (res.connected) navigate('/vinted')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Échec de connexion. Vérifiez que le backend est lancé.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-8 max-w-lg mx-auto animate-fade-in">
      <div className="text-center mb-8">
        <div className="w-16 h-16 bg-gray-900 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <LogIn className="w-7 h-7 text-white" />
        </div>
        <h1 className="page-title">Connexion Vinted</h1>
        <p className="page-subtitle">Liez votre compte pour voir annonces, ventes et publier</p>
      </div>

      <div className="glass-card space-y-5">
        <div>
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

        <div>
          <label className="text-xs font-medium text-gray-500 mb-1.5 flex items-center gap-1.5">
            <Cookie className="w-3.5 h-3.5" />Cookies de session (recommandé)
          </label>
          <textarea
            className="input h-28 resize-none font-mono text-xs"
            placeholder="_vinted_fr_session=...; access_token_web=...&#10;ou JSON depuis une extension cookies"
            value={cookies}
            onChange={e => setCookies(e.target.value)}
          />
          <div className="mt-2 p-3 rounded-xl bg-slate-50 border border-slate-100 text-xs text-slate-600 space-y-1">
            <p className="flex items-start gap-1.5 font-medium text-slate-700">
              <Info className="w-3.5 h-3.5 shrink-0 mt-0.5" />Comment récupérer vos cookies
            </p>
            <p>1. Connectez-vous sur vinted.fr dans Chrome</p>
            <p>2. F12 → Application → Cookies → copiez <code className="bg-white px-1 rounded">_vinted_fr_session</code> et <code className="bg-white px-1 rounded">access_token_web</code></p>
            <p>3. Collez au format : <code className="bg-white px-1 rounded">nom=valeur; nom2=valeur2</code></p>
            <p className="text-slate-500">Sans cookies : scan public uniquement. Avec cookies : vos annonces et ventes.</p>
          </div>
        </div>

        {error && <p className="text-red-500 text-sm">{error}</p>}

        <button onClick={connect} disabled={loading} className="btn-primary w-full py-3">
          <Sparkles className="w-4 h-4" />
          {loading ? 'Connexion...' : cookies.trim() ? 'Connecter avec mes cookies' : 'Connexion session anonyme'}
        </button>

        <div className="flex items-center gap-2 text-xs text-gray-400 justify-center">
          <Shield className="w-3.5 h-3.5" />
          Cookies chiffrés localement — jamais partagés
        </div>
      </div>
    </div>
  )
}
