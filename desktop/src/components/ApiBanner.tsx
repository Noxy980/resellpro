import { useEffect, useState } from 'react'
import { Wifi, WifiOff } from 'lucide-react'
import { api, getApiBase } from '../api'

export default function ApiBanner() {
  const [online, setOnline] = useState<boolean | null>(null)

  useEffect(() => {
    api.monitorStatus()
      .then(() => setOnline(true))
      .catch(() => setOnline(false))
  }, [])

  if (online === null || online) return null

  const missingUrl = import.meta.env.PROD && !import.meta.env.VITE_API_URL

  return (
    <div className="bg-amber-50 border-b border-amber-200 px-4 py-2.5 flex items-center gap-3 text-sm text-amber-900">
      <WifiOff className="w-4 h-4 shrink-0" />
      <div className="flex-1 min-w-0">
        {missingUrl ? (
          <span>
            <strong>API non configurée.</strong> Ajoutez la variable{' '}
            <code className="bg-amber-100 px-1 rounded">VITE_API_URL</code> dans Netlify
            (ex. https://votre-api.onrender.com/api).
          </span>
        ) : (
          <span>
            Impossible de joindre l'API ({getApiBase()}). Vérifiez que le backend est déployé et en ligne.
          </span>
        )}
      </div>
      <Wifi className="w-4 h-4 opacity-40 shrink-0" />
    </div>
  )
}
