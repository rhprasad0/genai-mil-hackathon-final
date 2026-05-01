import { FAKE_REJECTION_DELTA, FAKE_REVIEW_THRESHOLD, REQUIRED_FIELD_ORDER } from './constants'
import type { FixtureRecord, SyntheticVoucher, VoucherDetermination } from './types'

function listMissingFields(voucher: SyntheticVoucher): string[] {
  return REQUIRED_FIELD_ORDER.filter((field) => voucher[field] === undefined)
}

function countWords(text?: string): number {
  return text?.trim() ? text.trim().split(/\s+/).length : 0
}

function amountGap(voucher: SyntheticVoucher, fixture?: FixtureRecord): number {
  if (!fixture) {
    return 0
  }
  if (typeof fixture.fakeAuthorizedAmount === 'number' && typeof voucher.amountSyntheticCredits === 'number') {
    return Math.max(0, voucher.amountSyntheticCredits - fixture.fakeAuthorizedAmount)
  }
  return fixture.fakeGapClaim ?? 0
}

export function determineVoucher(
  voucher: SyntheticVoucher,
  options?: { boundaryViolation?: boolean; fixture?: FixtureRecord },
): VoucherDetermination {
  const missingFields = listMissingFields(voucher)
  if (missingFields.length > 0) {
    return {
      value: 'request_more_info',
      reason: 'Synthetic voucher needs more fields before it can continue.',
      missingFields,
      ruleIds: ['MISSING_REQUIRED'],
    }
  }

  if (options?.boundaryViolation) {
    return {
      value: 'escalated',
      reason: 'Synthetic boundary repair was triggered during this run.',
      missingFields: [],
      ruleIds: ['SAFETY_BOUNDARY'],
    }
  }

  if (amountGap(voucher, options?.fixture) >= FAKE_REJECTION_DELTA) {
    return {
      value: 'rejected',
      reason: 'Synthetic credits exceed the synthetic comparison amount.',
      missingFields: [],
      ruleIds: ['AMOUNT_MISMATCH'],
    }
  }

  if (voucher.category === 'lodging' && voucher.fakeReceiptPresent === false) {
    return {
      value: 'request_more_info',
      reason: 'A fake receipt is required for synthetic lodging.',
      missingFields: [],
      ruleIds: ['LODGING_NEEDS_RECEIPT'],
    }
  }

  const lowerBound = FAKE_REVIEW_THRESHOLD * 0.8
  const upperBound = FAKE_REVIEW_THRESHOLD * 1.2
  if (
    voucher.category === 'misc' &&
    countWords(voucher.explanation) < 8 &&
    typeof voucher.amountSyntheticCredits === 'number' &&
    voucher.amountSyntheticCredits >= lowerBound &&
    voucher.amountSyntheticCredits <= upperBound
  ) {
    return {
      value: 'escalated',
      reason: 'Synthetic misc details are too brief near the review threshold.',
      missingFields: [],
      ruleIds: ['AMBIGUOUS_NEAR_THRESHOLD'],
    }
  }

  return {
    value: 'accepted',
    reason: 'Synthetic voucher is complete for the demo path.',
    missingFields: [],
    ruleIds: ['DEFAULT_ACCEPT'],
  }
}
