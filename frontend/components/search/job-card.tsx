'use client'

import type { Job } from '@/types'
import { api } from '@/lib/api'
import { useState } from 'react'

interface JobCardProps {
  job: Job
}

const matchColor = (score: number) =>
  score >= 80 ? 'bg-emerald-500/15 text-emerald-400' :
  score >= 60 ? 'bg-indigo-500/15 text-indigo-400' :
  'bg-white/5 text-white/40'

export function JobCard({ job }: JobCardProps) {
  const [status, setStatus] = useState<'idle' | 'saved' | 'applied'>('idle')
  const [actionError, setActionError] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState(false)

  const apply = async () => {
    if (actionLoading) return
    setActionLoading(true)
    setActionError(null)
    try {
      await api.applications.create(job.id, 'applied')
      setStatus('applied')
      if (job.url) window.open(job.url, '_blank')
    } catch {
      setActionError('Could not save application. Please try again.')
    } finally {
      setActionLoading(false)
    }
  }

  const save = async () => {
    if (actionLoading) return
    setActionLoading(true)
    setActionError(null)
    try {
      await api.applications.create(job.id, 'saved')
      setStatus('saved')
    } catch {
      setActionError('Could not save job. Please try again.')
    } finally {
      setActionLoading(false)
    }
  }

  const salary = job.salary_min && job.salary_max
    ? `£${(job.salary_min / 1000).toFixed(0)}k–£${(job.salary_max / 1000).toFixed(0)}k`
    : null

  return (
    <div className="glass p-5 space-y-3">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-sm font-semibold text-white/90">{job.title}</div>
          <div className="text-xs text-white/40 mt-0.5">
            {job.company} · {job.location}{salary ? ` · ${salary}` : ''} · <span className="capitalize">{job.source}</span>
          </div>
        </div>
        <span className={`text-xs font-bold rounded-full px-2.5 py-1 shrink-0 ${matchColor(job.match_score)}`}>
          {job.match_score}%
        </span>
      </div>
      <p className="text-xs text-white/30 line-clamp-2">{job.description}</p>
      {actionError && <p className="text-rose-400 text-xs">{actionError}</p>}
      <div className="flex gap-2 pt-1">
        {status === 'applied' ? (
          <span className="text-xs text-emerald-400">✅ Applied</span>
        ) : status === 'saved' ? (
          <span className="text-xs text-white/40">Saved</span>
        ) : (
          <>
            <button
              onClick={apply}
              disabled={actionLoading}
              className="px-4 py-1.5 rounded-lg text-xs bg-indigo-500/20 border border-indigo-500/40 text-indigo-300 hover:bg-indigo-500/30 disabled:opacity-40 transition-colors"
            >
              {actionLoading ? '...' : 'Apply Now'}
            </button>
            <button
              onClick={save}
              disabled={actionLoading}
              className="px-4 py-1.5 rounded-lg text-xs bg-white/5 border border-white/10 text-white/40 hover:text-white/60 disabled:opacity-40 transition-colors"
            >
              Save
            </button>
          </>
        )}
      </div>
    </div>
  )
}
