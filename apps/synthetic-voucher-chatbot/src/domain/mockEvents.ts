import type { MockAuditEvent, MockAuditEventName, MockDbEvent, SyntheticVoucher, VoucherRun } from './types'

function formatId(prefix: 'DBE' | 'AUD', index: number): string {
  return `${prefix}-${String(index).padStart(4, '0')}`
}

export function createDbEvent(
  run: VoucherRun,
  operation: MockDbEvent['operation'],
  statePatch: MockDbEvent['statePatch'],
  result: MockDbEvent['result'] = 'ok',
): MockDbEvent {
  return {
    eventId: formatId('DBE', run.dbEvents.length + 1),
    runId: run.runId,
    voucherId: run.voucherId,
    operation,
    statePatch,
    result,
    syntheticOnly: true,
  }
}

export function createAuditEvent(
  run: VoucherRun,
  actor: MockAuditEvent['actor'],
  name: MockAuditEventName,
  note: string,
): MockAuditEvent {
  return {
    eventId: formatId('AUD', run.auditEvents.length + 1),
    runId: run.runId,
    actor,
    name,
    note,
  }
}

export function buildUpsertPatch(field: keyof SyntheticVoucher, value: SyntheticVoucher[keyof SyntheticVoucher]) {
  return { [field]: value } as Partial<SyntheticVoucher>
}
