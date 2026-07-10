import { Routes, Route, Navigate } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import MobileNav from './components/MobileNav'
import ApiBanner from './components/ApiBanner'
import Dashboard from './pages/Dashboard'
import Opportunities from './pages/Opportunities'
import AIAssistant from './pages/AIAssistant'
import Inventory from './pages/Inventory'
import Statistics from './pages/Statistics'
import PhotoEnhance from './pages/PhotoEnhance'
import ListingCreator from './pages/ListingCreator'
import SettingsPage from './pages/SettingsPage'
import VintedAccount from './pages/VintedAccount'
import VintedConnect from './pages/VintedConnect'

export default function App() {
  return (
    <div className="flex flex-col min-h-screen mesh-bg">
      <ApiBanner />

      {/* Mobile header */}
      <header className="lg:hidden sticky top-0 z-40 flex items-center justify-between px-4 py-3 bg-white/80 backdrop-blur-2xl border-b border-slate-200/60">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-violet-600 to-violet-800 flex items-center justify-center shadow-lg shadow-violet-500/30">
            <span className="text-white font-bold text-sm">RP</span>
          </div>
          <div>
            <p className="font-bold text-slate-900 text-sm leading-tight">ResellPro</p>
            <p className="text-[10px] text-violet-600 font-semibold">Assistant revendeur</p>
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Desktop sidebar */}
        <div className="hidden lg:flex shrink-0">
          <Sidebar />
        </div>

        <main className="flex-1 overflow-auto relative">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/opportunities" element={<Opportunities />} />
            <Route path="/ai" element={<AIAssistant />} />
            <Route path="/vinted" element={<VintedAccount />} />
            <Route path="/vinted/connect" element={<VintedConnect />} />
            <Route path="/listings" element={<ListingCreator />} />
            <Route path="/stock" element={<Inventory />} />
            <Route path="/photos" element={<PhotoEnhance />} />
            <Route path="/stats" element={<Statistics />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>

      <MobileNav />
    </div>
  )
}
