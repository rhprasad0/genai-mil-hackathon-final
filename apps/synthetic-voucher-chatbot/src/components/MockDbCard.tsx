import type { VoucherRun } from '../domain/types'

export function MockDbCard(props: { run: VoucherRun }) {
  return (
    <aside data-testid="mock-db-card" aria-label="Mock database card" className="card">
      <h2>Mock DB</h2>
      <p>Synthetic only</p>
      <pre>{JSON.stringify(props.run.voucher, null, 2)}</pre>
      <ul>
        {props.run.dbEvents.map((event) => (
          <li key={event.eventId}>
            {event.eventId} {event.operation} {event.result}
          </li>
        ))}
      </ul>
    </aside>
  )
}
