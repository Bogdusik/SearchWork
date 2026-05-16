'use client'

import { useEffect, useRef, useState } from 'react'
import { api } from '@/lib/api'

interface CoverLetterPanelProps {
  isOpen: boolean
  onClose: () => void
  externalId: string
  source: string
  jobTitle: string
  company: string
  description: string
}

export function CoverLetterModal({ isOpen, onClose, externalId, source, jobTitle, company, description }: CoverLetterPanelProps) {
  const [letter, setLetter] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const loadedFor = useRef<string | null>(null)
  const closeButtonRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (isOpen) closeButtonRef.current?.focus()
  }, [isOpen])

  useEffect(() => {
    if (!isOpen) return
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  const load = async (forceRegenerate = false) => {
    setLoading(true)
    setError(null)
    if (forceRegenerate) setLetter(null)
    try {
      const text = await api.cv.generateCoverLetter(externalId, source, jobTitle, company, description, forceRegenerate)
      setLetter(text)
      loadedFor.current = externalId
    } catch {
      setError('Failed to generate cover letter. Make sure your CV is uploaded.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!isOpen) return
    if (loadedFor.current === externalId && letter) return
    load()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, externalId])

  const copy = async () => {
    if (!letter) return
    await navigator.clipboard.writeText(letter)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <>
      <div
        className={`fixed inset-0 bg-black/40 z-40 transition-opacity duration-300 ${isOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}`}
        onClick={onClose}
      />

      <div
        className={`fixed top-0 right-0 h-full w-full sm:w-[480px] z-50 flex flex-col transition-transform duration-300 ease-in-out ${isOpen ? 'translate-x-0' : 'translate-x-full'}`}
        style={{ paddingTop: 'env(safe-area-inset-top)', paddingBottom: 'env(safe-area-inset-bottom)' }}
      >
        <div className="flex flex-col h-full backdrop-blur-xl bg-white/[0.04] border-l border-white/[0.08] shadow-2xl">

          <div className="flex items-start justify-between gap-4 px-4 sm:px-6 pt-4 sm:pt-6 pb-4 border-b border-white/[0.06] shrink-0">
            <div>
              <p className="text-xs text-white/30 uppercase tracking-widest mb-1">Cover Letter</p>
              <h2 className="text-sm font-semibold text-white/90 leading-snug">{jobTitle}</h2>
              <p className="text-xs text-white/40 mt-0.5">{company}</p>
            </div>
            <button
              ref={closeButtonRef}
              onClick={onClose}
              aria-label="Close"
              className="min-h-[44px] min-w-[44px] flex items-center justify-center text-white/30 hover:text-white/60 transition-colors text-lg shrink-0"
            >
              ✕
            </button>
          </div>

          <div className="flex-1 overflow-y-auto px-6 py-4 flex flex-col min-h-0">
            {loading && (
              <div className="flex-1 flex flex-col items-center justify-center gap-3 py-16">
                <div className="w-8 h-8 border-2 border-indigo-400/30 border-t-indigo-400 rounded-full animate-spin" />
                <p className="text-xs text-white/30">Generating cover letter…</p>
              </div>
            )}

            {error && !loading && (
              <div className="flex-1 flex flex-col items-center justify-center gap-3 py-16">
                <p className="text-rose-400 text-sm text-center">{error}</p>
                <button
                  onClick={() => load()}
                  className="px-4 py-1.5 rounded-lg text-xs bg-white/5 border border-white/10 text-white/50 hover:text-white/70 transition-colors"
                >
                  Retry
                </button>
              </div>
            )}

            {letter && !loading && (
              <textarea
                readOnly
                value={letter}
                className="flex-1 min-h-full w-full bg-white/[0.03] border border-white/[0.08] rounded-lg p-4 text-xs text-white/70 leading-relaxed resize-none outline-none"
              />
            )}
          </div>

          {letter && !loading && (
            <div className="flex gap-2 px-6 pb-6 pt-3 border-t border-white/[0.06] shrink-0">
              <button
                onClick={copy}
                className="px-4 py-1.5 rounded-lg text-xs bg-indigo-500/20 border border-indigo-500/40 text-indigo-300 hover:bg-indigo-500/30 transition-colors"
              >
                {copied ? 'Copied!' : 'Copy to Clipboard'}
              </button>
              <button
                onClick={() => load(true)}
                className="px-4 py-1.5 rounded-lg text-xs bg-white/5 border border-white/10 text-white/40 hover:text-white/60 transition-colors"
              >
                Regenerate
              </button>
            </div>
          )}
        </div>
      </div>
    </>
  )
}
