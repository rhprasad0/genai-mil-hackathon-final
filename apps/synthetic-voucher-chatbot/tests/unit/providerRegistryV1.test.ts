import { describe, expect, it, vi, afterEach } from 'vitest'
import { getProvider } from '../../src/providers/providerRegistry'
import type { ProviderId } from '../../src/domain/types'

const providerIds: ProviderId[] = ['stub', 'openai', 'anthropic', 'gemini', 'ollama_compatible']

describe('V1 provider registry guardrails', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('keeps the production provider ids fixed for V1', () => {
    expect(providerIds).toEqual(['stub', 'openai', 'anthropic', 'gemini', 'ollama_compatible'])
    for (const id of providerIds) {
      expect(getProvider(id).id).toBe(id)
    }
  })

  it('keeps stub deterministic without environment or network access', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => {
        throw new Error('Network disabled in deterministic unit tests')
      }),
    )
    const output = await getProvider('stub').complete({
      systemPrompt: 'Synthetic-only local demo.',
      messages: [],
      voucherState: { travelerPersona: 'Synthetic Traveler A' },
      allowedDeterminations: ['accepted', 'rejected', 'request_more_info', 'escalated'],
    })
    expect(output.assistantMessage).toContain('Synthetic helper')
    expect(globalThis.fetch).not.toHaveBeenCalled()
  })

  it.each(['openai', 'anthropic', 'gemini', 'ollama_compatible'] as const)(
    'routes %s through deterministic unavailable behavior without fetch',
    async (id) => {
      vi.stubGlobal(
        'fetch',
        vi.fn(() => {
          throw new Error('Network disabled in deterministic unit tests')
        }),
      )
      const output = await getProvider(id).complete({
        systemPrompt: 'Synthetic-only local demo.',
        messages: [],
        voucherState: {},
        allowedDeterminations: ['accepted', 'rejected', 'request_more_info', 'escalated'],
      })
      expect(output.assistantMessage).toContain('Synthetic helper')
      expect(output.safetyBoundaryOk).toBe(true)
      expect(globalThis.fetch).not.toHaveBeenCalled()
    },
  )
})
