import { PROVIDER_UNAVAILABLE_SUFFIX } from '../domain/constants'
import type { ProviderId } from '../domain/types'

const options: { id: ProviderId; label: string }[] = [
  { id: 'stub', label: 'stub' },
  { id: 'openai', label: `openai (${PROVIDER_UNAVAILABLE_SUFFIX})` },
  { id: 'anthropic', label: `anthropic (${PROVIDER_UNAVAILABLE_SUFFIX})` },
  { id: 'gemini', label: `gemini (${PROVIDER_UNAVAILABLE_SUFFIX})` },
  { id: 'ollama_compatible', label: `ollama_compatible (${PROVIDER_UNAVAILABLE_SUFFIX})` },
]

export function ProviderSelector(props: {
  value: string
  onChange: (value: string) => void
}) {
  return (
    <label>
      Provider
      <select
        data-testid="provider-selector"
        value={props.value}
        onChange={(event) => props.onChange(event.target.value)}
      >
        {options.map((option) => (
          <option key={option.id} value={option.id}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  )
}
