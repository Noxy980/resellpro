import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { LogIn, Globe, Shield, Sparkles } from 'lucide-react'
import { api } from '../api'

export default function VintedConnect() {
  const [country, setCountry] = useState('fr')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const connect = async () => {
    setLoading(true)
    setError('')
    try {
      await api.connectVinted(country)
      navigate('/')
    } catch {
      setError('Échec de connexion. Vérifiez que le backend est lancé.')
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
        <p className="page-subtitle">Liez votre compte pour synchroniser annonces et ventes</p>
      </div>

      <div className="glass-card">
        <label className="text-xs font-medium text-gray-500 mb-1.5 block">Pays Vinted</label>
        <div className="relative mb-5">
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

        {error && <p className="text-red-500 text-sm mb-4">{error}</p>}

        <button onClick={connect} disabled={loading} className="btn-primary w-full py-3">
          <Sparkles className="w-4 h-4" />
          {loading ? 'Connexion...' : 'Connecter mon compte Vinted'}
        </button>

        <div className="flex items-center gap-2 mt-4 text-xs text-gray-400 justify-center">
          <Shield className="w-3.5 h-3.5" />
          Session sécurisée — identifiants jamais stockés
        </div>
      </div>
    </div>
  )
}
