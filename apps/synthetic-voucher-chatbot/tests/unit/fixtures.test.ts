import { describe, expect, it } from 'vitest'
import { FIXTURE_IDS, FIXTURES } from '../../src/domain/fixtures'

describe('fixtures', () => {
  it('contains the required fixture ids', () => {
    expect(FIXTURE_IDS).toEqual([
      'SYN_CLEAN_LODGING',
      'SYN_MISSING_RECEIPT',
      'SYN_AMOUNT_MISMATCH',
      'SYN_AMBIGUOUS_MISC',
      'SYN_TRANSIT_SMALL',
    ])
  })

  it('avoids unsafe markers and has expectations', () => {
    const denylist = ['OPENAI_API_KEY', 'sk-', 'routing number', 'SSN', 'credit card', 'approved for payment']
    for (const fixture of Object.values(FIXTURES)) {
      const text = JSON.stringify(fixture)
      for (const marker of denylist) {
        expect(text).not.toContain(marker)
      }
      expect(fixture.expectedRuleIds.length).toBeGreaterThan(0)
      expect(fixture.transcript.length).toBe(8)
    }
  })
})
