'use client'

import type { JobSearchResult } from '@/types'
import { api } from '@/lib/api'
import { STATUS_COLORS, STATUS_LABELS } from '@/lib/constants'
import { useState, useEffect } from 'react'

interface JobCardProps {
  job: JobSearchResult
  initialStatus?: string
  onCoverLetter?: () => void
}

type CardStatus = 'idle' | 'saved' | 'in_progress' | 'applied' | 'interview' | 'offer' | 'rejected'

const matchColor = (score: number) =>
  score >= 80 ? 'bg-emerald-500/15 text-emerald-400' :
  score >= 60 ? 'bg-indigo-500/15 text-indigo-400' :
  'bg-white/5 text-white/40'


export function JobCard({ job, initialStatus, onCoverLetter }: JobCardProps) {
  const [status, setStatus] = useState<CardStatus>(
    (initialStatus as CardStatus) ?? 'idle'
  )
  const [actionError, setActionError] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState(false)
  const [showWhy, setShowWhy] = useState(false)

  useEffect(() => {
    if (initialStatus) setStatus(initialStatus as CardStatus)
  }, [initialStatus])

  const apply = async () => {
    if (actionLoading) return
    setActionLoading(true)
    setActionError(null)
    try {
      await api.applications.create(job, 'in_progress')
      setStatus('in_progress')
      if (job.url) window.open(job.url, '_blank')
    } catch (err) {
      if (err instanceof Error && err.message.includes('409')) {
        setStatus('in_progress')
        if (job.url) window.open(job.url, '_blank')
      } else {
        setActionError('Could not save application. Please try again.')
      }
    } finally {
      setActionLoading(false)
    }
  }

  const save = async () => {
    if (actionLoading) return
    setActionLoading(true)
    setActionError(null)
    try {
      await api.applications.create(job, 'saved')
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

      {(job.matched_skills?.length > 0 || job.missing_skills?.length > 0) && (
        <div>
          <button
            onClick={() => setShowWhy(v => !v)}
            className="text-xs text-white/30 hover:text-white/50 transition-colors"
          >
            {showWhy ? '▾ Hide reasoning' : '▸ Why this score?'}
          </button>
          {showWhy && (
            <div className="mt-2 space-y-2">
              {job.matched_skills?.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {job.matched_skills.map(s => (
                    <span key={s} className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/20">
                      ✓ {s}
                    </span>
                  ))}
                </div>
              )}
              {job.missing_skills?.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {job.missing_skills.map(s => (
                    <span key={s} className="text-xs px-2 py-0.5 rounded-full bg-rose-500/15 text-rose-400 border border-rose-500/20">
                      ✗ {s}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {actionError && <p className="text-rose-400 text-xs">{actionError}</p>}
      <div className="flex flex-wrap items-center gap-2 pt-1">
        {status !== 'idle' ? (
          <span className={`text-xs px-4 py-1.5 ${STATUS_COLORS[status] ?? 'text-white/40'}`}>
            {STATUS_LABELS[status] ?? status}
          </span>
        ) : (
          <>
            <button
              onClick={apply}
              disabled={actionLoading}
              className="min-h-[44px] px-4 py-2 rounded-lg text-xs bg-indigo-500/20 border border-indigo-500/40 text-indigo-300 hover:bg-indigo-500/30 disabled:opacity-40 transition-colors"
            >
              {actionLoading ? '...' : 'Apply Now'}
            </button>
            <button
              onClick={save}
              disabled={actionLoading}
              className="min-h-[44px] px-4 py-2 rounded-lg text-xs bg-white/5 border border-white/10 text-white/40 hover:text-white/60 disabled:opacity-40 transition-colors"
            >
              Save
            </button>
          </>
        )}
        <button
          onClick={onCoverLetter}
          className="min-h-[44px] px-4 py-2 rounded-lg text-xs bg-violet-500/15 border border-violet-500/30 text-violet-300 hover:bg-violet-500/25 transition-colors"
        >
          Cover Letter
        </button>
      </div>
    </div>
  )
}
