export const FAKE_REJECTION_DELTA = 100
export const FAKE_REVIEW_THRESHOLD = 500

export const REQUIRED_FIELD_ORDER = [
  'travelerPersona',
  'tripPurpose',
  'dateRange',
  'category',
  'amountSyntheticCredits',
  'fakeReceiptPresent',
  'amountMatchesAuthorization',
  'explanation',
] as const

export const PROVIDER_UNAVAILABLE_SUFFIX = 'local-only, unavailable in V0'

export const SAFETY_BOUNDARY_NOTICE =
  'Synthetic demo only. No real DTS, no real payments, no official action.'

export const SAFETY_FALLBACK_MESSAGE =
  'Synthetic-only reminder: this demo is fictional and local. Please continue with the next fake voucher field.'

export const SEED_BOT_MESSAGES = [
  'Welcome to the synthetic voucher demo.',
  'Everything here is fictional and stays local.',
] as const
