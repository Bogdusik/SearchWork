'use client'

import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import type { CVProfile } from '@/types'
import { UploadZone } from '@/components/cv/upload-zone'
import { SkillsDisplay } from '@/components/cv/skills-display'

export default function CVPage() {
  const [profile, setProfile] = useState<CVProfile | null>(null)

  useEffect(() => {
    api.cv.get().then((p) => setProfile(p)).catch(() => null)
  }, [])

  return (
    <div className="max-w-xl">
      <p className="text-xs text-white/30 uppercase tracking-widest mb-1">CV Profile</p>
      <h1 className="text-3xl font-bold bg-gradient-to-b from-white to-white/75 bg-clip-text text-transparent mb-8">
        Upload Your Resume
      </h1>
      <UploadZone onUpload={setProfile} />
      {profile && <SkillsDisplay profile={profile} />}
    </div>
  )
}
