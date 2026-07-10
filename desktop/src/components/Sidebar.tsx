import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, Sparkles, Package, BarChart3, Camera, FileText,
  MessageSquare, Settings, User, TrendingUp, LogIn,
} from 'lucide-react'

const NAV = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/opportunities', icon: TrendingUp, label: 'Opportunités' },
  { to: '/ai', icon: MessageSquare, label: 'Assistant IA' },
  { to: '/vinted', icon: User, label: 'Mon Vinted' },
  { to: '/vinted/connect', icon: LogIn, label: 'Connexion Vinted' },
  { to: '/listings', icon: FileText, label: 'Annonces' },
  { to: '/stock', icon: Package, label: 'Stock' },
  { to: '/photos', icon: Camera, label: 'AI Photo Studio' },
  { to: '/stats', icon: BarChart3, label: 'Statistiques' },
  { to: '/settings', icon: Settings, label: 'Paramètres' },
]

export default function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const location = useLocation()

  return (
    <aside className="w-60 shrink-0 flex flex-col h-full bg-white/90 backdrop-blur-xl border-r border-gray-100 shadow-lg lg:shadow-none">
      <div className="p-5 mb-1">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-gray-900 rounded-xl flex items-center justify-center">
            <TrendingUp className="w-4 h-4 text-white" />
          </div>
          <div>
            <div className="font-semibold text-sm text-gray-900">ResellPro</div>
            <div className="text-[11px] text-gray-400">Assistant revendeur Pro</div>
          </div>
        </div>
      </div>

      <nav className="flex-1 px-3 space-y-0.5 overflow-y-auto">
        {NAV.map(({ to, icon: Icon, label }) => {
          const active = location.pathname === to
          return (
            <NavLink key={to} to={to} onClick={onNavigate}
              className={active ? 'nav-item-active' : 'nav-item-inactive'}>
              <Icon className="w-4 h-4" />
              {label}
            </NavLink>
          )
        })}
      </nav>

      <div className="p-4 mx-3 mb-3 glass rounded-xl">
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <Sparkles className="w-3.5 h-3.5 text-violet-500" />
          IA OpenRouter · Modèles gratuits
        </div>
      </div>
    </aside>
  )
}
