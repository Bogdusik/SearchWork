'use client'

import { useState, useCallback } from 'react'
import { api } from '@/lib/api'
import type { CVProfile } from '@/types'

interface UploadZoneProps {
  onUpload: (profile: CVProfile) => void
}

export function UploadZone({ onUpload }: UploadZoneProps) {
  const [dragging, setDragging] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleFile = useCallback(async (file: File) => {
    if (!file.name.endsWith('.pdf')) {
      setError('Please upload a PDF file')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const profile = await api.cv.upload(file)
      onUpload(profile)
    } catch {
      setError('Failed to process CV. Please try a different PDF.')
    } finally {
      setLoading(false)
    }
  }, [onUpload])

  return (
    <div
      className={`glass p-8 text-center cursor-pointer transition-colors ${dragging ? 'border-indigo-500/50' : ''}`}
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault()
        setDragging(false)
        const f = e.dataTransfer.files[0]
        if (f) handleFile(f)
      }}
      onClick={() => document.getElementById('cv-file-input')?.click()}
    >
      <input
        id="cv-file-input"
        type="file"
        accept=".pdf"
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0]
          if (f) handleFile(f)
        }}
      />
      <div className="text-4xl mb-3">📄</div>
      {loading ? (
        <div className="text-white/50 text-sm">Analysing your CV with AI...</div>
      ) : (
        <>
          <div className="text-white/60 text-sm">Drop your PDF here</div>
          <div className="text-indigo-400 text-xs mt-1">or click to browse</div>
        </>
      )}
      {error && <div className="text-rose-400 text-xs mt-3">{error}</div>}
    </div>
  )
}
