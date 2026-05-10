'use client'

import { useState } from 'react'
import type { Application, ApplicationStatus } from '@/types'
import { api } from '@/lib/api'

const STATUS_OPTIONS: { value: ApplicationStatus; label: string }[] = [
  { value: 'saved', label: 'Saved' },
  { value: 'applied', label: 'Applied' },
  { value: 'interview', label: 'Interview' },
  { value: 'offer', label: 'Offer' },
  { value: 'rejected', label: 'Rejected' },
]

const STATUS_COLORS: Record<ApplicationStatus, string> = {
  saved: 'text-white/40',
  applied: 'text-emerald-400',
  interview: 'text-indigo-400',
  offer: 'text-amber-400',
  rejected: 'text-rose-400',
}

interface ApplicationRowProps {
  application: Application
  onStatusChange?: (id: number, newStatus: ApplicationStatus) => void
}

export function ApplicationRow({ application, onStatusChange }: ApplicationRowProps) {
  const [status, setStatus] = useState<ApplicationStatus>(application.status as ApplicationStatus)
  const [updating, setUpdating] = useState(false)

  const handleChange = async (newStatus: ApplicationStatus) => {
    if (updating) return
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

  return (
    <div className="glass p-4 flex items-center justify-between gap-4">
      <div className="min-w-0">
        <div className="text-sm font-medium text-white/85 truncate">{application.job.title}</div>
        <div className="text-xs text-white/30 mt-0.5">
          {application.job.company} · {application.job.location}
          {salary ? ` · ${salary}` : ''}
          {application.applied_at
            ? ` · Applied ${new Date(application.applied_at).toLocaleDateString('en-GB')}`
            : ''}
        </div>
      </div>
      <div className="flex items-center gap-3 shrink-0">
        <span className="text-xs font-semibold text-indigo-300">{application.job.match_score}%</span>
        <select
          value={status}
          disabled={updating}
          onChange={(e) => handleChange(e.target.value as ApplicationStatus)}
          className={`bg-transparent border border-current/40 rounded-lg px-2 py-1 text-xs outline-none cursor-pointer disabled:opacity-50 ${STATUS_COLORS[status]}`}
        >
          {STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value} className="bg-[#030303] text-white">
              {opt.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  )
}
