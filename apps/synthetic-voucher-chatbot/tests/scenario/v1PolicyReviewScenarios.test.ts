import { describe, expect, it } from 'vitest'
import { derivePolicyReview } from '../../src/domain/policyReview'
import { playFixtureTranscript } from '../../src/test/transcriptHelpers'

const v1Cases = [
  ['SYN_CLEAN_LODGING', 'accepted', 'approve'],
  ['SYN_MISSING_RECEIPT', 'request_more_info', 'request_more_info'],
  ['SYN_AMOUNT_MISMATCH', 'rejected', 'escalate'],
] as const

describe('V1 policy review scenarios', () => {
  it.each(v1Cases)('plays %s to V0 %s and V1 %s', async (fixtureId, v0Determination, v1Recommendation) => {
    const result = await playFixtureTranscript(fixtureId, { alsoConfirm: true })
    expect(result.run.determination?.value).toBe(v0Determination)
    const review = derivePolicyReview(fixtureId, result.run.voucher)
    expect(review.recommendation).toBe(v1Recommendation)
    expect(review.syntheticOnly).toBe(true)
  })

  it('does not surface the legacy amount mismatch internal word in the policy panel', async () => {
    const result = await playFixtureTranscript('SYN_AMOUNT_MISMATCH', { alsoConfirm: true })
    expect(result.run.determination?.value).toBe('rejected')
    const panel = result.screen.getByTestId('policy-review-panel')
    expect(panel).toHaveTextContent('Escalate')
    expect(panel.textContent ?? '').not.toMatch(/rejected/i)
  })

  it('keeps the policy review deterministic before and after confirmation for the same voucher fields', async () => {
    const result = await playFixtureTranscript('SYN_MISSING_RECEIPT')
    const before = derivePolicyReview('SYN_MISSING_RECEIPT', result.run.voucher)
    await result.confirm()
    const after = derivePolicyReview('SYN_MISSING_RECEIPT', result.run.voucher)
    expect(after).toEqual(before)
  })

  it('keeps scenario content synthetic-only and public-safe', async () => {
    const result = await playFixtureTranscript('SYN_CLEAN_LODGING', { alsoConfirm: true })
    const rendered = document.body.textContent ?? ''
    expect(rendered).toContain('Synthetic')
    for (const unsafe of [
      /real claimant/i,
      /real voucher/i,
      /official workflow/i,
      /production deployment/i,
      /Slack/i,
      /raw transcript/i,
      /\/home\/ryan/,
      /s[k]-/,
    ]) {
      expect(rendered).not.toMatch(unsafe)
    }
    expect(result.run.provider).toBe('stub')
  })
})
