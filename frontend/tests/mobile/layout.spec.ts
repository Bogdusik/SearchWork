import { test, expect } from '@playwright/test'
import { mockApi, hasNoHorizontalOverflow } from './helpers'

const pages = ['/applications', '/search', '/cv']

for (const path of pages) {
  test(`no horizontal overflow on ${path}`, async ({ page }) => {
    await mockApi(page)
    await page.goto(path)
    await page.waitForLoadState('networkidle')
    expect(await hasNoHorizontalOverflow(page)).toBe(true)
  })
}

test('applications page renders content without overflow', async ({ page }) => {
  await mockApi(page)
  await page.goto('/applications')
  await page.waitForLoadState('networkidle')

  await expect(page.getByText('My Applications')).toBeVisible()
  await expect(page.getByText('Junior Software Developer').first()).toBeVisible()
  expect(await hasNoHorizontalOverflow(page)).toBe(true)
})

test('search page renders search bar without overflow', async ({ page }) => {
  await mockApi(page)
  await page.goto('/search')
  await page.waitForLoadState('networkidle')

  await expect(page.getByPlaceholder(/search jobs/i)).toBeVisible()
  expect(await hasNoHorizontalOverflow(page)).toBe(true)
})

test('cv page renders tabs without overflow', async ({ page }) => {
  await mockApi(page)
  await page.goto('/cv')
  await page.waitForLoadState('networkidle')

  await expect(page.getByText('Your Resume')).toBeVisible()
  expect(await hasNoHorizontalOverflow(page)).toBe(true)
})
