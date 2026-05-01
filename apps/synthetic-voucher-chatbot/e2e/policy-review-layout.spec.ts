import { test, expect } from '@playwright/test'

async function optionValues(page: import('@playwright/test').Page, testId: string) {
  return page.getByTestId(testId).locator('option').evaluateAll((options) =>
    options.map((option) => (option as HTMLOptionElement).value),
  )
}

test('policy review panel layout and scenario updates', async ({ page }, testInfo) => {
  await page.goto('/')

  const chat = page.getByTestId('chat-pane')
  const panel = page.getByTestId('policy-review-panel')
  const db = page.getByTestId('mock-db-card')
  const audit = page.getByTestId('mock-audit-card')

  await expect(page.getByRole('heading', { name: 'Policy Bonfire: DTS From Hell' })).toBeVisible()
  await expect(page.getByTestId('safety-boundary-notice')).toBeVisible()
  await expect(panel).toBeVisible()
  await expect(panel).toContainText('Approve')
  await expect(optionValues(page, 'scenario-selector')).resolves.toEqual([
    'SYN_CLEAN_LODGING',
    'SYN_MISSING_RECEIPT',
    'SYN_AMOUNT_MISMATCH',
  ])

  const chatBox = (await chat.boundingBox())!
  const panelBox = (await panel.boundingBox())!
  const dbBox = (await db.boundingBox())!
  const auditBox = (await audit.boundingBox())!

  if (testInfo.project.name === 'desktop') {
    expect(chatBox.x).toBeLessThan(panelBox.x)
    expect(panelBox.width).toBeGreaterThan(280)
    expect(panelBox.y).toBeLessThan(dbBox.y)
  } else {
    expect(Math.abs(chatBox.x - panelBox.x)).toBeLessThanOrEqual(1)
    expect(panelBox.y).toBeGreaterThan(chatBox.y)
    expect(dbBox.y).toBeGreaterThan(panelBox.y)
    expect(auditBox.y).toBeGreaterThan(dbBox.y)
    const overflow = await page.evaluate(() => ({
      body: document.body.scrollWidth > document.body.clientWidth,
      html: document.documentElement.scrollWidth > document.documentElement.clientWidth,
    }))
    expect(overflow).toEqual({ body: false, html: false })
  }

  await page.getByTestId('scenario-selector').selectOption('SYN_MISSING_RECEIPT')
  await expect(panel).toContainText('Request more info')

  await page.getByTestId('scenario-selector').selectOption('SYN_AMOUNT_MISMATCH')
  await expect(panel).toContainText('Escalate')
  await expect(panel).toContainText('Mismatch found. Stop here.')

  const beforeProviderChange = await panel.textContent()
  await page.getByTestId('provider-selector').selectOption('gemini')
  await expect(panel).toHaveText(beforeProviderChange ?? '')

  await expect(page.getByTestId('chat-input')).toBeVisible()
  await expect(page.getByTestId('send-button')).toBeVisible()
})
