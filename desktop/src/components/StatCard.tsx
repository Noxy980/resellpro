import { LucideIcon } from 'lucide-react'

export function StatCard({
  icon: Icon,
  label,
  value,
  sub,
  accent = 'violet',
}: {
  icon: LucideIcon
  label: string
  value: string
  sub?: string
  accent?: 'violet' | 'emerald' | 'blue' | 'amber'
}) {
  const accents = {
    violet: { bg: 'bg-violet-500', light: 'bg-violet-50 text-violet-600', ring: 'ring-violet-100' },
    emerald: { bg: 'bg-emerald-500', light: 'bg-emerald-50 text-emerald-600', ring: 'ring-emerald-100' },
    blue: { bg: 'bg-blue-500', light: 'bg-blue-50 text-blue-600', ring: 'ring-blue-100' },
    amber: { bg: 'bg-amber-500', light: 'bg-amber-50 text-amber-600', ring: 'ring-amber-100' },
  }
  const a = accents[accent]

  return (
    <div className={`stat-card ring-1 ${a.ring}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <p className="text-xs md:text-sm font-medium text-slate-500 mb-1">{label}</p>
          <p className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">{value}</p>
          {sub && <p className="text-xs text-slate-400 mt-1">{sub}</p>}
        </div>
        <div className={`w-11 h-11 md:w-12 md:h-12 rounded-2xl ${a.light} flex items-center justify-center shrink-0`}>
          <Icon className="w-5 h-5" strokeWidth={2.5} />
        </div>
      </div>
    </div>
  )
}

export function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="skeleton h-40 md:h-48 rounded-3xl" />
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
        {[1, 2, 3, 4].map(i => <div key={i} className="skeleton h-28 rounded-3xl" />)}
      </div>
      <div className="skeleton h-24 rounded-3xl" />
      <div className="space-y-3">
        {[1, 2, 3].map(i => <div key={i} className="skeleton h-20 rounded-3xl" />)}
      </div>
    </div>
  )
}
