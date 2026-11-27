import { test, expect, type Page, type Request } from '@playwright/test'
import { hasNoHorizontalOverflow } from './helpers'

const API = 'http://localhost:8000'

interface StoredAlerts {
  enabled: boolean
  query: string
  locations: string[]
  min_score: number
  ntfy_topic: string
  last_scan_at: string | null
}

async function setUpCvPage(page: Page, opts: { initial?: StoredAlerts | null; testStatus?: number } = {}) {
  let stored: StoredAlerts | null = opts.initial ?? null
  const puts: Request[] = []
  const testCalls: Request[] = []

  await page.context().addCookies([{ name: 'sw_authed', value: '1', url: 'http://localhost:3000' }])
  await page.route(`${API}/auth/refresh`, (route) =>
    route.fulfill({ json: { access_token: 'synthetic-token', token_type: 'bearer' } }),
  )
  await page.route(`${API}/auth/me`, (route) => route.fulfill({ json: { id: 1, email: 'tester@example.com' } }))
  await page.route(`${API}/cv`, (route) => route.fulfill({ json: null }))
  await page.route(`${API}/alerts`, async (route) => {
    if (route.request().method() === 'PUT') {
      puts.push(route.request())
      stored = { ...(route.request().postDataJSON() as Omit<StoredAlerts, 'last_scan_at'>), last_scan_at: null }
      return route.fulfill({ json: stored })
    }
    return route.fulfill({ json: stored })
  })
  await page.route(`${API}/alerts/test`, (route) => {
    testCalls.push(route.request())
    const status = opts.testStatus ?? 204
    if (status === 204) return route.fulfill({ status: 204, body: '' })
    return route.fulfill({ status, json: { detail: 'Could not reach ntfy' } })
  })

  await page.goto('/cv')
  const card = page.getByTestId('alert-settings')
  await expect(card.getByLabel('Search query')).toBeVisible()
  return { card, puts, testCalls }
}

const SAVED: StoredAlerts = {
  enabled: true,
  query: 'junior python developer',
  locations: ['Glasgow', 'Edinburgh'],
  min_score: 75,
  ntfy_topic: 'sw-synthetic-topic-123',
  last_scan_at: null,
}

test('job alerts card shows an empty form with alerts off when nothing is saved', async ({ page }) => {
  const { card } = await setUpCvPage(page)

  await expect(card.getByRole('heading', { name: 'Job alerts' })).toBeVisible()
  await expect(card.getByRole('switch', { name: 'Alerts enabled' })).not.toBeChecked()
  await expect(card.getByLabel('Search query')).toHaveValue('')
  await expect(card.getByLabel('ntfy topic')).toHaveValue('')
})

test('invalid input shows inline errors and sends no request', async ({ page }) => {
  const { card, puts } = await setUpCvPage(page)

  await card.getByLabel('ntfy topic').fill('short')
  await card.getByRole('button', { name: 'Save alerts' }).click()

  await expect(card.getByText('Enter a search query')).toBeVisible()
  await expect(card.getByText(/8-64 characters/)).toBeVisible()
  expect(puts).toHaveLength(0)
})

test('saving valid settings shows success and the values survive a reload', async ({ page }) => {
  const { card, puts } = await setUpCvPage(page)

  await card.getByRole('switch', { name: 'Alerts enabled' }).click()
  await card.getByLabel('Search query').fill('junior python developer')
  await card.getByLabel('Cities').fill('Glasgow, Edinburgh')
  await card.getByLabel('Minimum match score').fill('75')
  await card.getByLabel('ntfy topic').fill('sw-synthetic-topic-123')
  await card.getByRole('button', { name: 'Save alerts' }).click()

  await expect(card.getByText('Alerts saved')).toBeVisible()
  expect(puts).toHaveLength(1)
  expect(puts[0].postDataJSON()).toEqual({
    enabled: true,
    query: 'junior python developer',
    locations: ['Glasgow', 'Edinburgh'],
    min_score: 75,
    ntfy_topic: 'sw-synthetic-topic-123',
  })

  await page.reload()
  const reloaded = page.getByTestId('alert-settings')
  await expect(reloaded.getByLabel('Search query')).toHaveValue('junior python developer')
  await expect(reloaded.getByLabel('Cities')).toHaveValue('Glasgow, Edinburgh')
  await expect(reloaded.getByLabel('Minimum match score')).toHaveValue('75')
  await expect(reloaded.getByRole('switch', { name: 'Alerts enabled' })).toBeChecked()
})

test('send test push reports success', async ({ page }) => {
  const { card, testCalls } = await setUpCvPage(page, { initial: SAVED })

  await card.getByRole('button', { name: 'Send test push' }).click()

  await expect(card.getByText('Test push sent')).toBeVisible()
  expect(testCalls).toHaveLength(1)
})

test('send test push shows the error when ntfy is unreachable', async ({ page }) => {
  const { card } = await setUpCvPage(page, { initial: SAVED, testStatus: 502 })

  await card.getByRole('button', { name: 'Send test push' }).click()

  await expect(card.getByText('Could not reach ntfy')).toBeVisible()
})

test('send test push is disabled until settings are saved', async ({ page }) => {
  const { card } = await setUpCvPage(page)

  await expect(card.getByRole('button', { name: 'Send test push' })).toBeDisabled()
})

test('job alerts card fits the screen without horizontal overflow', async ({ page }) => {
  const { card } = await setUpCvPage(page, { initial: SAVED })

  await expect(card.getByRole('button', { name: 'Save alerts' })).toBeVisible()
  expect(await hasNoHorizontalOverflow(page)).toBe(true)
})

test('generate fills a random topic that passes validation', async ({ page }) => {
  const { card } = await setUpCvPage(page)

  await card.getByRole('button', { name: 'Generate' }).click()

  await expect(card.getByLabel('ntfy topic')).toHaveValue(/^sw-[0-9a-f]{24}$/)
})
