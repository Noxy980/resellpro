import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Sparkles, TrendingUp } from 'lucide-react'
import { api } from '../api'

interface Message { role: 'user' | 'assistant'; content: string }

const SUGGESTIONS = [
  'Est-ce une bonne affaire ?',
  'Quel prix dois-je mettre ?',
  'Comment vendre cet article rapidement ?',
  'Quels vêtements acheter actuellement ?',
  'Quelles marques se revendent le mieux ?',
]

export default function AIAssistant() {
  const [messages, setMessages] = useState<Message[]>([{
    role: 'assistant',
    content: "Bonjour ! Je suis votre assistant expert en revente Vinted. Posez-moi vos questions sur les achats, les prix, les tendances ou la stratégie de vente. Je m'améliore à chaque utilisation.",
  }])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const send = async (text: string) => {
    if (!text.trim() || loading) return
    setMessages(m => [...m, { role: 'user', content: text }])
    setInput('')
    setLoading(true)
    try {
      const res = await api.chat(text)
      setMessages(m => [...m, { role: 'assistant', content: res.reply }])
    } catch {
      setMessages(m => [...m, { role: 'assistant', content: 'Erreur de connexion à l\'IA. Vérifiez votre clé OpenRouter.' }])
    } finally { setLoading(false) }
  }

  const trends = async () => {
    setLoading(true)
    try {
      const res = await api.trends()
      setMessages(m => [...m, { role: 'user', content: 'Quelles sont les tendances actuelles ?' },
        { role: 'assistant', content: res.analysis }])
    } finally { setLoading(false) }
  }

  return (
    <div className="flex flex-col h-screen animate-fade-in">
      <div className="px-8 pt-8 pb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-violet-100 rounded-xl flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-violet-600" />
            </div>
            <div>
              <h1 className="page-title">Assistant IA</h1>
              <p className="page-subtitle">Propulsé par OpenRouter — modèles gratuits</p>
            </div>
          </div>
          <button onClick={trends} className="btn-secondary text-xs">
            <TrendingUp className="w-3.5 h-3.5" />Tendances du moment
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-8 space-y-4 max-w-3xl">
        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
            <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${
              msg.role === 'assistant' ? 'bg-violet-100' : 'bg-gray-100'
            }`}>
              {msg.role === 'assistant'
                ? <Bot className="w-4 h-4 text-violet-600" />
                : <User className="w-4 h-4 text-gray-500" />}
            </div>
            <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
              msg.role === 'assistant'
                ? 'bg-white border border-gray-100 shadow-sm text-gray-800'
                : 'bg-gray-900 text-white'
            }`}>{msg.content}</div>
          </div>
        ))}
        {loading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 bg-violet-100 rounded-xl flex items-center justify-center">
              <Bot className="w-4 h-4 text-violet-600 animate-pulse" />
            </div>
            <div className="bg-white border border-gray-100 rounded-2xl px-4 py-3 text-sm text-gray-400 shadow-sm">
              Réflexion en cours...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {messages.length <= 1 && (
        <div className="px-8 pb-2 flex flex-wrap gap-2 max-w-3xl">
          {SUGGESTIONS.map(s => (
            <button key={s} onClick={() => send(s)} className="btn-secondary text-xs">{s}</button>
          ))}
        </div>
      )}

      <div className="px-8 py-4 border-t border-gray-100 bg-white/50 backdrop-blur-sm">
        <div className="flex gap-2 max-w-3xl">
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
