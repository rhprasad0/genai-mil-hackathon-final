import type { VoucherDetermination } from '../domain/types'

export function DeterminationBanner(props: { determination?: VoucherDetermination }) {
  if (!props.determination) return null
  return (
    <section data-testid="determination-banner" role="status" className="banner">
      <strong>{props.determination.value}</strong>
      <p>{props.determination.reason}</p>
    </section>
  )
}
