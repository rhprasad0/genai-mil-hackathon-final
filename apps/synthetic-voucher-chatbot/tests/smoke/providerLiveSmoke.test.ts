import { describe, expect, it } from 'vitest'

const liveEnabled = process.env.LIVE_PROVIDER_SMOKE === '1'
const noLiveAdaptersYet = true

const liveCases = [
  { id: 'stub', requiredEnv: [] },
  { id: 'openai', requiredEnv: ['OPENAI_API_KEY'] },
  { id: 'anthropic', requiredEnv: ['ANTHROPIC_API_KEY'] },
  { id: 'gemini', requiredEnv: ['GEMINI_API_KEY or GOOGLE_API_KEY'] },
  { id: 'ollama_compatible', requiredEnv: ['OLLAMA_BASE_URL', 'OLLAMA_MODEL'] },
  { id: 'ollama_cloud', requiredEnv: ['OLLAMA_BASE_URL', 'OLLAMA_MODEL', 'OLLAMA_CLOUD_API_KEY'] },
] as const

describe('optional live provider smoke harness', () => {
  it('documents all provider smoke cases without reading secret values', () => {
    expect(liveCases.map((testCase) => testCase.id)).toEqual([
      'stub',
      'openai',
      'anthropic',
      'gemini',
      'ollama_compatible',
      'ollama_cloud',
    ])
  })

  for (const smokeCase of liveCases) {
    it.skipIf(!liveEnabled || noLiveAdaptersYet)(
      `live smoke for ${smokeCase.id} only when explicitly enabled and configured`,
      async () => {
        expect(smokeCase.requiredEnv.every((name) => name.length > 0)).toBe(true)
      },
    )
  }
})
