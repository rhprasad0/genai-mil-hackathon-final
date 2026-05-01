import { describe, expect, it, beforeEach } from 'vitest'
import { FIXTURES } from '../../src/domain/fixtures'
import { createFlakeyTestProvider } from '../../src/test/flakeyTestProvider'
import { registerProvider, resetProviderRegistry } from '../../src/providers/providerRegistry'
import { playFixtureTranscript } from '../../src/test/transcriptHelpers'
import { SAFETY_FALLBACK_MESSAGE } from '../../src/domain/constants'

describe('provider failure scenarios', () => {
  beforeEach(() => {
    resetProviderRegistry()
  })

  it('falls back after provider timeout', async () => {
    registerProvider(createFlakeyTestProvider('timeout'))
    const result = await playFixtureTranscript(FIXTURES.SYN_CLEAN_LODGING.id, {
      providerId: 'test_flakey',
    })
    expect(result.run.auditEvents.filter((event) => event.name === 'provider.fallback_to_stub')).toHaveLength(8)
  })

  it('repairs unsafe provider text', async () => {
    registerProvider(createFlakeyTestProvider('boundary'))
    const result = await playFixtureTranscript(FIXTURES.SYN_CLEAN_LODGING.id, {
      providerId: 'test_flakey',
    })
    expect(result.screen.getAllByText(SAFETY_FALLBACK_MESSAGE).length).toBeGreaterThan(0)
  })
})
