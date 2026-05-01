import { SAFETY_BOUNDARY_NOTICE } from '../domain/constants'

export function SafetyBoundaryNotice() {
  return (
    <p data-testid="safety-boundary-notice" className="notice">
      {SAFETY_BOUNDARY_NOTICE}
    </p>
  )
}
