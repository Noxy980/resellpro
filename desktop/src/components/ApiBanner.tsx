import { useEffect, useState } from 'react'
import { WifiOff, RefreshCw, Loader2, Server } from 'lucide-react'
import { wakeApi, getApiBase } from '../api'

type Status = 'checking' | 'waking' | 'online' | 'offline'

export default function ApiBanner() {
  const [status, setStatus] = useState<Status>('checking')
  const [attempt, setAttempt] = useState(0)

  const connect = async () => {
    setStatus('waking')
    setAttempt(0)
    const ok = await wakeApi()
    setStatus(ok ? 'online' : 'offline')
  }

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      setStatus('waking')
      for (let i = 1; i <= 4; i++) {
        if (cancelled) return
        setAttempt(i)
        const ok = await wakeApi()
        if (ok) {
          if (!cancelled) setStatus('online')
          return
        }
      }
      if (!cancelled) setStatus('offline')
    })()
    return () => { cancelled = true }
  }, [])

  if (status === 'checking' || status === 'online') return null

  if (status === 'waking') {
    return (
      <div className="bg-gradient-to-r from-violet-600 to-violet-700 text-white px-4 py-3 flex items-center gap-3 text-sm relative z-50">
        <Loader2 className="w-5 h-5 animate-spin shrink-0" />
        <div className="flex-1">
          <p className="font-bold">Connexion au serveur...</p>
          <p className="text-xs text-violet-200 mt-0.5">
            Render (plan gratuit) peut prendre jusqu'à 60 secondes au réveil — tentative {attempt}/4
          </p>
        </div>
        <Server className="w-5 h-5 opacity-60 shrink-0" />
      </div>
    )
  }

  return (
    <div className="bg-gradient-to-r from-amber-50 to-orange-50 border-b border-amber-200/80 px-4 py-3 flex items-start gap-3 text-sm text-amber-900 relative z-50">
      <WifiOff className="w-5 h-5 shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <p className="font-bold">Impossible de joindre l'API</p>
        <p className="text-xs mt-1 text-amber-700">
          {getApiBase()} — Appuyez sur Réveiller et attendez 30-60 secondes.
        </p>
      </div>
      <button
        onClick={connect}
        className="shrink-0 flex items-center gap-1.5 px-3 py-2 rounded-xl bg-violet-600 text-white text-xs font-bold hover:bg-violet-700"
      >
        <RefreshCw className="w-3.5 h-3.5" />
        Réveiller
      </button>
    </div>
  )
}
