import { STUB_FALLBACK_MESSAGE } from './stubProvider'
import type { ChatProvider } from './types'

export const unavailableProvider: ChatProvider = {
  id: 'openai',
  label: 'Unavailable',
  async complete() {
    return {
      assistantMessage: `${STUB_FALLBACK_MESSAGE} Selected provider is unavailable in V0.`,
      safetyBoundaryOk: true,
      providerStatus: 'unavailable',
    }
  },
}
