import { NavLink, useLocation } from 'react-router-dom'
import { LayoutDashboard, TrendingUp, MessageSquare, Package, User } from 'lucide-react'

const TABS = [
  { to: '/', icon: LayoutDashboard, label: 'Accueil' },
  { to: '/opportunities', icon: TrendingUp, label: 'Deals' },
  { to: '/ai', icon: MessageSquare, label: 'IA' },
  { to: '/stock', icon: Package, label: 'Stock' },
  { to: '/vinted', icon: User, label: 'Vinted' },
]

export default function MobileNav() {
  const { pathname } = useLocation()

  return (
    <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-2xl border-t border-slate-200/80 px-2 pt-2 pb-[max(0.5rem,env(safe-area-inset-bottom))] shadow-[0_-8px_32px_-8px_rgba(0,0,0,0.1)]">
      <div className="flex items-center justify-around max-w-lg mx-auto">
        {TABS.map(({ to, icon: Icon, label }) => {
          const active = to === '/' ? pathname === '/' : pathname.startsWith(to)
          return (
            <NavLink key={to} to={to} className={active ? 'mobile-nav-active' : 'mobile-nav-inactive'}>
              <Icon className={`w-5 h-5 ${active ? 'text-violet-600' : ''}`} strokeWidth={active ? 2.5 : 2} />
              <span>{label}</span>
            </NavLink>
          )
        })}
      </div>
    </nav>
  )
}
