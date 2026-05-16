'use client'

import { useState } from 'react'
import type { Application, ApplicationStatus } from '@/types'
import { api } from '@/lib/api'
import { CoverLetterModal } from '@/components/ui/cover-letter-modal'
import { STATUS_OPTIONS, STATUS_COLORS } from '@/lib/constants'

interface ApplicationRowProps {
  application: Application
  onStatusChange?: (id: number, newStatus: ApplicationStatus) => void
  onDelete?: (id: number) => void
}

export function ApplicationRow({ application, onStatusChange, onDelete }: ApplicationRowProps) {
  const [status, setStatus] = useState<ApplicationStatus>(application.status as ApplicationStatus)
  const [updating, setUpdating] = useState(false)
  const [showCoverLetter, setShowCoverLetter] = useState(false)

  const handleChange = async (value: string) => {
    if (updating) return

    if (value === '__delete__') {
      setUpdating(true)
      try {
        await api.applications.delete(application.id)
        onDelete?.(application.id)
      } finally {
        setUpdating(false)
      }
      return
    }

    const newStatus = value as ApplicationStatus
    setUpdating(true)
    setStatus(newStatus)
    try {
      await api.applications.updateStatus(application.id, newStatus)
      onStatusChange?.(application.id, newStatus)
    } catch {
      setStatus(application.status as ApplicationStatus)
    } finally {
      setUpdating(false)
    }
  }

  const salary = application.job.salary_min && application.job.salary_max
    ? `£${(application.job.salary_min / 1000).toFixed(0)}k–£${(application.job.salary_max / 1000).toFixed(0)}k`
    : null

  const matched = application.job.matched_skills ?? []
  const missing = application.job.missing_skills ?? []

  return (
    <>
      <div className="glass p-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
        <div className="min-w-0 flex-1">
          <div className="text-sm font-medium text-white/85 truncate">{application.job.title}</div>
          <div className="text-xs text-white/30 mt-0.5">
            {application.job.company} · {application.job.location}
            {salary ? ` · ${salary}` : ''}
            {application.applied_at
              ? ` · Applied ${new Date(application.applied_at).toLocaleDateString('en-GB')}`
              : ''}
          </div>
          {(matched.length > 0 || missing.length > 0) && (
            <div className="flex flex-wrap gap-1 mt-1.5">
              {matched.slice(0, 4).map(s => (
                <span key={s} className="text-xs px-1.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500/70">✓ {s}</span>
              ))}
              {missing.slice(0, 3).map(s => (
                <span key={s} className="text-xs px-1.5 py-0.5 rounded-full bg-rose-500/10 text-rose-500/70">✗ {s}</span>
              ))}
            </div>
          )}
        </div>
        <div className="flex items-center justify-between sm:justify-end gap-2 sm:shrink-0">
          <span className="text-xs font-semibold text-indigo-300">{application.job.match_score}%</span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowCoverLetter(true)}
              aria-label="Generate cover letter"
              title="Generate Cover Letter"
              className="min-h-[44px] px-3 py-2 rounded-lg text-xs bg-violet-500/15 border border-violet-500/30 text-violet-300 hover:bg-violet-500/25 transition-colors"
            >
              CL
            </button>
            <select
              value={status}
              disabled={updating}
              onChange={(e) => handleChange(e.target.value)}
              className={`min-h-[44px] bg-transparent border border-current/40 rounded-lg px-2 py-2 text-xs outline-none cursor-pointer disabled:opacity-50 ${STATUS_COLORS[status]}`}
            >
              {STATUS_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value} className="bg-[#030303] text-white">
                  {opt.label}
                </option>
              ))}
              <option value="__delete__" className="bg-[#030303] text-rose-400">Delete</option>
            </select>
          </div>
        </div>
      </div>

      <CoverLetterModal
        isOpen={showCoverLetter}
        onClose={() => setShowCoverLetter(false)}
        externalId={application.job.external_id}
        source={application.job.source}
        jobTitle={application.job.title}
        company={application.job.company}
        description={application.job.description}
      />
    </>
  )
}
