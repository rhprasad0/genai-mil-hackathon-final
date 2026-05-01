import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import { FIXTURES } from '../../src/domain/fixtures'
import { V1_SCENARIO_FIXTURE_IDS, derivePolicyReview } from '../../src/domain/policyReview'
import type { ProviderId, SyntheticVoucher } from '../../src/domain/types'

const providerIds: ProviderId[] = ['stub', 'openai', 'anthropic', 'gemini', 'ollama_compatible']

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

function sourceText(path: string) {
  return readFileSync(resolve(process.cwd(), path), 'utf8')
}

describe('policy review provider isolation', () => {
  it('derives identical policy review output across all provider ids', () => {
    for (const fixtureId of V1_SCENARIO_FIXTURE_IDS) {
      const voucher = voucherFor(fixtureId)
      const baseline = derivePolicyReview(fixtureId, voucher)
      for (const provider of providerIds) {
        const fakeRun = { provider, voucher }
        expect(derivePolicyReview(fixtureId, fakeRun.voucher)).toEqual(baseline)
      }
    }
  })

  it('does not import provider modules from the deterministic policy-review domain or panel', () => {
    const files = ['src/domain/policyReview.ts', 'src/components/PolicyReviewPanel.tsx']
    for (const file of files) {
      const text = sourceText(file)
      expect(text).not.toMatch(/from ['"].*providers\//)
      expect(text).not.toMatch(/src\/providers/)
    }
  })

  it('keeps policy review files free of network, model, and env dependencies', () => {
    const files = ['src/domain/policyReview.ts', 'src/components/PolicyReviewPanel.tsx']
    const forbidden = [
      'complete(',
      'fetch(',
      'XMLHttpRequest',
      'WebSocket',
      'OPENAI_API_KEY',
      'ANTHROPIC_API_KEY',
      'GEMINI_API_KEY',
      'GOOGLE_API_KEY',
      'OLLAMA_BASE_URL',
      'OLLAMA_API_KEY',
      'OLLAMA_CLOUD_API_KEY',
    ]
    for (const file of files) {
      const text = sourceText(file)
      for (const marker of forbidden) {
        expect(text).not.toContain(marker)
      }
    }
  })
})
