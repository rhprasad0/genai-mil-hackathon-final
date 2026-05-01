import { unavailableProvider } from './unavailableProvider'
import { stubProvider } from './stubProvider'
import type { ChatProvider } from './types'

const providers = new Map<string, ChatProvider>([
  ['stub', stubProvider],
  ['openai', { ...unavailableProvider, id: 'openai', label: 'OpenAI' }],
  ['anthropic', { ...unavailableProvider, id: 'anthropic', label: 'Anthropic' }],
  ['gemini', { ...unavailableProvider, id: 'gemini', label: 'Gemini' }],
  ['ollama_compatible', { ...unavailableProvider, id: 'ollama_compatible', label: 'Ollama-compatible' }],
])

export function getProvider(id: string): ChatProvider {
  return providers.get(id) ?? stubProvider
}

export function registerProvider(provider: ChatProvider) {
  providers.set(provider.id, provider)
}

export function resetProviderRegistry() {
  for (const id of Array.from(providers.keys())) {
    if (!['stub', 'openai', 'anthropic', 'gemini', 'ollama_compatible'].includes(id)) {
      providers.delete(id)
    }
  }
}
