import type { JobSearchResult } from '@/types'

let _jobs: JobSearchResult[] = []
let _query = ''
let _locations: string[] = []
let _searched = false

export const searchStore = {
  get jobs() { return _jobs },
  get query() { return _query },
  get locations() { return _locations },
  get searched() { return _searched },
  save(jobs: JobSearchResult[], query: string, locations: string[]) {
    _jobs = jobs
    _query = query
    _locations = locations
    _searched = true
  },
}
