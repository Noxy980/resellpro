import { useEffect, useState } from 'react'
import { api, Opportunity } from './api'

export function useVintedStatus() {
  const [connected, setConnected] = useState(false)
  const [loading, setLoading] = useState(true)
  const [backendDown, setBackendDown] = useState(false)

  useEffect(() => {
    api.vintedStatus()
      .then(s => { setConnected(s.connected); setBackendDown(false) })
      .catch(() => { setConnected(false); setBackendDown(true) })
      .finally(() => setLoading(false))
  }, [])

  return { connected, loading, setConnected, backendDown }
}

export function useOpportunities(filters: Record<string, string | number> = {}) {
  const [data, setData] = useState<Opportunity[]>([])
  const [loading, setLoading] = useState(true)
  const key = JSON.stringify(filters)

  const refresh = () => {
    setLoading(true)
    api.opportunities(filters).then(setData).catch(() => setData([])).finally(() => setLoading(false))
  }

  useEffect(() => { refresh() }, [key])

  return { data, loading, refresh }
}
