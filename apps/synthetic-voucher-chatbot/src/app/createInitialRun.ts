import { SEED_BOT_MESSAGES } from '../domain/constants'
import type { ChatMessage, FixtureRecord, ProviderId, VoucherRun } from '../domain/types'

let runCounter = 0

function nextId(prefix: 'SYN-RUN' | 'SYN-VCH'): string {
  runCounter += 1
  return `${prefix}-${String(runCounter).padStart(4, '0')}`
}

function seedMessages(): ChatMessage[] {
  return SEED_BOT_MESSAGES.map((text, index) => ({
    id: `seed-${index + 1}`,
    role: 'assistant',
    text,
  }))
}

export function createInitialRun(options?: {
  provider?: ProviderId
  fixtureId?: FixtureRecord['id']
}): VoucherRun {
  return {
    runId: nextId('SYN-RUN'),
    voucherId: nextId('SYN-VCH'),
    status: 'collecting',
    provider: options?.provider ?? 'stub',
    voucher: {},
    chatMessages: seedMessages(),
    dbEvents: [],
    auditEvents: [],
    boundaryViolation: false,
    activeFixtureId: options?.fixtureId,
  }
}
