import { useEffect, useState } from 'react'
import { Save, Key, Sparkles, Brain } from 'lucide-react'
import { api } from '../api'

export default function SettingsPage() {
  const [settings, setSettings] = useState({ monitor_enabled: true, poll_interval: 90, has_openai_key: false, ai_provider: '' })
  const [apiKey, setApiKey] = useState('')
  const [profile, setProfile] = useState<Record<string, unknown>>({})
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    api.settings().then(s => setSettings({
      monitor_enabled: Boolean(s.monitor_enabled ?? true),
      poll_interval: Number(s.poll_interval ?? 90),
      has_openai_key: Boolean(s.has_openai_key),
      ai_provider: String(s.ai_provider ?? ''),
    }))
    api.profile().then(setProfile)
  }, [])

  const save = async () => {
    await api.updateSettings({
      openai_api_key: apiKey || undefined,
      monitor_enabled: settings.monitor_enabled,
      poll_interval: settings.poll_interval,
    })
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const preferred = (profile as { preferred_brands?: { name: string; score: number }[] }).preferred_brands || []
  const avoided = (profile as { avoided_brands?: { name: string; score: number }[] }).avoided_brands || []

  return (
    <div className="p-8 max-w-2xl mx-auto animate-fade-in">
      <div className="mb-8">
        <h1 className="page-title">Paramètres</h1>
        <p className="page-subtitle">Configuration de l'application et de l'IA</p>
      </div>

      <div className="space-y-5">
        <div className="glass-card">
          <h3 className="font-medium mb-3 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-violet-500" />Intelligence artificielle
          </h3>
          <p className="text-sm text-gray-500 mb-3">
            {settings.ai_provider || 'OpenRouter'} — modèles gratuits uniquement
            {settings.has_openai_key && <span className="text-emerald-600 ml-2">✓ Configuré</span>}
          </p>
          <label className="text-xs font-medium text-gray-500">Clé API OpenRouter</label>
          <input type="password" className="input mt-1" placeholder="sk-or-v1-..."
            value={apiKey} onChange={e => setApiKey(e.target.value)} />
        </div>

        <div className="glass-card">
          <h3 className="font-medium mb-3">Scanner automatique</h3>
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm text-gray-600">Surveillance en arrière-plan</span>
            <button onClick={() => setSettings(s => ({ ...s, monitor_enabled: !s.monitor_enabled }))}
              className={`w-11 h-6 rounded-full transition-colors relative ${settings.monitor_enabled ? 'bg-gray-900' : 'bg-gray-200'}`}>
              <div className={`w-5 h-5 bg-white rounded-full absolute top-0.5 transition-transform shadow-sm ${settings.monitor_enabled ? 'translate-x-5' : 'translate-x-0.5'}`} />
            </button>
          </div>
          <label className="text-xs font-medium text-gray-500">Intervalle (secondes)</label>
          <input type="number" className="input mt-1" value={settings.poll_interval}
            onChange={e => setSettings(s => ({ ...s, poll_interval: parseInt(e.target.value) }))} />
        </div>

        {(preferred.length > 0 || avoided.length > 0) && (
          <div className="glass-card">
            <h3 className="font-medium mb-3 flex items-center gap-2">
              <Brain className="w-4 h-4 text-violet-500" />Profil personnalisé
            </h3>
            <p className="text-sm text-gray-500 mb-3">L'IA apprend de vos choix pour affiner ses recommandations</p>
            {preferred.length > 0 && (
              <div className="mb-3">
                <p className="text-xs font-medium text-gray-400 mb-1">Marques préférées</p>
                {preferred.map(b => (
                  <div key={b.name} className="flex justify-between text-sm py-1">
                    <span>{b.name}</span><span className="text-emerald-600">+{b.score.toFixed(0)}</span>
                  </div>
                ))}
              </div>
            )}
            {avoided.length > 0 && (
              <div>
                <p className="text-xs font-medium text-gray-400 mb-1">Marques évitées</p>
                {avoided.map(b => (
                  <div key={b.name} className="flex justify-between text-sm py-1">
                    <span>{b.name}</span><span className="text-red-500">{b.score.toFixed(0)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        <button onClick={save} className="btn-primary">
          <Save className="w-4 h-4" />{saved ? 'Enregistré !' : 'Enregistrer'}
        </button>
      </div>
    </div>
  )
}
