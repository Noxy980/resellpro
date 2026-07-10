import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Sparkles, TrendingUp, Trash2 } from 'lucide-react'
import { api, ChatMessage } from '../api'
import PageShell from '../components/PageShell'

const WELCOME = "Bonjour ! Je suis votre assistant expert en revente Vinted. Posez-moi vos questions sur les achats, les prix, les tendances ou la stratégie de vente."

const SUGGESTIONS = [
  'Quels vêtements acheter en ce moment ?',
  'Quelles marques se revendent le mieux ?',
  'Comment fixer le bon prix ?',
  'Conseils pour vendre plus vite',
]

export default function AIAssistant() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [loaded, setLoaded] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    api.chatHistory()
      .then(msgs => {
        if (msgs.length > 0) {
          setMessages(msgs)
        } else {
          setMessages([{ id: 0, role: 'assistant', content: WELCOME, created_at: new Date().toISOString() }])
        }
      })
      .catch(() => {
        setMessages([{ id: 0, role: 'assistant', content: WELCOME, created_at: new Date().toISOString() }])
      })
      .finally(() => setLoaded(true))
  }, [])

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const send = async (text: string) => {
    if (!text.trim() || loading) return
    const userMsg: ChatMessage = { id: Date.now(), role: 'user', content: text, created_at: new Date().toISOString() }
    setMessages(m => [...m, userMsg])
    setInput('')
    setLoading(true)
    try {
      const res = await api.chat(text)
      setMessages(m => [...m, {
        id: Date.now() + 1, role: 'assistant', content: res.reply, created_at: new Date().toISOString(),
      }])
    } catch {
      setMessages(m => [...m, {
        id: Date.now() + 1, role: 'assistant',
        content: 'Erreur de connexion à l\'IA. Vérifiez que l\'API Render est en ligne.',
        created_at: new Date().toISOString(),
      }])
    } finally { setLoading(false) }
  }

  const clear = async () => {
    await api.clearChatHistory()
    setMessages([{ id: 0, role: 'assistant', content: WELCOME, created_at: new Date().toISOString() }])
  }

  const trends = async () => {
    setLoading(true)
    try {
      const res = await api.trends()
      setMessages(m => [...m,
        { id: Date.now(), role: 'user', content: 'Quelles sont les tendances actuelles ?', created_at: new Date().toISOString() },
        { id: Date.now() + 1, role: 'assistant', content: res.analysis, created_at: new Date().toISOString() },
      ])
    } finally { setLoading(false) }
  }

  if (!loaded) {
    return <PageShell><div className="skeleton h-96 rounded-3xl" /></PageShell>
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] lg:h-[calc(100vh-2rem)]">
      <PageShell className="!pb-4 flex-shrink-0">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 bg-gradient-to-br from-violet-500 to-violet-700 rounded-2xl flex items-center justify-center shadow-lg shadow-violet-500/30">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="page-title text-xl">Assistant IA</h1>
              <p className="text-xs text-violet-600 font-medium">Historique sauvegardé · OpenRouter</p>
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={trends} className="btn-secondary text-xs py-2">
              <TrendingUp className="w-3.5 h-3.5" />Tendances
            </button>
            <button onClick={clear} className="btn-ghost text-xs py-2 text-red-500">
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </PageShell>

      <div className="flex-1 overflow-y-auto px-4 md:px-8 space-y-4 max-w-3xl mx-auto w-full">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
            <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${
              msg.role === 'assistant' ? 'bg-violet-100' : 'bg-slate-200'
            }`}>
              {msg.role === 'assistant'
                ? <Bot className="w-4 h-4 text-violet-600" />
                : <User className="w-4 h-4 text-slate-600" />}
            </div>
            <div className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
              msg.role === 'assistant'
                ? 'bg-white border border-slate-100 shadow-soft text-slate-800'
                : 'bg-slate-900 text-white'
            }`}>{msg.content}</div>
          </div>
        ))}
        {loading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 bg-violet-100 rounded-xl flex items-center justify-center">
              <Bot className="w-4 h-4 text-violet-600 animate-pulse" />
            </div>
            <div className="bg-white border border-slate-100 rounded-2xl px-4 py-3 text-sm text-slate-400 shadow-soft">
              Réflexion en cours...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {messages.length <= 2 && (
        <div className="px-4 md:px-8 pb-2 flex flex-wrap gap-2 max-w-3xl mx-auto w-full">
          {SUGGESTIONS.map(s => (
            <button key={s} onClick={() => send(s)} className="btn-secondary text-xs">{s}</button>
          ))}
        </div>
      )}

      <div className="px-4 md:px-8 py-4 border-t border-slate-100 bg-white/80 backdrop-blur-xl pb-24 lg:pb-4">
        <div className="flex gap-2 max-w-3xl mx-auto">
          <input className="input flex-1" placeholder="Posez votre question..."
            value={input} onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && send(input)} />
          <button onClick={() => send(input)} disabled={loading} className="btn-primary px-5">
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
