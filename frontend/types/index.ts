export interface CVProfile {
  id: number
  skills: string[]
  job_titles: string[]
  keywords: string[]
  updated_at: string
}

export interface Job {
  id: number
  external_id: string
  source: 'adzuna' | 'reed'
  title: string
  company: string
  location: string
  salary_min: number | null
  salary_max: number | null
  url: string
  description: string
  match_score: number
  created_at: string
}

export interface Application {
  id: number
  job: Job
  status: 'saved' | 'applied' | 'interview' | 'offer' | 'rejected'
  applied_at: string | null
  notes: string | null
  updated_at: string
}

export type ApplicationStatus = Application['status']
