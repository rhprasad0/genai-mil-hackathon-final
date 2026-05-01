import { describe, expect, it } from 'vitest'
import { FIXTURES } from '../../src/domain/fixtures'
import {
  V1_SCENARIO_FIXTURE_IDS,
  derivePolicyReview,
  mapDeterminationToReviewRecommendation,
} from '../../src/domain/policyReview'
import type { SyntheticVoucher } from '../../src/domain/types'

function voucherFor(fixtureId: (typeof V1_SCENARIO_FIXTURE_IDS)[number]): SyntheticVoucher {
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

describe('policy review domain', () => {
  it('exposes exactly the three V1 scenario fixtures', () => {
    expect(V1_SCENARIO_FIXTURE_IDS).toEqual([
      'SYN_CLEAN_LODGING',
      'SYN_MISSING_RECEIPT',
      'SYN_AMOUNT_MISMATCH',
    ])
    expect(V1_SCENARIO_FIXTURE_IDS).not.toContain('SYN_AMBIGUOUS_MISC')
    expect(V1_SCENARIO_FIXTURE_IDS).not.toContain('SYN_TRANSIT_SMALL')
  })

  it('maps legacy V0 determinations into safe V1 recommendations', () => {
    expect(mapDeterminationToReviewRecommendation('accepted')).toBe('approve')
    expect(mapDeterminationToReviewRecommendation('request_more_info')).toBe('request_more_info')
    expect(mapDeterminationToReviewRecommendation('escalated')).toBe('escalate')
    expect(mapDeterminationToReviewRecommendation('rejected')).toBe('escalate')
  })

  it('derives clean packet review deterministically without hidden packet facts', () => {
    const voucher = voucherFor('SYN_CLEAN_LODGING')
    const review = derivePolicyReview('SYN_CLEAN_LODGING', voucher)
    expect(review.recommendation).toBe('approve')
    expect(review.recommendationLabel).toBe('Approve')
    expect(review.syntheticOnly).toBe(true)
    expect(review.checks).toHaveLength(5)
    expect(review.checks.map((check) => check.status)).toEqual(['pass', 'pass', 'info', 'info', 'info'])
    expect(JSON.stringify(review)).not.toContain('fakeGapClaim')
    expect(derivePolicyReview('SYN_CLEAN_LODGING', voucher)).toEqual(review)
  })

  it('derives missing receipt review with evidence and confidence warnings', () => {
    const review = derivePolicyReview('SYN_MISSING_RECEIPT', voucherFor('SYN_MISSING_RECEIPT'))
    expect(review.recommendation).toBe('request_more_info')
    expect(review.recommendationLabel).toBe('Request more info')
    expect(review.checks.find((check) => check.id === 'evidence_support')?.status).toBe('warn')
    expect(review.checks.find((check) => check.id === 'confidence_warning')?.status).toBe('warn')
    expect(JSON.stringify(review)).toContain('fakeReceiptPresent')
    expect(JSON.stringify(review)).toContain('false')
  })

  it('derives amount mismatch review as escalation with stop boundaries', () => {
    const review = derivePolicyReview('SYN_AMOUNT_MISMATCH', voucherFor('SYN_AMOUNT_MISMATCH'))
    expect(review.recommendation).toBe('escalate')
    expect(review.recommendationLabel).toBe('Escalate')
    expect(review.summary).toContain('Mismatch found. Stop here.')
    expect(review.checks.find((check) => check.id === 'human_boundary')?.status).toBe('stop')
    expect(review.checks.find((check) => check.id === 'confidence_warning')?.status).toBe('stop')
    const serialized = JSON.stringify(review)
    expect(serialized).toContain('amountSyntheticCredits')
    expect(serialized).toContain('fakeAuthorizedAmount')
    expect(serialized).toContain('amountMatchesAuthorization')
    expect(serialized).toContain('false')
  })

  it('keeps every check traceable and visible recommendation labels away from denial language', () => {
    for (const fixtureId of V1_SCENARIO_FIXTURE_IDS) {
      const review = derivePolicyReview(fixtureId, voucherFor(fixtureId))
      for (const check of review.checks) {
        expect(check.packetRefs.length + check.policyRefs.length).toBeGreaterThan(0)
      }
      expect(review.recommendationLabel).not.toMatch(/deny|denied|rejected/i)
    }
  })

  it('does not vary when provider ids elsewhere in a fake run object vary', () => {
    const voucher = voucherFor('SYN_AMOUNT_MISMATCH')
    const baseline = derivePolicyReview('SYN_AMOUNT_MISMATCH', voucher)
    for (const provider of ['stub', 'openai', 'anthropic', 'gemini', 'ollama_compatible']) {
      const fakeRun = { provider, voucher }
      expect(fakeRun.provider).toBe(provider)
      expect(derivePolicyReview('SYN_AMOUNT_MISMATCH', fakeRun.voucher)).toEqual(baseline)
    }
  })
})
