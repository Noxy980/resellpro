import { useEffect, useState } from 'react'
import { WifiOff, RefreshCw } from 'lucide-react'
import { api, getApiBase } from '../api'

export default function ApiBanner() {
  const [online, setOnline] = useState<boolean | null>(null)

  const check = () => {
    api.monitorStatus()
      .then(() => setOnline(true))
      .catch(() => setOnline(false))
  }

  useEffect(() => { check() }, [])

  if (online === null || online) return null

  const missingUrl = import.meta.env.PROD && !import.meta.env.VITE_API_URL

  return (
    <div className="bg-gradient-to-r from-amber-50 to-orange-50 border-b border-amber-200/80 px-4 py-3 flex items-start gap-3 text-sm text-amber-900 relative z-50">
      <WifiOff className="w-5 h-5 shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        {missingUrl ? (
          <>
            <p className="font-bold">API non configurée sur Netlify</p>
            <p className="text-xs mt-1 text-amber-700">
              Ajoutez <code className="bg-amber-100 px-1.5 py-0.5 rounded font-mono">VITE_API_URL</code> puis redéployez.
            </p>
          </>
        ) : (
          <>
            <p className="font-bold">Backend hors ligne</p>
            <p className="text-xs mt-1 text-amber-700 truncate">
              {getApiBase()} — Render peut mettre 30s à démarrer (plan gratuit).
            </p>
          </>
        )}
      </div>
      <button onClick={check} className="shrink-0 p-2 rounded-xl bg-white/80 hover:bg-white border border-amber-200">
        <RefreshCw className="w-4 h-4" />
      </button>
    </div>
  )
}
