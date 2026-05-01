import { describe, expect, it } from 'vitest'
import { FIXTURES } from '../../src/domain/fixtures'
import { determineVoucher } from '../../src/domain/rules'

describe('determineVoucher', () => {
  it('matches rule order', () => {
    expect(determineVoucher({})).toMatchObject({ ruleIds: ['MISSING_REQUIRED'], missingFields: expect.arrayContaining(['travelerPersona']) })
    expect(determineVoucher({}, { boundaryViolation: true })).toMatchObject({ ruleIds: ['MISSING_REQUIRED'] })
    expect(determineVoucher({ ...FIXTURES.SYN_CLEAN_LODGING, amountSyntheticCredits: 640 }, { boundaryViolation: true, fixture: FIXTURES.SYN_AMOUNT_MISMATCH })).toMatchObject({ ruleIds: ['SAFETY_BOUNDARY'] })
    expect(determineVoucher({ ...FIXTURES.SYN_AMOUNT_MISMATCH }, { fixture: FIXTURES.SYN_AMOUNT_MISMATCH })).toMatchObject({ ruleIds: ['AMOUNT_MISMATCH'] })
    expect(determineVoucher({ ...FIXTURES.SYN_MISSING_RECEIPT }, { fixture: FIXTURES.SYN_MISSING_RECEIPT })).toMatchObject({ ruleIds: ['LODGING_NEEDS_RECEIPT'] })
    expect(determineVoucher({ ...FIXTURES.SYN_AMBIGUOUS_MISC }, { fixture: FIXTURES.SYN_AMBIGUOUS_MISC })).toMatchObject({ ruleIds: ['AMBIGUOUS_NEAR_THRESHOLD'] })
    expect(determineVoucher({ ...FIXTURES.SYN_TRANSIT_SMALL }, { fixture: FIXTURES.SYN_TRANSIT_SMALL })).toMatchObject({ ruleIds: ['DEFAULT_ACCEPT'] })
  })
})
