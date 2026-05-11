'use client'

import { useState, useEffect, useRef } from 'react'
import { api } from '@/lib/api'
import type { CVProfile, CVReview, CVReviewItem, PriorityItem } from '@/types'

interface CvReviewProps {
  profile: CVProfile | null
  review: CVReview | null
  targetRole: string
  onTargetRoleChange: (v: string) => void
  onReviewChange: (r: CVReview | null) => void
}

const impactColour: Record<PriorityItem['impact'], string> = {
  Huge: 'text-rose-400 bg-rose-500/10 border-rose-500/20',
  High: 'text-indigo-300 bg-indigo-500/10 border-indigo-500/20',
  Medium: 'text-amber-300 bg-amber-500/10 border-amber-500/20',
  Low: 'text-white/40 bg-white/5 border-white/10',
}

const STEPS = [
  { label: 'Reading your CV…', pct: 15 },
  { label: 'Checking structure & ATS compatibility…', pct: 35 },
  { label: 'Identifying critical issues…', pct: 55 },
  { label: 'Generating priority actions…', pct: 75 },
  { label: 'Finalising review…', pct: 90 },
]

function AnalysisProgress({ progress, label }: { progress: number; label: string }) {
  return (
    <div className="glass p-6 space-y-4">
      <div className="flex justify-between items-center mb-1">
        <p className="text-xs text-white/50">{label}</p>
        <p className="text-xs text-indigo-400 font-medium tabular-nums">{progress}%</p>
      </div>
      <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-indigo-500 to-violet-500 rounded-full transition-all duration-700 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>
      <p className="text-center text-xs text-white/30">Claude is reviewing your CV — this takes ~15 seconds</p>
    </div>
  )
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

export function CvReview({ profile, review, targetRole, onTargetRoleChange, onReviewChange }: CvReviewProps) {
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [stepLabel, setStepLabel] = useState('')
  const [error, setError] = useState<string | null>(null)
  const timerRefs = useRef<ReturnType<typeof setTimeout>[]>([])

  useEffect(() => {
    return () => { timerRefs.current.forEach(clearTimeout) }
  }, [])

  if (!profile) {
    return (
      <div className="glass p-8 text-center mt-6">
        <p className="text-white/40 text-sm">Upload your CV on the Profile tab first.</p>
      </div>
    )
  }

  function startProgress() {
    setProgress(0)
    setStepLabel(STEPS[0].label)
    timerRefs.current = STEPS.map((step, i) =>
      setTimeout(() => { setProgress(step.pct); setStepLabel(step.label) }, i * 3000)
    )
  }

  function finishProgress() {
    timerRefs.current.forEach(clearTimeout)
    timerRefs.current = []
    setProgress(100)
  }

  async function handleAnalyse() {
    setLoading(true)
    setError(null)
    startProgress()
    try {
      const result = await api.cv.review(targetRole)
      finishProgress()
      onReviewChange(result)
      setLoading(false)
    } catch (e: unknown) {
      finishProgress()
      const msg = e instanceof Error ? e.message : 'Analysis failed. Please try again.'
      setError(msg)
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
            onChange={(e) => onTargetRoleChange(e.target.value)}
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

      {loading && <AnalysisProgress progress={progress} label={stepLabel} />}

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
            onClick={() => { onReviewChange(null); onTargetRoleChange('') }}
            className="w-full py-2 rounded-lg text-sm font-medium border border-white/10 text-white/50 hover:text-white hover:border-white/20 transition-colors"
          >
            Analyse Again
          </button>
        </>
      )}
    </div>
  )
}
