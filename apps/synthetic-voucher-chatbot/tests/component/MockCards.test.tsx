import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { createInitialRun } from '../../src/app/createInitialRun'
import { createAuditEvent, createDbEvent } from '../../src/domain/mockEvents'
import { MockAuditCard } from '../../src/components/MockAuditCard'
import { MockDbCard } from '../../src/components/MockDbCard'

describe('mock cards', () => {
  it('render content and synthetic marker', () => {
    const run = createInitialRun()
    run.dbEvents.push(createDbEvent(run, 'fake_db.begin_tx', { status: run.status }))
    run.auditEvents.push(createAuditEvent(run, 'chatbot', 'chat.field_requested', 'travelerPersona'))
    render(
      <>
        <MockDbCard run={run} />
        <MockAuditCard run={run} />
      </>,
    )
    expect(screen.getByTestId('mock-db-card')).toHaveTextContent('Synthetic only')
    expect(screen.getByTestId('mock-audit-card')).toHaveTextContent('chat.field_requested')
  })
})
