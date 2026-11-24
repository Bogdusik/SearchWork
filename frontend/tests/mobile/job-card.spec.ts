import { test, expect, type Page, type Route } from '@playwright/test'

const API = 'http://localhost:8000'

function makeJob(id: string, title: string, matchScore: number) {
  return {
    external_id: id,
    source: 'adzuna',
    title,
    company: 'Example Ltd',
    location: 'Glasgow',
    salary_min: null,
    salary_max: null,
    url: '',
    description: 'Synthetic job description.',
    match_score: matchScore,
    matched_skills: [],
    missing_skills: [],
  }
}

const appliedJob = makeJob('abc123', 'Applied Backend Role', 95)
const idleJob = makeJob('def456', 'Idle Frontend Role', 90)
const fillerJobs = Array.from({ length: 22 }, (_, i) =>
  makeJob(`filler${i}`, `Filler Role ${i}`, i < 3 ? 0 : 80 - i),
)
const searchResults = [appliedJob, idleJob, ...fillerJobs]

const existingApplication = {
  id: 1,
  status: 'in_progress',
  applied_at: null,
  notes: null,
  updated_at: '2026-01-01T00:00:00',
  job: { ...appliedJob, id: 1, created_at: '2026-01-01T00:00:00' },
}

function deferred() {
  let release!: () => void
  const promise = new Promise<void>((resolve) => { release = resolve })
  return { promise, release }
}

async function setUpLoggedInSearch(
  page: Page,
  opts: { applicationsGate?: Promise<void>; createStatus?: number } = {},
) {
  await page.context().addCookies([{ name: 'sw_authed', value: '1', url: 'http://localhost:3000' }])
  await page.route(`${API}/auth/refresh`, (route) =>
    route.fulfill({ json: { access_token: 'synthetic-token', token_type: 'bearer' } }),
  )
  await page.route(`${API}/auth/me`, (route) =>
    route.fulfill({ json: { id: 1, email: 'tester@example.com' } }),
  )
  await page.route(`${API}/cv`, (route) => route.fulfill({ json: null }))
  await page.route(`${API}/jobs*`, (route) => route.fulfill({ json: searchResults }))
  await page.route(`${API}/applications`, async (route: Route) => {
    if (route.request().method() === 'POST') {
      const status = opts.createStatus ?? 201
      if (status >= 400) return route.fulfill({ status, body: 'synthetic failure' })
      return route.fulfill({ status, json: { ...existingApplication, id: 2, status: 'saved' } })
    }
    if (opts.applicationsGate) await opts.applicationsGate
    return route.fulfill({ json: [existingApplication] })
  })

  await page.goto('/search')
  await page.getByPlaceholder(/search jobs/i).fill('developer')
  await page.getByPlaceholder(/search jobs/i).press('Enter')
  await expect(card(page, idleJob.title)).toBeVisible()
}

function card(page: Page, title: string) {
  return page.locator('div.glass.p-5').filter({ hasText: title })
}

test('card shows the existing application status when /applications responds after results render', async ({ page }) => {
  const gate = deferred()
  await setUpLoggedInSearch(page, { applicationsGate: gate.promise })

  const applied = card(page, appliedJob.title)
  await expect(applied.getByRole('button', { name: 'Save' })).toBeVisible()
  await expect(applied.getByText('In Progress', { exact: true })).toHaveCount(0)

  gate.release()

  await expect(applied.getByText('In Progress', { exact: true })).toBeVisible()
  await expect(applied.getByRole('button', { name: 'Save' })).toHaveCount(0)
})

test('card without an application shows Save and Apply and no status label', async ({ page }) => {
  await setUpLoggedInSearch(page)

  const idle = card(page, idleJob.title)
  await expect(card(page, appliedJob.title).getByText('In Progress', { exact: true })).toBeVisible()
  await expect(idle.getByRole('button', { name: 'Save' })).toBeVisible()
  await expect(idle.getByRole('button', { name: 'Apply Now' })).toBeVisible()
  for (const label of ['Saved', 'In Progress', 'Applied', 'Interview', 'Offer', 'Rejected']) {
    await expect(idle.getByText(label, { exact: true })).toHaveCount(0)
  }
})

test('Saved label survives re-renders of the results list', async ({ page }) => {
  await setUpLoggedInSearch(page)

  const idle = card(page, idleJob.title)
  await idle.getByRole('button', { name: 'Save' }).click()
  await expect(idle.getByText('Saved', { exact: true })).toBeVisible()

  await page.getByRole('button', { name: /load more/i }).click()
  await expect(card(page, 'Filler Role 21')).toBeVisible()
  await expect(idle.getByText('Saved', { exact: true })).toBeVisible()

  const hideZeroToggle = page.getByText(/hide 0% matches/i).locator('xpath=preceding-sibling::div')
  await hideZeroToggle.click()
  await expect(card(page, 'Filler Role 0')).toBeVisible()
  await expect(idle.getByText('Saved', { exact: true })).toBeVisible()

  await hideZeroToggle.click()
  await expect(card(page, 'Filler Role 0')).toHaveCount(0)
  await expect(idle.getByText('Saved', { exact: true })).toBeVisible()
  await expect(idle.getByRole('button', { name: 'Save' })).toHaveCount(0)
})

test('failed Save shows the error and keeps the previous status', async ({ page }) => {
  await setUpLoggedInSearch(page, { createStatus: 500 })

  const idle = card(page, idleJob.title)
  await idle.getByRole('button', { name: 'Save' }).click()

  await expect(idle.getByText('Could not save job. Please try again.')).toBeVisible()
  await expect(idle.getByRole('button', { name: 'Save' })).toBeVisible()
  await expect(idle.getByText('Saved', { exact: true })).toHaveCount(0)
})
