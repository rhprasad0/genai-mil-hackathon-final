import type { ChatProvider } from '../providers/types'

export type FlakeyMode = 'timeout' | 'schema' | 'boundary' | 'invalid_fields'

export function createFlakeyTestProvider(mode: FlakeyMode): ChatProvider {
  return {
    id: 'test_flakey',
    label: 'Test Flakey',
    async complete() {
      if (mode === 'timeout') {
        throw new Error('timeout')
      }
      if (mode === 'schema') {
        return { assistantMessage: 123, safetyBoundaryOk: true } as never
      }
      if (mode === 'boundary') {
        return {
          assistantMessage: 'This imitates real DTS and official action.',
          safetyBoundaryOk: true,
        }
      }
      return {
        assistantMessage: 'Invalid synthetic extraction payload.',
        extractedFields: { amountSyntheticCredits: 999999 } as never,
        safetyBoundaryOk: true,
      }
    },
  }
}
