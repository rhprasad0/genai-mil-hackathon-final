import { describe, expect, it } from 'vitest'
import { collectField } from '../../src/domain/fieldCollector'

describe('fieldCollector', () => {
  it('accepts valid values', () => {
    expect(collectField({}, 'travelerPersona', 'Synthetic Traveler A')).toEqual({ travelerPersona: 'Synthetic Traveler A' })
    expect(collectField({}, 'dateRange', '2026-05-01..2026-05-02')).toEqual({ dateRange: '2026-05-01..2026-05-02' })
    expect(collectField({}, 'category', 'TRANSIT')).toEqual({ category: 'transit' })
    expect(collectField({}, 'amountSyntheticCredits', '42')).toEqual({ amountSyntheticCredits: 42 })
    expect(collectField({}, 'fakeReceiptPresent', 'yes')).toEqual({ fakeReceiptPresent: true })
    expect(collectField({}, 'amountMatchesAuthorization', 'n')).toEqual({ amountMatchesAuthorization: false })
  })

  it('rejects invalid values deterministically', () => {
    expect(collectField({}, 'travelerPersona', 'Unknown')).toEqual({
      rejectionReason: 'Use one of the synthetic traveler personas from the fixture list.',
    })
    expect(collectField({}, 'category', 'hotel')).toEqual({
      rejectionReason: 'Category must be lodging, meal, transit, or misc.',
    })
  })
})
