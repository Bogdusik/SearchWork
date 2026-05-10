'use client'

import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import type { CVProfile } from '@/types'
import { UploadZone } from '@/components/cv/upload-zone'
import { SkillsDisplay } from '@/components/cv/skills-display'

export default function CVPage() {
  const [profile, setProfile] = useState<CVProfile | null>(null)
  const [fetchError, setFetchError] = useState(false)

  useEffect(() => {
    api.cv.get()
      .then((p) => setProfile(p))
      .catch(() => setFetchError(true))
  }, [])

  return (
    <div className="max-w-xl">
      <p className="text-xs text-white/30 uppercase tracking-widest mb-1">CV Profile</p>
      <h1 className="text-3xl font-bold bg-gradient-to-b from-white to-white/75 bg-clip-text text-transparent mb-8">
        Upload Your Resume
      </h1>
      {fetchError && (
        <p className="text-rose-400 text-xs mb-4">Could not load CV profile. You can still upload a new one.</p>
      )}
      <UploadZone onUpload={(p) => { setProfile(p); setFetchError(false) }} />
      {profile && <SkillsDisplay profile={profile} />}
    </div>
  )
}
