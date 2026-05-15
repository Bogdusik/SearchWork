import type { Page } from '@playwright/test'

export const mockApplications = [
  {
    id: 1,
    status: 'in_progress',
    applied_at: '2024-03-01T10:00:00',
    job: {
      id: 1,
      title: 'Junior Software Developer',
      company: 'TechCorp Ltd',
      location: 'Glasgow',
      salary_min: 28000,
      salary_max: 35000,
      external_id: 'abc123',
      source: 'adzuna',
      match_score: 85,
      matched_skills: ['Python', 'FastAPI', 'React'],
      missing_skills: ['Docker'],
      description: 'A great role for a junior developer in a fast-growing team.',
      url: 'https://example.com/job/1',
    },
  },
]

export const mockCv = {
  id: 1,
  skills: ['Python', 'FastAPI', 'React', 'TypeScript'],
  job_titles: ['Junior Developer', 'Backend Developer'],
  updated_at: '2024-03-01T00:00:00',
}

export async function mockApi(page: Page) {
  await page.route('http://localhost:8000/applications', (route) => {
    route.fulfill({ json: mockApplications, status: 200 })
  })
  await page.route('http://localhost:8000/applications/*', (route) => {
    route.fulfill({ json: mockApplications[0], status: 200 })
  })
  await page.route('http://localhost:8000/cv', (route) => {
    if (route.request().method() === 'GET') {
      route.fulfill({ json: mockCv, status: 200 })
    } else {
      route.fulfill({ json: mockCv, status: 200 })
    }
  })
  await page.route('http://localhost:8000/cv/**', (route) => {
    route.fulfill({ json: { content: 'Mock cover letter content.' }, status: 200 })
  })
  await page.route('http://localhost:8000/jobs*', (route) => {
    route.fulfill({ json: [], status: 200 })
  })
}

export async function hasNoHorizontalOverflow(page: Page): Promise<boolean> {
  return page.evaluate(() => {
    return document.documentElement.scrollWidth <= document.documentElement.clientWidth
  })
}
