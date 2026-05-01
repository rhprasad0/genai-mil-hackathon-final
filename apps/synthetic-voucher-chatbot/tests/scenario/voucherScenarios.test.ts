import { describe, expect, it } from 'vitest'
import { FIXTURES } from '../../src/domain/fixtures'
import { playFixtureTranscript } from '../../src/test/transcriptHelpers'

describe('voucher scenarios', () => {
  it.each([
    ['SYN_CLEAN_LODGING', 'accepted', ['DEFAULT_ACCEPT']],
    ['SYN_MISSING_RECEIPT', 'request_more_info', ['LODGING_NEEDS_RECEIPT']],
    ['SYN_AMOUNT_MISMATCH', 'rejected', ['AMOUNT_MISMATCH']],
    ['SYN_AMBIGUOUS_MISC', 'escalated', ['AMBIGUOUS_NEAR_THRESHOLD']],
    ['SYN_TRANSIT_SMALL', 'accepted', ['DEFAULT_ACCEPT']],
  ] as const)('plays %s to a deterministic determination', async (fixtureId, value, ruleIds) => {
    const result = await playFixtureTranscript(fixtureId, { alsoConfirm: true })
    expect(result.run.determination?.value).toBe(value)
    expect(result.run.determination?.ruleIds).toEqual(ruleIds)
    expect(result.run.voucher.explanation).toBe(FIXTURES[fixtureId].explanation)
    expect(
      result.run.dbEvents.some((event) =>
        JSON.stringify(event.statePatch ?? {}).includes(FIXTURES[fixtureId].explanation),
      ),
    ).toBe(true)
    expect(result.run.auditEvents.at(-1)?.name).toBe('voucher.determination_rendered')
  })
})
