import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { VoucherChatApp } from '../../src/app/VoucherChatApp'
import { SAFETY_BOUNDARY_NOTICE } from '../../src/domain/constants'

describe('VoucherChatApp', () => {
  it('shows the safety notice, Policy Bonfire title, provider defaults, and V1 panel', async () => {
    render(<VoucherChatApp />)
    expect(screen.getByRole('heading', { name: 'Policy Bonfire: DTS From Hell' })).toBeInTheDocument()
    expect(screen.getByTestId('safety-boundary-notice')).toHaveTextContent(SAFETY_BOUNDARY_NOTICE)
    expect(screen.getByTestId('provider-selector')).toHaveValue('stub')
    expect(screen.getByTestId('policy-review-panel')).toHaveTextContent('Approve')
  })

  it('keeps disallowed phrases out of the rendered app shell', () => {
    render(<VoucherChatApp />)
    const text = document.body.textContent ?? ''
    for (const marker of [
      'approved for payment',
      'official DTS',
      'real reimbursement',
      'entitlement determination',
      'payability determination',
      'fraud determination',
      'audit certification',
    ]) {
      expect(text).not.toContain(marker)
    }
  })

  it('scenario selector exposes exactly the three V1 scenarios and provider changes do not rewrite the panel', async () => {
    const user = userEvent.setup()
    render(<VoucherChatApp />)
    const scenarioSelector = screen.getByTestId('scenario-selector')
    expect(Array.from(scenarioSelector.querySelectorAll('option')).map((option) => option.value)).toEqual([
      'SYN_CLEAN_LODGING',
      'SYN_MISSING_RECEIPT',
      'SYN_AMOUNT_MISMATCH',
    ])

    await user.selectOptions(scenarioSelector, 'SYN_AMOUNT_MISMATCH')
    const before = screen.getByTestId('policy-review-panel').textContent
    await user.selectOptions(screen.getByTestId('provider-selector'), 'anthropic')
    expect(screen.getByTestId('policy-review-panel').textContent).toBe(before)
  })

  it('is keyboard reachable', async () => {
    const user = userEvent.setup()
    render(<VoucherChatApp />)
    await user.tab()
    await user.tab()
    await user.tab()
    expect(screen.getByTestId('chat-input')).toHaveFocus()
  })
})
