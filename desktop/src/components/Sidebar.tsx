import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, Sparkles, Package, BarChart3, Camera, FileText,
  MessageSquare, Settings, User, TrendingUp, LogIn,
} from 'lucide-react'

const NAV_MAIN = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/opportunities', icon: TrendingUp, label: 'Opportunités' },
  { to: '/ai', icon: MessageSquare, label: 'Assistant IA' },
  { to: '/stock', icon: Package, label: 'Stock' },
]

const NAV_MORE = [
  { to: '/vinted', icon: User, label: 'Mon Vinted' },
  { to: '/vinted/connect', icon: LogIn, label: 'Connexion' },
  { to: '/listings', icon: FileText, label: 'Annonces' },
  { to: '/photos', icon: Camera, label: 'AI Photo Studio' },
  { to: '/stats', icon: BarChart3, label: 'Statistiques' },
  { to: '/settings', icon: Settings, label: 'Paramètres' },
]

export default function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const location = useLocation()

  const isActive = (to: string) => to === '/' ? location.pathname === '/' : location.pathname.startsWith(to)

  return (
    <aside className="w-full h-full flex flex-col bg-white/80 backdrop-blur-2xl border-r border-slate-200/60">
      <div className="p-6">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-violet-600 to-violet-800 flex items-center justify-center shadow-lg shadow-violet-500/30">
            <TrendingUp className="w-5 h-5 text-white" strokeWidth={2.5} />
          </div>
          <div>
            <div className="font-bold text-base text-slate-900">ResellPro</div>
            <div className="text-[11px] font-semibold text-violet-600">Pro Edition</div>
          </div>
        </div>
      </div>

      <nav className="flex-1 px-4 space-y-1 overflow-y-auto">
        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest px-4 mb-2">Principal</p>
        {NAV_MAIN.map(({ to, icon: Icon, label }) => (
          <NavLink key={to} to={to} onClick={onNavigate}
            className={isActive(to) ? 'nav-item-active' : 'nav-item-inactive'}>
            <Icon className="w-4 h-4" strokeWidth={isActive(to) ? 2.5 : 2} />
            {label}
          </NavLink>
        ))}

        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest px-4 mt-6 mb-2">Outils</p>
        {NAV_MORE.map(({ to, icon: Icon, label }) => (
          <NavLink key={to} to={to} onClick={onNavigate}
            className={isActive(to) ? 'nav-item-active' : 'nav-item-inactive'}>
            <Icon className="w-4 h-4" strokeWidth={isActive(to) ? 2.5 : 2} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 m-4 rounded-3xl bg-gradient-to-br from-violet-50 to-violet-100/50 border border-violet-100">
        <div className="flex items-center gap-2 text-xs font-semibold text-violet-700">
          <Sparkles className="w-4 h-4" />
          IA OpenRouter active
        </div>
        <p className="text-[11px] text-violet-500 mt-1">Modèles gratuits · Analyse auto</p>
      </div>
    </aside>
  )
}
