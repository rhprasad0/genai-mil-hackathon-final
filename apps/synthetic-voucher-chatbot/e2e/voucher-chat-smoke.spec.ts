import { test, expect } from '@playwright/test'

test('smoke flow', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByTestId('chat-pane')).toBeVisible()
})
