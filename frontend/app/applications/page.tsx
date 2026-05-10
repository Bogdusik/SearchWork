'use client'

import { useState, useEffect, useMemo } from 'react'
import { api } from '@/lib/api'
import type { Application, ApplicationStatus } from '@/types'
import { StatusTabs } from '@/components/applications/status-tabs'
import { ApplicationRow } from '@/components/applications/application-row'

type FilterValue = ApplicationStatus | 'all'

export default function ApplicationsPage() {
  const [applications, setApplications] = useState<Application[]>([])
  const [filter, setFilter] = useState<FilterValue>('all')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    api.applications.list()
      .then(setApplications)
      .catch(() => setError(true))
      .finally(() => setLoading(false))
  }, [])

  const counts = useMemo(() => {
    const c: Record<string, number> = { all: applications.length }
    for (const app of applications) {
      c[app.status] = (c[app.status] ?? 0) + 1
    }
    return c
  }, [applications])

  const handleStatusChange = (id: number, newStatus: ApplicationStatus) => {
    setApplications(prev =>
      prev.map(app => app.id === id ? { ...app, status: newStatus } : app)
    )
  }

  const filtered = filter === 'all' ? applications : applications.filter(a => a.status === filter)

  return (
    <div className="max-w-2xl">
      <p className="text-xs text-white/30 uppercase tracking-widest mb-1">Track Progress</p>
      <h1 className="text-3xl font-bold bg-gradient-to-b from-white to-white/75 bg-clip-text text-transparent mb-8">
        My Applications
      </h1>
      {error && <p className="text-rose-400 text-sm mb-4">Could not load applications. Please refresh.</p>}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="w-6 h-6 border-2 border-indigo-500/50 border-t-indigo-400 rounded-full animate-spin" />
        </div>
      ) : (
        <>
          <StatusTabs active={filter} counts={counts} onChange={setFilter} />
          <div className="space-y-3">
            {filtered.length === 0 ? (
              <p className="text-white/30 text-sm">No applications here yet.</p>
            ) : (
              filtered.map((app) => <ApplicationRow key={app.id} application={app} onStatusChange={handleStatusChange} />)
            )}
          </div>
        </>
      )}
    </div>
  )
}
