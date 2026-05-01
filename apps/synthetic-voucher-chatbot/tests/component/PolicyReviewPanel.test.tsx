import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { PolicyReviewPanel } from '../../src/components/PolicyReviewPanel'
import { FIXTURES } from '../../src/domain/fixtures'
import { derivePolicyReview } from '../../src/domain/policyReview'
import type { SyntheticVoucher } from '../../src/domain/types'

function voucherFor(fixtureId: 'SYN_CLEAN_LODGING' | 'SYN_MISSING_RECEIPT' | 'SYN_AMOUNT_MISMATCH'): SyntheticVoucher {
  const fixture = FIXTURES[fixtureId]
  return {
    travelerPersona: fixture.travelerPersona,
    tripPurpose: fixture.tripPurpose,
    dateRange: fixture.dateRange,
    category: fixture.category,
    amountSyntheticCredits: fixture.amountSyntheticCredits,
    fakeReceiptPresent: fixture.fakeReceiptPresent,
    amountMatchesAuthorization: fixture.amountMatchesAuthorization,
    explanation: fixture.explanation,
  }
}

describe('PolicyReviewPanel', () => {
  it('renders the clean packet recommendation and narrow synthetic copy', () => {
    render(<PolicyReviewPanel review={derivePolicyReview('SYN_CLEAN_LODGING', voucherFor('SYN_CLEAN_LODGING'))} />)
    const panel = screen.getByTestId('policy-review-panel')
    expect(panel).toHaveAccessibleName('Policy review panel')
    expect(within(panel).getByText('Approve')).toBeInTheDocument()
    expect(panel).toHaveTextContent('narrow synthetic recommendation')
  })

  it('renders missing receipt as request more info with packet refs', () => {
    render(<PolicyReviewPanel review={derivePolicyReview('SYN_MISSING_RECEIPT', voucherFor('SYN_MISSING_RECEIPT'))} />)
    const panel = screen.getByTestId('policy-review-panel')
    expect(within(panel).getByText('Request more info')).toBeInTheDocument()
    expect(panel).toHaveTextContent('fakeReceiptPresent=false')
  })

  it('renders amount mismatch as escalation without unsafe visible terms', () => {
    render(<PolicyReviewPanel review={derivePolicyReview('SYN_AMOUNT_MISMATCH', voucherFor('SYN_AMOUNT_MISMATCH'))} />)
    const panel = screen.getByTestId('policy-review-panel')
    expect(within(panel).getByText('Escalate')).toBeInTheDocument()
    expect(panel).toHaveTextContent('Mismatch found. Stop here.')
    expect(panel.textContent ?? '').not.toMatch(/fraud|denied|\bdeny\b|rejected|payment|entitlement|official action/i)
  })

  it('renders the five checks in stable order with refs and educational policy notes', () => {
    render(<PolicyReviewPanel review={derivePolicyReview('SYN_AMOUNT_MISMATCH', voucherFor('SYN_AMOUNT_MISMATCH'))} />)
    const checkTitles = screen.getAllByTestId('policy-review-check-title').map((node) => node.textContent)
    expect(checkTitles).toEqual([
      'Evidence support',
      'Traceability',
      'Confidence warning',
      'Human boundary',
      'Policy notes',
    ])
    const panel = screen.getByTestId('policy-review-panel')
    expect(panel).toHaveTextContent('amountSyntheticCredits=640')
    expect(panel).toHaveTextContent('fakeAuthorizedAmount=500')
    expect(panel).toHaveTextContent('Testable behavior')
    expect(panel).not.toHaveTextContent(/compliance score|formal citation/i)
  })
})
