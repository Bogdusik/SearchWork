'use client'

import { useState } from 'react'

interface SearchBarProps {
  onSearch: (query: string) => void
  loading: boolean
}

export function SearchBar({ onSearch, loading }: SearchBarProps) {
  const [query, setQuery] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) onSearch(query.trim())
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-3 mb-8">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search jobs... e.g. junior developer"
        className="flex-1 glass px-4 py-3 text-sm text-white placeholder-white/30 outline-none focus:border-indigo-500/50 rounded-xl"
      />
      <button
        type="submit"
        disabled={loading || !query.trim()}
        className="px-5 py-3 rounded-xl text-sm font-medium bg-indigo-500/20 border border-indigo-500/40 text-indigo-300 hover:bg-indigo-500/30 disabled:opacity-40 transition-colors"
      >
        {loading ? 'Searching...' : 'Search'}
      </button>
    </form>
  )
}
