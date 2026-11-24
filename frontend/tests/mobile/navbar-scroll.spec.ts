import { test, expect, type Page } from '@playwright/test'

const API = 'http://localhost:8000'
const SCROLLED_CLASS = /bg-black\/50/

async function setUpLoggedIn(page: Page, refreshGate?: Promise<void>) {
  await page.context().addCookies([{ name: 'sw_authed', value: '1', url: 'http://localhost:3000' }])
  await page.addInitScript(() => {
    const tallPage = new CSSStyleSheet()
    tallPage.replaceSync('html { min-height: 3000px; }')
    document.adoptedStyleSheets = [...document.adoptedStyleSheets, tallPage]
  })
  await page.route(`${API}/**`, (route) => route.fulfill({ json: [] }))
  await page.route(`${API}/auth/refresh`, async (route) => {
    if (refreshGate) await refreshGate
    return route.fulfill({ json: { access_token: 'synthetic-token', token_type: 'bearer' } })
  })
  await page.route(`${API}/auth/me`, (route) =>
    route.fulfill({ json: { id: 1, email: 'tester@example.com' } }),
  )
}

const header = (page: Page) => page.locator('header')

test('navbar is unscrolled when the page loads at the top', async ({ page }) => {
  await setUpLoggedIn(page)
  await page.goto('/applications')

  await expect(header(page)).toBeVisible()
  await expect(header(page)).not.toHaveClass(SCROLLED_CLASS)
})

test('navbar switches to scrolled style only above 10px', async ({ page }) => {
  await setUpLoggedIn(page)
  await page.goto('/applications')
  await expect(header(page)).toBeVisible()

  await page.evaluate(() => window.scrollTo(0, 10))
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBe(10)
  await expect(header(page)).not.toHaveClass(SCROLLED_CLASS)

  await page.evaluate(() => window.scrollTo(0, 11))
  await expect(header(page)).toHaveClass(SCROLLED_CLASS)

  await page.evaluate(() => window.scrollTo(0, 10))
  await expect(header(page)).not.toHaveClass(SCROLLED_CLASS)

  await page.evaluate(() => window.scrollTo(0, 11))
  await expect(header(page)).toHaveClass(SCROLLED_CLASS)

  await page.evaluate(() => window.scrollTo(0, 0))
  await expect(header(page)).not.toHaveClass(SCROLLED_CLASS)
})

test('navbar is scrolled on mount when the page is already scrolled, without any scroll event', async ({ page }) => {
  let releaseRefresh!: () => void
  const refreshGate = new Promise<void>((resolve) => { releaseRefresh = resolve })
  await setUpLoggedIn(page, refreshGate)
  await page.addInitScript(() => {
    window.addEventListener('scroll', (e) => e.stopImmediatePropagation(), true)
  })

  await page.goto('/applications')
  await expect(header(page)).toHaveCount(0)
  await page.evaluate(() => window.scrollTo(0, 200))
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBe(200)

  releaseRefresh()

  await expect(header(page)).toBeVisible()
  await expect(header(page)).toHaveClass(SCROLLED_CLASS)
})
