import { test, expect } from '@playwright/test'
import { mockApi } from './helpers'

const MIN_TOUCH = 44

test.describe('applications page touch targets', () => {
  test.beforeEach(async ({ page }) => {
    await mockApi(page)
    await page.goto('/applications')
    await page.waitForLoadState('networkidle')
    await page.waitForSelector('text=Junior Software Developer')
  })

  test('status tab buttons meet 44px minimum', async ({ page }) => {
    const tabs = page.locator('button:has-text("All"), button:has-text("Saved"), button:has-text("Applied")')
    for (const tab of await tabs.all()) {
      const box = await tab.boundingBox()
      expect(box).not.toBeNull()
      expect(box!.height).toBeGreaterThanOrEqual(MIN_TOUCH)
    }
  })

  test('CL button in application row meets 44px minimum', async ({ page }) => {
    const clButton = page.getByRole('button', { name: 'CL' }).first()
    const box = await clButton.boundingBox()
    expect(box).not.toBeNull()
    expect(box!.height).toBeGreaterThanOrEqual(MIN_TOUCH)
  })

  test('status select in application row meets 44px minimum', async ({ page }) => {
    const select = page.locator('select').first()
    const box = await select.boundingBox()
    expect(box).not.toBeNull()
    expect(box!.height).toBeGreaterThanOrEqual(MIN_TOUCH)
  })

  test('application row controls appear below job info on mobile', async ({ page }) => {
    const jobTitle = page.locator('text=Junior Software Developer').first()
    const clButton = page.getByRole('button', { name: 'CL' }).first()

    const titleBox = await jobTitle.boundingBox()
    const clBox = await clButton.boundingBox()

    expect(titleBox).not.toBeNull()
    expect(clBox).not.toBeNull()
    expect(clBox!.y).toBeGreaterThan(titleBox!.y)
  })
})

test.describe('search page touch targets', () => {
  test.beforeEach(async ({ page }) => {
    await mockApi(page)
    await page.goto('/search')
    await page.waitForLoadState('networkidle')
  })

  test('search input meets 44px minimum', async ({ page }) => {
    const input = page.getByPlaceholder(/search jobs/i)
    const box = await input.boundingBox()
    expect(box).not.toBeNull()
    expect(box!.height).toBeGreaterThanOrEqual(MIN_TOUCH)
  })

  test('search button meets 44px minimum', async ({ page }) => {
    const button = page.getByRole('button', { name: /^search$/i })
    const box = await button.boundingBox()
    expect(box).not.toBeNull()
    expect(box!.height).toBeGreaterThanOrEqual(MIN_TOUCH)
  })

  test('location input row meets 44px minimum', async ({ page }) => {
    const locationRow = page.getByPlaceholder(/add city/i).locator('..')
    const box = await locationRow.boundingBox()
    expect(box).not.toBeNull()
    expect(box!.height).toBeGreaterThanOrEqual(MIN_TOUCH)
  })
})
