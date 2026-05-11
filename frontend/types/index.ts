export interface CVProfile {
  id: number
  skills: string[]
  job_titles: string[]
  keywords: string[]
  updated_at: string
}

/** Live search result from internet — not saved to DB. */
export interface JobSearchResult {
  external_id: string
  source: 'adzuna' | 'reed' | 'indeed' | 'gradcracker' | 'jsearch' | 'arbeitnow' | 'remotive' | 'totaljobs'
  title: string
  company: string
  location: string
  salary_min: number | null
  salary_max: number | null
  url: string
  description: string
  match_score: number
}

/** Job saved to DB — exists inside Application. */
export interface Job extends JobSearchResult {
  id: number
  created_at: string
}

export interface Application {
  id: number
  job: Job
  status: 'saved' | 'in_progress' | 'applied' | 'interview' | 'offer' | 'rejected'
  applied_at: string | null
  notes: string | null
  updated_at: string
}

export type ApplicationStatus = Application['status']

export interface CVReviewItem {
  title: string
  detail: string
}

export interface PriorityItem {
  priority: number
  action: string
  impact: 'Huge' | 'High' | 'Medium' | 'Low'
}

export interface CVReview {
  summary: string
  critical_issues: CVReviewItem[]
  structural_issues: CVReviewItem[]
  polish_issues: CVReviewItem[]
  priority_table: PriorityItem[]
}
