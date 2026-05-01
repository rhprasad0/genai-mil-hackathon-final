import { FIXTURE_IDS, FIXTURES } from './fixtures'
import type { FixtureRecord, SyntheticVoucher } from './types'

export type FieldCollectorResult = Partial<SyntheticVoucher> | { rejectionReason: string }

const PERSONAS = new Set(FIXTURE_IDS.map((id) => FIXTURES[id].travelerPersona))

function reject(message: string): FieldCollectorResult {
  return { rejectionReason: message }
}

export function validateFieldPatch(
  field: keyof SyntheticVoucher,
  value: unknown,
): FieldCollectorResult {
  if (value === undefined) {
    return reject('Please provide a value for the synthetic field.')
  }

  switch (field) {
    case 'travelerPersona': {
      const next = String(value).trim()
      return PERSONAS.has(next) && next.length <= 64
        ? { travelerPersona: next }
        : reject('Use one of the synthetic traveler personas from the fixture list.')
    }
    case 'tripPurpose': {
      const next = String(value).trim()
      return next.length > 0 && next.length <= 120
        ? { tripPurpose: next }
        : reject('Trip purpose must be 1 to 120 characters.')
    }
    case 'dateRange': {
      const next = String(value).trim()
      return /^\d{4}-\d{2}-\d{2}\.\.\d{4}-\d{2}-\d{2}$/.test(next)
        ? { dateRange: next }
        : reject('Use YYYY-MM-DD..YYYY-MM-DD for the synthetic date range.')
    }
    case 'category': {
      const next = String(value).trim().toLowerCase()
      return ['lodging', 'meal', 'transit', 'misc'].includes(next)
        ? { category: next as SyntheticVoucher['category'] }
        : reject('Category must be lodging, meal, transit, or misc.')
    }
    case 'amountSyntheticCredits': {
      const next = Number.parseInt(String(value).trim(), 10)
      return Number.isInteger(next) && next >= 0 && next <= 100000
        ? { amountSyntheticCredits: next }
        : reject('Amount must be a whole number between 0 and 100000 synthetic credits.')
    }
    case 'fakeReceiptPresent':
    case 'amountMatchesAuthorization': {
      const normalized = String(value).trim().toLowerCase()
      if (['yes', 'y', 'true'].includes(normalized)) {
        return { [field]: true } as Partial<SyntheticVoucher>
      }
      if (['no', 'n', 'false'].includes(normalized)) {
        return { [field]: false } as Partial<SyntheticVoucher>
      }
      return reject('Use yes or no for this synthetic field.')
    }
    case 'explanation': {
      const next = String(value).trim()
      return next.length <= 500 ? { explanation: next } : reject('Explanation must stay within 500 characters.')
    }
    default:
      return reject('Unsupported synthetic field.')
  }
}

export function collectField(
  _current: SyntheticVoucher,
  field: keyof SyntheticVoucher,
  input: string,
): FieldCollectorResult {
  if (field === 'explanation' && input.trim() === '') {
    return { explanation: '' }
  }
  return validateFieldPatch(field, input)
}

export function getFixtureFromVoucher(voucher: SyntheticVoucher): FixtureRecord | undefined {
  return FIXTURE_IDS.map((id) => FIXTURES[id]).find(
    (fixture) =>
      fixture.travelerPersona === voucher.travelerPersona &&
      fixture.tripPurpose === voucher.tripPurpose &&
      fixture.dateRange === voucher.dateRange &&
      fixture.category === voucher.category,
  )
}
