import { test, expect } from '@playwright/test'

test('responsive card placement', async ({ page }, testInfo) => {
  await page.goto('/')
  const chat = (await page.getByTestId('chat-pane').boundingBox())!
  const db = (await page.getByTestId('mock-db-card').boundingBox())!
  const audit = (await page.getByTestId('mock-audit-card').boundingBox())!

  if (testInfo.project.name === 'desktop') {
    expect(chat.x).toBeLessThan(db.x)
    expect(chat.width).toBeGreaterThan(db.width * 1.5)
  } else {
    expect(Math.abs(chat.x - db.x)).toBeLessThanOrEqual(1)
    expect(db.y).toBeGreaterThan(chat.y)
  }

  expect(db.y).toBeLessThan(audit.y)
})
