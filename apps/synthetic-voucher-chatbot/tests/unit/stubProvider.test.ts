import { describe, expect, it } from 'vitest'
import { stubProvider } from '../../src/providers/stubProvider'
import type { ProviderOutput } from '../../src/providers/types'

describe('stubProvider', () => {
  it('is deterministic', async () => {
    const input = {
      systemPrompt: 'Synthetic-only local demo.',
      messages: [],
      voucherState: {},
      allowedDeterminations: ['accepted', 'rejected', 'request_more_info', 'escalated'] as const,
    }
    const first = await stubProvider.complete(input)
    const second = await stubProvider.complete(input)
    expect(first).toEqual(second)
  })

  it('does not expose determination on ProviderOutput', () => {
    const output: ProviderOutput = { assistantMessage: 'ok', safetyBoundaryOk: true }
    // @ts-expect-error determination is intentionally not part of ProviderOutput
    const determination = output.determination
    expect(determination).toBeUndefined()
    expect(output.assistantMessage).toBe('ok')
  })
})
