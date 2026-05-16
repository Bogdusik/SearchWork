'use client'

import { useState, useEffect, useRef } from 'react'
import { api } from '@/lib/api'
import { searchStore } from '@/lib/search-store'
import type { JobSearchResult } from '@/types'
import { SearchBar } from '@/components/search/search-bar'
import { JobCard } from '@/components/search/job-card'
import { CoverLetterModal } from '@/components/ui/cover-letter-modal'
import { JobCardSkeleton } from '@/components/ui/skeleton'

export default function SearchPage() {
  const PAGE_SIZE = 20
  const abortRef = useRef<AbortController | null>(null)
  const [jobs, setJobs] = useState<JobSearchResult[]>(searchStore.jobs)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searched, setSearched] = useState(searchStore.searched)
  const [jobTitles, setJobTitles] = useState<string[]>([])
  const [appStatuses, setAppStatuses] = useState<Record<string, string>>({})
  const [coverLetterJob, setCoverLetterJob] = useState<JobSearchResult | null>(null)

  useEffect(() => {
    Promise.all([api.cv.get(), api.applications.list()]).then(([cv, apps]) => {
      if (cv?.job_titles?.length) setJobTitles(cv.job_titles)
      const map: Record<string, string> = {}
      apps.forEach(app => {
        map[`${app.job.external_id}:${app.job.source}`] = app.status
      })
      setAppStatuses(map)
    }).catch(() => {})
  }, [])

  const handleSearch = async (query: string, locations: string[]) => {
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    setLoading(true)
    setError(null)
    setJobs([])
    try {
      const results = await api.jobs.search(query, locations, controller.signal)
      setJobs(results)
      setPage(1)
      setSearched(true)
      searchStore.save(results, query, locations)
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') return
      setError('Search failed. Make sure your CV is uploaded first.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl">
      <p className="text-xs text-white/30 uppercase tracking-widest mb-1">Find Jobs</p>
      <h1 className="text-3xl font-bold bg-gradient-to-b from-white to-white/75 bg-clip-text text-transparent mb-8">
        Job Search
      </h1>
      <SearchBar
        onSearch={handleSearch}
        loading={loading}
        suggestions={jobTitles}
        initialQuery={searchStore.query}
        initialLocations={searchStore.locations}
      />
      {error && <p className="text-rose-400 text-sm mb-4">{error}</p>}
      {searched && !loading && jobs.length > 0 && (
        <p className="text-xs text-white/20 mb-4">
          {jobs.length} results · sorted by AI match score
        </p>
      )}
      {searched && !loading && jobs.length === 0 && !error && (
        <div className="glass p-10 text-center space-y-3 mb-4">
          <p className="text-2xl">🔍</p>
          <p className="text-white/60 text-sm font-medium">No jobs found</p>
          <p className="text-white/30 text-xs leading-relaxed">
            Try a broader title (e.g. &ldquo;developer&rdquo; instead of &ldquo;React developer&rdquo;),
            add more locations, or check that your CV is uploaded so AI scoring works.
          </p>
        </div>
      )}
      {loading ? (
        <div className="space-y-4" role="status" aria-label="Searching for jobs">
          {Array.from({ length: 5 }).map((_, i) => <JobCardSkeleton key={i} />)}
        </div>
      ) : (
        <div className="space-y-4">
          {jobs.slice(0, page * PAGE_SIZE).map((job) => (
            <JobCard
              key={`${job.external_id}:${job.source}`}
              job={job}
              initialStatus={appStatuses[`${job.external_id}:${job.source}`]}
              onCoverLetter={() => setCoverLetterJob(job)}
            />
          ))}
        </div>
      )}
      {jobs.length > page * PAGE_SIZE && (
        <button
          onClick={() => setPage(p => p + 1)}
          className="w-full mt-4 py-3 rounded-xl text-sm text-white/40 hover:text-white/70 bg-white/[0.03] border border-white/[0.07] hover:bg-white/[0.06] transition-colors"
        >
          Load more · {jobs.length - page * PAGE_SIZE} remaining
        </button>
      )}

      <CoverLetterModal
        isOpen={coverLetterJob !== null}
        onClose={() => setCoverLetterJob(null)}
        externalId={coverLetterJob?.external_id ?? ''}
        source={coverLetterJob?.source ?? ''}
        jobTitle={coverLetterJob?.title ?? ''}
        company={coverLetterJob?.company ?? ''}
        description={coverLetterJob?.description ?? ''}
      />
    </div>
  )
}
