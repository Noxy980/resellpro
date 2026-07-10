import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Sparkles, TrendingUp, Trash2 } from 'lucide-react'
import { api, ChatMessage } from '../api'
import MarkdownContent from '../components/MarkdownContent'

const WELCOME = `Bonjour ! Je suis **ResellPro AI**, votre expert en achat-revente Vinted.

Je peux vous aider à :
- **Trouver** les meilleures opportunités du moment
- **Fixer** le bon prix de revente
- **Analyser** une marque ou un modèle
- **Optimiser** votre stratégie de vente

Posez-moi une question ou choisissez une suggestion ci-dessous.`

const SUGGESTIONS = [
  'Quels vêtements acheter en ce moment ?',
  'Top marques qui se revendent vite',
  'Comment fixer le bon prix ?',
  'Stratégie pour vendre en 7 jours',
]

export default function AIAssistant() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [loaded, setLoaded] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    api.chatHistory()
      .then(msgs => {
        if (msgs.length > 0) setMessages(msgs)
        else setMessages([{ id: 0, role: 'assistant', content: WELCOME, created_at: new Date().toISOString() }])
      })
      .catch(() => {
        setMessages([{ id: 0, role: 'assistant', content: WELCOME, created_at: new Date().toISOString() }])
      })
      .finally(() => setLoaded(true))
  }, [])

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, loading])

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
        content: '**Erreur de connexion** — Vérifiez que l\'API Render est en ligne.',
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
        { id: Date.now(), role: 'user', content: 'Quelles sont les tendances actuelles du resell ?', created_at: new Date().toISOString() },
        { id: Date.now() + 1, role: 'assistant', content: res.analysis, created_at: new Date().toISOString() },
      ])
    } finally { setLoading(false) }
  }

  if (!loaded) {
    return <div className="p-8 max-w-4xl mx-auto"><div className="skeleton h-96 rounded-3xl" /></div>
  }

  return (
    <div className="flex flex-col h-full min-h-0">
      {/* Header */}
      <div className="shrink-0 px-4 md:px-8 pt-6 pb-4 border-b border-slate-100/80 bg-white/50 backdrop-blur-xl">
        <div className="max-w-4xl mx-auto flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-violet-500 to-indigo-600 rounded-2xl flex items-center justify-center shadow-lg shadow-violet-500/25">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900 font-display">Assistant IA</h1>
              <p className="text-xs text-violet-600 font-medium">Expert resell · Markdown · Historique sauvegardé</p>
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={trends} disabled={loading} className="btn-secondary text-xs py-2">
              <TrendingUp className="w-3.5 h-3.5" />Tendances
            </button>
            <button onClick={clear} className="btn-ghost text-xs py-2 text-red-500">
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto min-h-0 px-4 md:px-8 py-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
              <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 shadow-sm ${
                msg.role === 'assistant'
                  ? 'bg-gradient-to-br from-violet-100 to-indigo-100'
                  : 'bg-slate-800'
              }`}>
                {msg.role === 'assistant'
                  ? <Bot className="w-4 h-4 text-violet-600" />
                  : <User className="w-4 h-4 text-white" />}
              </div>
              <div className={`max-w-[88%] md:max-w-[78%] rounded-2xl px-4 py-3 text-sm ${
                msg.role === 'assistant'
                  ? 'bg-white border border-slate-100 shadow-soft text-slate-800'
                  : 'bg-slate-900 text-white'
              }`}>
                {msg.role === 'assistant'
                  ? <MarkdownContent content={msg.content} />
                  : <p className="leading-relaxed whitespace-pre-wrap">{msg.content}</p>}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex gap-3">
              <div className="w-9 h-9 bg-violet-100 rounded-xl flex items-center justify-center">
                <Bot className="w-4 h-4 text-violet-600" />
              </div>
              <div className="bg-white border border-slate-100 rounded-2xl px-4 py-3 shadow-soft">
                <div className="flex gap-1.5">
                  <span className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      </div>

      {/* Suggestions */}
      {messages.length <= 2 && !loading && (
        <div className="shrink-0 px-4 md:px-8 pb-2">
          <div className="max-w-4xl mx-auto flex flex-wrap gap-2">
            {SUGGESTIONS.map(s => (
              <button key={s} onClick={() => send(s)} className="btn-secondary text-xs">{s}</button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="shrink-0 px-4 md:px-8 py-4 border-t border-slate-100 bg-white/90 backdrop-blur-xl pb-24 lg:pb-5">
        <div className="max-w-4xl mx-auto flex gap-2 items-end">
          <textarea
            ref={textareaRef}
            className="input flex-1 min-h-[44px] max-h-32 resize-none py-3"
            placeholder="Posez votre question sur le resell, les prix, les marques..."
            rows={1}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(input) }
            }}
          />
          <button onClick={() => send(input)} disabled={loading || !input.trim()} className="btn-primary px-5 h-11 shrink-0">
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
