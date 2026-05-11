'use client'

import { useState } from 'react'
import { api } from '@/lib/api'
import type { CVProfile, CVReview, CVReviewItem, PriorityItem } from '@/types'

interface CvReviewProps {
  profile: CVProfile | null
}

const impactColour: Record<PriorityItem['impact'], string> = {
  Huge: 'text-rose-400 bg-rose-500/10 border-rose-500/20',
  High: 'text-indigo-300 bg-indigo-500/10 border-indigo-500/20',
  Medium: 'text-amber-300 bg-amber-500/10 border-amber-500/20',
  Low: 'text-white/40 bg-white/5 border-white/10',
}

function IssueCard({
  title,
  icon,
  borderColour,
  items,
}: {
  title: string
  icon: string
  borderColour: string
  items: CVReviewItem[]
}) {
  return (
    <div className={`glass p-5 border-l-2 ${borderColour}`}>
      <h3 className="text-sm font-semibold text-white/80 mb-3 flex items-center gap-2">
        <span>{icon}</span> {title}
      </h3>
      <ul className="space-y-3">
        {items.map((item, i) => (
          <li key={i}>
            <p className="text-xs font-medium text-white/70">{item.title}</p>
            <p className="text-xs text-white/40 mt-0.5">{item.detail}</p>
          </li>
        ))}
      </ul>
    </div>
  )
}

export function CvReview({ profile }: CvReviewProps) {
  const [targetRole, setTargetRole] = useState('')
  const [loading, setLoading] = useState(false)
  const [review, setReview] = useState<CVReview | null>(null)
  const [error, setError] = useState<string | null>(null)

  if (!profile) {
    return (
      <div className="glass p-8 text-center mt-6">
        <p className="text-white/40 text-sm">Upload your CV on the Profile tab first.</p>
      </div>
    )
  }

  async function handleAnalyse() {
    setLoading(true)
    setError(null)
    setReview(null)
    try {
      const result = await api.cv.review(targetRole)
      setReview(result)
    } catch {
      setError('Analysis failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-5 mt-6">
      {!review && (
        <div className="glass p-5 space-y-3">
          <label className="block text-xs text-white/30 uppercase tracking-widest">
            Target Role
          </label>
          <input
            type="text"
            value={targetRole}
            onChange={(e) => setTargetRole(e.target.value)}
            placeholder="e.g. Backend Engineer"
            className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-white/20 focus:outline-none focus:border-indigo-500/50"
          />
          <button
            onClick={handleAnalyse}
            disabled={!targetRole.trim() || loading}
            className="w-full py-2 rounded-lg text-sm font-medium bg-indigo-500 text-white hover:bg-indigo-400 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Analysing…' : 'Analyse CV'}
          </button>
          {error && <p className="text-rose-400 text-xs">{error}</p>}
        </div>
      )}

      {loading && (
        <div className="glass p-8 text-center">
          <div className="inline-block w-5 h-5 border-2 border-indigo-400/30 border-t-indigo-400 rounded-full animate-spin mb-3" />
          <p className="text-white/40 text-sm">Claude is reviewing your CV…</p>
        </div>
      )}

      {review && (
        <>
          <p className="text-sm text-white/50 italic">{review.summary}</p>

          <IssueCard
            title="Critical Issues"
            icon="🔴"
            borderColour="border-rose-500/50"
            items={review.critical_issues}
          />
          <IssueCard
            title="Structure / ATS"
            icon="🟡"
            borderColour="border-amber-500/50"
            items={review.structural_issues}
          />
          <IssueCard
            title="Polish"
            icon="🟢"
            borderColour="border-emerald-500/50"
            items={review.polish_issues}
          />

          <div className="glass p-5">
            <h3 className="text-xs text-white/30 uppercase tracking-widest mb-3">Priority Actions</h3>
            <div className="space-y-2">
              {review.priority_table.map((item) => (
                <div key={item.priority} className="flex items-start gap-3">
                  <span className="text-xs text-white/20 w-4 shrink-0 pt-0.5">{item.priority}</span>
                  <p className="text-xs text-white/60 flex-1">{item.action}</p>
                  <span className={`text-[10px] px-2 py-0.5 rounded-full border font-medium shrink-0 ${impactColour[item.impact]}`}>
                    {item.impact}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <button
            onClick={() => { setReview(null); setTargetRole('') }}
            className="w-full py-2 rounded-lg text-sm font-medium border border-white/10 text-white/50 hover:text-white hover:border-white/20 transition-colors"
          >
            Analyse Again
          </button>
        </>
      )}
    </div>
  )
}
