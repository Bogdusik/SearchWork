import type { Application } from '@/types'

interface RecentJobsProps {
  applications: Application[]
}

const STATUS_COLORS: Record<string, string> = {
  applied: 'text-emerald-400 border-emerald-400/40',
  interview: 'text-indigo-400 border-indigo-400/40',
  offer: 'text-amber-400 border-amber-400/40',
  rejected: 'text-rose-400 border-rose-400/40',
  saved: 'text-white/40 border-white/10',
}

export function RecentJobs({ applications }: RecentJobsProps) {
  if (applications.length === 0) {
    return (
      <p className="text-white/30 text-sm">
        No applications yet.{' '}
        <a href="/search" className="text-indigo-400 underline">Start searching →</a>
      </p>
    )
  }
  return (
    <div className="space-y-3">
      {applications.slice(0, 5).map((app) => (
        <div key={app.id} className="glass p-4 flex items-center justify-between">
          <div>
            <div className="text-sm font-medium text-white/85">{app.job.title}</div>
            <div className="text-xs text-white/35 mt-0.5">{app.job.company} · {app.job.location}</div>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-indigo-300 font-semibold">{app.job.match_score}%</span>
            <span className={`text-xs border rounded-full px-2 py-0.5 ${STATUS_COLORS[app.status] ?? ''}`}>
              {app.status}
            </span>
          </div>
        </div>
      ))}
    </div>
  )
}
