import { useState } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Menu, X } from 'lucide-react'
import Sidebar from './components/Sidebar'
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
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-[#f8f9fc]">
      <div className="absolute inset-0 bg-gradient-to-br from-violet-50/40 via-transparent to-blue-50/20 pointer-events-none" />
      <ApiBanner />

      <div className="lg:hidden flex items-center justify-between px-4 py-3 border-b border-gray-100 bg-white/80 backdrop-blur-xl relative z-20">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-gray-900 rounded-lg flex items-center justify-center text-white text-xs font-bold">RP</div>
          <span className="font-semibold text-sm">ResellPro</span>
        </div>
        <button onClick={() => setMobileOpen(o => !o)} className="p-2 rounded-lg hover:bg-gray-100" aria-label="Menu">
          {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      <div className="flex flex-1 overflow-hidden relative">
        <div className={`${mobileOpen ? 'block' : 'hidden'} lg:block absolute lg:relative z-30 h-full`}>
          <Sidebar onNavigate={() => setMobileOpen(false)} />
        </div>
        {mobileOpen && (
          <div className="fixed inset-0 bg-black/20 z-20 lg:hidden" onClick={() => setMobileOpen(false)} />
        )}
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
    </div>
  )
}
