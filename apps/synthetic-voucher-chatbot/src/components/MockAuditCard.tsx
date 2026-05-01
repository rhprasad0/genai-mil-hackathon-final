import type { VoucherRun } from '../domain/types'

export function MockAuditCard(props: { run: VoucherRun }) {
  return (
    <aside data-testid="mock-audit-card" aria-label="Mock audit card" className="card">
      <h2>Mock Audit</h2>
      <ul>
        {props.run.auditEvents.map((event) => (
          <li key={event.eventId}>
            {event.eventId} {event.name} {event.actor}
          </li>
        ))}
      </ul>
    </aside>
  )
}
