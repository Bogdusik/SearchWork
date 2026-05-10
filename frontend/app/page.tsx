import { api } from '@/lib/api'
import { StatsRow } from '@/components/dashboard/stats-row'
import { RecentJobs } from '@/components/dashboard/recent-jobs'

export default async function DashboardPage() {
  const applications = await api.applications.list().catch(() => [])

  const totalApplications = applications.filter(a => a.status !== 'saved').length
  const responses = applications.filter(a => ['interview', 'offer', 'rejected'].includes(a.status)).length
  const bestMatch = applications.length > 0 ? Math.max(...applications.map(a => a.job.match_score)) : 0

  return (
    <div className="max-w-2xl">
      <div className="mb-8">
        <p className="text-xs text-white/30 uppercase tracking-widest mb-1">Overview</p>
        <h1 className="text-3xl font-bold bg-gradient-to-b from-white to-white/75 bg-clip-text text-transparent">
          Welcome back, Bohdan
        </h1>
      </div>
      <StatsRow totalApplications={totalApplications} responses={responses} bestMatch={bestMatch} />
      <div>
        <h2 className="text-sm font-medium text-white/50 uppercase tracking-widest mb-4">Recent Applications</h2>
        <RecentJobs applications={applications} />
      </div>
    </div>
  )
}
