import { describe, expect, it } from 'vitest'
import { createInitialRun } from '../../src/app/createInitialRun'
import { createAuditEvent, createDbEvent } from '../../src/domain/mockEvents'

describe('mock event ids', () => {
  it('start at 1 and increment', () => {
    const run = createInitialRun()
    const db1 = createDbEvent(run, 'fake_db.begin_tx', { status: run.status })
    run.dbEvents.push(db1)
    const db2 = createDbEvent(run, 'fake_db.commit_tx', { status: run.status })
    const audit1 = createAuditEvent(run, 'chatbot', 'chat.field_requested', 'travelerPersona')
    run.auditEvents.push(audit1)
    const audit2 = createAuditEvent(run, 'user', 'chat.field_captured', 'travelerPersona')
    expect(db1.eventId).toBe('DBE-0001')
    expect(db2.eventId).toBe('DBE-0002')
    expect(audit1.eventId).toBe('AUD-0001')
    expect(audit2.eventId).toBe('AUD-0002')
  })
})
