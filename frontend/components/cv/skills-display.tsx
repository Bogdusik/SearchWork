import type { CVProfile } from '@/types'

interface SkillsDisplayProps {
  profile: CVProfile
}

export function SkillsDisplay({ profile }: SkillsDisplayProps) {
  return (
    <div className="space-y-6 mt-6">
      <div>
        <h3 className="text-xs text-white/30 uppercase tracking-widest mb-3">Extracted Skills</h3>
        <div className="flex flex-wrap gap-2">
          {profile.skills.map((skill) => (
            <span key={skill} className="px-3 py-1 rounded-full text-xs bg-indigo-500/15 border border-indigo-500/30 text-indigo-300">
              {skill}
            </span>
          ))}
        </div>
      </div>
      <div>
        <h3 className="text-xs text-white/30 uppercase tracking-widest mb-3">Target Roles</h3>
        <div className="flex flex-wrap gap-2">
          {profile.job_titles.map((title) => (
            <span key={title} className="px-3 py-1 rounded-full text-xs bg-white/5 border border-white/10 text-white/60">
              {title}
            </span>
          ))}
        </div>
      </div>
      <p className="text-xs text-white/20">
        {(() => {
          const d = new Date(profile.updated_at)
          return isNaN(d.getTime()) ? null : `Last updated: ${d.toLocaleDateString('en-GB')}`
        })()}
      </p>
    </div>
  )
}
