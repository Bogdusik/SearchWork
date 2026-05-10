'use client'

import { useState } from 'react'
import { api } from '@/lib/api'
import type { Job } from '@/types'
import { SearchBar } from '@/components/search/search-bar'
import { JobCard } from '@/components/search/job-card'

export default function SearchPage() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searched, setSearched] = useState(false)

  const handleSearch = async (query: string) => {
    setLoading(true)
    setError(null)
    setJobs([])
    try {
      const results = await api.jobs.search(query)
      setJobs(results)
      setSearched(true)
    } catch {
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
      <SearchBar onSearch={handleSearch} loading={loading} />
      {error && <p className="text-rose-400 text-sm mb-4">{error}</p>}
      {searched && !loading && (
        <p className="text-xs text-white/20 mb-4">
          {jobs.length} results · sorted by AI match score
        </p>
      )}
      <div className="space-y-4">
        {jobs.map((job) => <JobCard key={job.id} job={job} />)}
      </div>
    </div>
  )
}
