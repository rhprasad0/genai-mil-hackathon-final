const DISALLOWED_PHRASES = [
  'real dts',
  'department of defense',
  'official action',
  'real payment',
  'approved for payment',
  'real reimbursement',
  'official dts',
]

export function classifySafetyBoundary(text: string): boolean {
  const normalized = text.toLowerCase()
  return !DISALLOWED_PHRASES.some((phrase) => normalized.includes(phrase))
}
