import { REQUIRED_FIELD_ORDER } from '../domain/constants'
import type { SyntheticVoucher } from '../domain/types'
import type { ChatProvider } from './types'

function nextField(voucher: SyntheticVoucher) {
  return REQUIRED_FIELD_ORDER.find((field) => voucher[field] === undefined)
}

export const STUB_FALLBACK_MESSAGE = 'Synthetic helper is continuing locally with deterministic guidance.'

export const stubProvider: ChatProvider = {
  id: 'stub',
  label: 'Stub',
  async complete(input) {
    const requestedField = nextField(input.voucherState)
    return {
      assistantMessage: requestedField
        ? `${STUB_FALLBACK_MESSAGE} Next field: ${requestedField}.`
        : 'Synthetic summary is complete and ready for confirmation.',
      requestedField,
      safetyBoundaryOk: true,
      providerStatus: 'ok',
    }
  },
}
