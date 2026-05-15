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

  // menu nav links should not be visible before opening
  const menuSearchLink = page.locator('div.fixed.top-14 a[href="/search"]')
  await expect(menuSearchLink).toBeHidden()

  await toggle.click()
  await expect(menuSearchLink).toBeVisible()
})

test('mobile menu closes when a nav link is clicked', async ({ page }) => {
  const toggle = page.getByRole('button', { name: /toggle menu/i })
  await toggle.click()

  const menuSearchLink = page.locator('div.fixed.top-14 a[href="/search"]')
  await expect(menuSearchLink).toBeVisible()

  await page.evaluate(() => {
    const overlay = document.querySelector('div.fixed.top-14')
    const link = overlay?.querySelector('a[href="/search"]') as HTMLElement | null
    link?.click()
  })

  await expect(page.locator('div.fixed.top-14 a[href="/search"]')).toBeHidden()
})
