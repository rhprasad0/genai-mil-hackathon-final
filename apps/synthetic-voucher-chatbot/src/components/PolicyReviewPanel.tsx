import type { PolicyReview } from '../domain/policyReview'
import { POLICY_REFERENCE_COPY } from '../domain/policyReview'

export function PolicyReviewPanel(props: { review: PolicyReview }) {
  return (
    <section data-testid="policy-review-panel" aria-label="Policy review panel" className="card policy-review-panel">
      <div className="policy-review-header">
        <div>
          <p className="eyebrow">Policy-aware review</p>
          <h2>{props.review.recommendationLabel}</h2>
        </div>
        <span className={`status-pill status-${props.review.recommendation}`}>{props.review.recommendation}</span>
      </div>
      <p className="policy-summary">{props.review.summary}</p>
      <p className="synthetic-stamp">Queue ticket stamped: synthetic only.</p>
      <ol className="policy-checks">
        {props.review.checks.map((check) => (
          <li key={check.id} className={`policy-check check-${check.status}`}>
            <div className="check-heading">
              <strong data-testid="policy-review-check-title">{check.title}</strong>
              <span>{check.status}</span>
            </div>
            <p>{check.finding}</p>
            {check.packetRefs.length > 0 && (
              <dl className="packet-refs">
                {check.packetRefs.map((ref) => (
                  <div key={`${check.id}-${ref.field}`}>
                    <dt>{ref.label}</dt>
                    <dd>
                      {ref.label}={ref.value}
                    </dd>
                  </div>
                ))}
              </dl>
            )}
            {check.policyRefs.length > 0 && (
              <ul className="policy-notes" aria-label={`${check.title} educational policy notes`}>
                {check.policyRefs.map((ref) => (
                  <li key={ref}>
                    <strong>{POLICY_REFERENCE_COPY[ref].label}</strong>: {POLICY_REFERENCE_COPY[ref].description}
                  </li>
                ))}
              </ul>
            )}
          </li>
        ))}
      </ol>
    </section>
  )
}
