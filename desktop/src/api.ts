const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8420/api'
const IS_PROD = import.meta.env.PROD
const TIMEOUT_MS = IS_PROD ? 20000 : 8000

export function getApiBase(): string {
  return API.replace(/\/$/, '')
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS)
  try {
    const res = await fetch(`${API}${path}`, {
      headers: { 'Content-Type': 'application/json', ...options?.headers },
      signal: controller.signal,
      ...options,
    })
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new Error('Le serveur met trop de temps à répondre. Vérifiez que l\'API backend est en ligne.')
    }
    if (IS_PROD && !import.meta.env.VITE_API_URL) {
      throw new Error('API non configurée. Définissez VITE_API_URL sur Netlify.')
    }
    throw err
  } finally {
    clearTimeout(timeout)
  }
}

export interface Opportunity {
  id: number; vinted_id: number; title: string; brand: string; model: string
  category: string; size: string; condition: string; price: number
  estimated_resale: number; potential_profit: number; profit_percent: number
  score: number; demand_level: string; selling_speed: string
  quick_sale_probability: number; why_buy: string; risk: string
  url: string; image_url: string | null; status: string; found_at: string
}

export interface InventoryItem {
  id: number; title: string; brand: string; model: string; size: string
  condition: string; purchase_price: number; purchase_date: string
  planned_resale_price: number; actual_sale_price: number | null
  sale_date: string | null; status: string; notes: string
  vinted_listing_url: string; real_profit: number | null; margin_percent: number | null
}

export interface Stats {
  total_profit: number; total_items_sold: number; avg_profit: number
  avg_margin: number; success_rate: number
  best_brands: { brand: string; profit: number }[]
  best_categories: { category: string; profit: number }[]
  profit_timeline: { date: string; profit: number }[]
}

export interface VintedProfile {
  id?: number; login?: string; photo?: string; item_count?: number
  feedback_count?: number; positive_feedback?: number
  is_connected: boolean; error?: string
}

export interface DraftListing {
  id: number; title: string; brand: string; price: number
  status: string; created_at: string
}

export const api = {
  connectVinted: (country = 'fr') =>
    request<{ connected: boolean }>('/vinted/connect', { method: 'POST', body: JSON.stringify({ country }) }),

  vintedStatus: () => request<{ connected: boolean; country: string; username: string }>('/vinted/status'),
  vintedProfile: () => request<VintedProfile>('/vinted/profile'),
  vintedListings: () => request<{ listings: Record<string, unknown>[] }>('/vinted/listings'),

  opportunities: (params: Record<string, string | number> = {}) => {
    const q = new URLSearchParams()
    Object.entries(params).forEach(([k, v]) => { if (v !== undefined && v !== '') q.set(k, String(v)) })
    return request<Opportunity[]>(`/opportunities?${q}`)
  },

  opportunity: (id: number) => request<Opportunity>(`/opportunities/${id}`),
  opportunityAction: (id: number, action: string) =>
    request(`/opportunities/${id}/action`, { method: 'POST', body: JSON.stringify({ action }) }),
  scan: () => request<{ found: number; opportunities: Opportunity[] }>('/opportunities/scan', { method: 'POST' }),
  monitorStatus: () => request<{ running: boolean; status: string; last_scan: string | null }>('/monitor/status'),

  chat: (message: string, opportunityId?: number) =>
    request<{ reply: string; ai_available: boolean }>('/ai/chat', {
      method: 'POST', body: JSON.stringify({ message, opportunity_id: opportunityId }),
    }),
  analyze: (id: number) => request<{ analysis: string }>(`/ai/analyze/${id}`, { method: 'POST' }),
  trends: () => request<{ analysis: string }>('/ai/trends', { method: 'POST' }),

  generateListing: (data: Record<string, unknown>) =>
    request<Record<string, string>>('/ai/generate-listing', { method: 'POST', body: JSON.stringify(data) }),
  createDraft: (data: Record<string, unknown>) =>
    request<Record<string, unknown>>('/drafts', { method: 'POST', body: JSON.stringify(data) }),
  drafts: () => request<DraftListing[]>('/drafts'),
  getDraft: (id: number) => request<Record<string, unknown>>(`/drafts/${id}`),

  enhancePhoto: async (file: File, removeBg = false) => {
    const form = new FormData()
    form.append('file', file)
    const res = await fetch(`${API}/photos/enhance?remove_bg=${removeBg}`, { method: 'POST', body: form })
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  },

  inventory: (status?: string) => request<InventoryItem[]>(`/inventory${status ? '?status=' + status : ''}`),
  createInventory: (data: Record<string, unknown>) =>
    request<InventoryItem>('/inventory', { method: 'POST', body: JSON.stringify(data) }),
  updateInventory: (id: number, data: Record<string, unknown>) =>
    request<InventoryItem>(`/inventory/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),

  statistics: () => request<Stats>('/statistics'),
  dashboard: () => request<Record<string, unknown>>('/dashboard'),
  deleteInventory: (id: number) => request(`/inventory/${id}`, { method: 'DELETE' }),
  profile: () => request<Record<string, unknown>>('/profile'),
  settings: () => request<Record<string, unknown>>('/settings'),
  updateSettings: (data: Record<string, unknown>) =>
    request('/settings', { method: 'PATCH', body: JSON.stringify(data) }),
}
