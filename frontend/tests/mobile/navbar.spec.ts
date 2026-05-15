import { test, expect } from '@playwright/test'
import { mockApi } from './helpers'

test.beforeEach(async ({ page }) => {
  await mockApi(page)
  await page.goto('/applications')
  await page.waitForLoadState('networkidle')
})

test('desktop nav links are hidden on mobile', async ({ page }) => {
  const desktopNav = page.locator('nav .hidden.md\\:flex')
  await expect(desktopNav).toBeHidden()
})

test('hamburger button is visible and meets 44px touch target', async ({ page }) => {
  const toggle = page.getByRole('button', { name: /toggle menu/i })
  await expect(toggle).toBeVisible()

  const box = await toggle.boundingBox()
  expect(box).not.toBeNull()
  expect(box!.height).toBeGreaterThanOrEqual(44)
  expect(box!.width).toBeGreaterThanOrEqual(44)
})

test('mobile menu opens when hamburger is clicked', async ({ page }) => {
  const toggle = page.getByRole('button', { name: /toggle menu/i })

  // menu is not in the DOM until opened (conditional render)
  await expect(page.locator('a[href="/search"]').nth(0)).toBeHidden()

  await toggle.click()

  const menuLink = page.locator('div.fixed a[href="/search"]')
  await expect(menuLink).toBeVisible()
})

test('mobile menu closes and navigates when a nav link is clicked', async ({ page }) => {
  const toggle = page.getByRole('button', { name: /toggle menu/i })
  await toggle.click()

  const menuLink = page.locator('div.fixed a[href="/search"]')
  await expect(menuLink).toBeVisible()

  await menuLink.click()

  // menu should be gone after navigation
  await expect(page.locator('div.fixed a[href="/search"]')).toHaveCount(0)
})
