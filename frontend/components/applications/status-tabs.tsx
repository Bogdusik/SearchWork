import type { ApplicationStatus } from '@/types'

const TABS: { value: ApplicationStatus | 'all'; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'saved', label: 'Saved' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'applied', label: 'Applied' },
  { value: 'interview', label: 'Interview' },
  { value: 'offer', label: 'Offer' },
  { value: 'rejected', label: 'Rejected' },
]

interface StatusTabsProps {
  active: ApplicationStatus | 'all'
  counts: Record<string, number>
  onChange: (value: ApplicationStatus | 'all') => void
}

export function StatusTabs({ active, counts, onChange }: StatusTabsProps) {
  return (
    <div className="flex gap-2 flex-wrap mb-6">
      {TABS.map((tab) => (
        <button
          key={tab.value}
          onClick={() => onChange(tab.value)}
          className={`min-h-[44px] px-4 py-2 rounded-full text-xs border transition-colors flex items-center ${
            active === tab.value
              ? 'bg-indigo-500/20 border-indigo-500/50 text-indigo-300'
              : 'bg-transparent border-white/10 text-white/35 hover:text-white/60'
          }`}
        >
          {tab.label}{counts[tab.value] !== undefined ? ` (${counts[tab.value]})` : ''}
        </button>
      ))}
    </div>
  )
}
