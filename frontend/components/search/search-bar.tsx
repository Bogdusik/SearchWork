'use client'

import { useState, useRef, useEffect, KeyboardEvent } from 'react'

const UK_CITIES = [
  'Glasgow', 'Edinburgh', 'Newcastle upon Tyne', 'Leeds', 'Manchester', 'Liverpool',
  'London', 'Birmingham', 'Bristol', 'Sheffield', 'Nottingham',
  'Oxford', 'Cambridge', 'Reading', 'Cardiff', 'Belfast', 'Remote',
]

interface SearchBarProps {
  onSearch: (query: string, locations: string[]) => void
  loading: boolean
  suggestions?: string[]
  initialQuery?: string
  initialLocations?: string[]
}

export function SearchBar({
  onSearch,
  loading,
  suggestions = [],
  initialQuery = '',
  initialLocations = [],
}: SearchBarProps) {
  const [query, setQuery] = useState(initialQuery)
  const [showJobDropdown, setShowJobDropdown] = useState(false)
  const [locations, setLocations] = useState<string[]>(initialLocations)
  const [locationInput, setLocationInput] = useState('')
  const [showCityDropdown, setShowCityDropdown] = useState(false)

  const queryContainerRef = useRef<HTMLDivElement>(null)
  const cityContainerRef = useRef<HTMLDivElement>(null)

  const filteredJobs = query.length > 0
    ? suggestions.filter(s => s.toLowerCase().includes(query.toLowerCase()))
    : suggestions

  const filteredCities = UK_CITIES.filter(
    c =>
      !locations.includes(c) &&
      c.toLowerCase().includes(locationInput.toLowerCase()),
  )

  const addLocation = (city: string) => {
    const trimmed = city.trim()
    if (trimmed && !locations.includes(trimmed)) {
      setLocations(prev => [...prev, trimmed])
    }
    setLocationInput('')
    setShowCityDropdown(false)
  }

  const removeLocation = (city: string) => {
    setLocations(prev => prev.filter(l => l !== city))
  }

  const handleLocationKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if ((e.key === 'Enter' || e.key === ',') && locationInput.trim()) {
      e.preventDefault()
      addLocation(locationInput)
    }
    if (e.key === 'Backspace' && !locationInput && locations.length > 0) {
      setLocations(prev => prev.slice(0, -1))
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) {
      setShowJobDropdown(false)
      onSearch(query.trim(), locations)
    }
  }

  const selectJobSuggestion = (s: string) => {
    setQuery(s)
    setShowJobDropdown(false)
  }

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (queryContainerRef.current && !queryContainerRef.current.contains(e.target as Node))
        setShowJobDropdown(false)
      if (cityContainerRef.current && !cityContainerRef.current.contains(e.target as Node))
        setShowCityDropdown(false)
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  return (
    <form onSubmit={handleSubmit} className="mb-8 space-y-2">
      {/* Job title row */}
      <div className="flex gap-3">
        <div ref={queryContainerRef} className="relative flex-1">
          <input
            type="text"
            value={query}
            onChange={(e) => { setQuery(e.target.value); setShowJobDropdown(true) }}
            onFocus={() => setShowJobDropdown(true)}
            placeholder="Search jobs... e.g. junior developer"
            className="w-full glass min-h-[44px] px-4 py-3 text-sm text-white placeholder-white/30 outline-none focus:border-indigo-500/50 rounded-xl"
          />
          {showJobDropdown && filteredJobs.length > 0 && (
            <ul className="absolute z-50 top-full left-0 right-0 mt-1 glass rounded-xl overflow-hidden border border-white/[0.08]">
              {filteredJobs.map((s) => (
                <li
                  key={s}
                  onMouseDown={() => selectJobSuggestion(s)}
                  className="px-4 py-2.5 text-sm text-white/60 hover:text-white hover:bg-white/[0.06] cursor-pointer transition-colors"
                >
                  {s}
                </li>
              ))}
            </ul>
          )}
        </div>
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="min-h-[44px] px-5 py-3 rounded-xl text-sm font-medium bg-indigo-500/20 border border-indigo-500/40 text-indigo-300 hover:bg-indigo-500/30 disabled:opacity-40 transition-colors"
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {/* Location row */}
      <div ref={cityContainerRef} className="relative">
        <div className="glass rounded-xl px-3 py-2 flex flex-wrap items-center gap-2 min-h-[44px]">
          <span className="text-xs text-white/25 shrink-0">📍</span>
          {locations.map(city => (
            <span
              key={city}
              className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs bg-indigo-500/20 border border-indigo-500/30 text-indigo-300"
            >
              {city}
              <button
                type="button"
                onClick={() => removeLocation(city)}
                className="hover:text-white transition-colors leading-none"
              >
                ×
              </button>
            </span>
          ))}
          <input
            type="text"
            value={locationInput}
            onChange={(e) => { setLocationInput(e.target.value); setShowCityDropdown(true) }}
            onFocus={() => setShowCityDropdown(true)}
            onKeyDown={handleLocationKeyDown}
            placeholder={locations.length === 0 ? 'Add city...' : 'Add city...'}
            className="flex-1 min-w-[140px] bg-transparent text-sm text-white placeholder-white/25 outline-none"
          />
        </div>
        {showCityDropdown && filteredCities.length > 0 && (
          <ul className="absolute z-50 top-full left-0 right-0 mt-1 glass rounded-xl overflow-hidden border border-white/[0.08]">
            {filteredCities.slice(0, 8).map(city => (
              <li
                key={city}
                onMouseDown={() => addLocation(city)}
                className="px-4 py-2.5 text-sm text-white/60 hover:text-white hover:bg-white/[0.06] cursor-pointer transition-colors"
              >
                {city}
              </li>
            ))}
          </ul>
        )}
      </div>
    </form>
  )
}
