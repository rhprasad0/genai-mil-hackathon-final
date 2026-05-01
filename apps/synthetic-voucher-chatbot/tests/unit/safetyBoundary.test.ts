import { describe, expect, it } from 'vitest'
import { classifySafetyBoundary } from '../../src/domain/safetyBoundary'

describe('classifySafetyBoundary', () => {
  it('accepts safe synthetic text', () => {
    expect(classifySafetyBoundary('Synthetic local-only guidance for the demo.')).toBe(true)
  })

  it('rejects disallowed phrases', () => {
    // SAFETY-TEST-FIXTURE: deliberate boundary phrase
    expect(classifySafetyBoundary('This looks like real DTS workflow text.')).toBe(false)
    // SAFETY-TEST-FIXTURE: deliberate boundary phrase
    expect(classifySafetyBoundary('Approved for payment by the official action path.')).toBe(false)
  })
})
