import { useEffect, useState } from 'react'
import { createInitialRun } from './createInitialRun'
import { confirmRun, replayRun, submitUserTurn } from './runReducer'
import { ChatPane } from '../components/ChatPane'
import { MockAuditCard } from '../components/MockAuditCard'
import { MockDbCard } from '../components/MockDbCard'
import { PolicyReviewPanel } from '../components/PolicyReviewPanel'
import { ProviderSelector } from '../components/ProviderSelector'
import { SafetyBoundaryNotice } from '../components/SafetyBoundaryNotice'
import { V1_SCENARIO_FIXTURE_IDS, derivePolicyReview, isV1ScenarioFixtureId } from '../domain/policyReview'
import type { FixtureRecord, VoucherRun } from '../domain/types'

export function VoucherChatApp(props: {
  initialFixtureId?: FixtureRecord['id']
  initialProviderId?: string
  onRunChange?: (run: VoucherRun) => void
}) {
  const initialFixtureId = props.initialFixtureId ?? V1_SCENARIO_FIXTURE_IDS[0]
  const [fixtureId, setFixtureId] = useState<FixtureRecord['id']>(initialFixtureId)
  const [providerId, setProviderId] = useState(props.initialProviderId ?? 'stub')
  const [run, setRun] = useState(() => createInitialRun({ fixtureId, provider: 'stub' }))
  const [inputValue, setInputValue] = useState('')
  const reviewFixtureId = isV1ScenarioFixtureId(fixtureId) ? fixtureId : V1_SCENARIO_FIXTURE_IDS[0]
  const policyReview = derivePolicyReview(reviewFixtureId, run.voucher)

  useEffect(() => {
    props.onRunChange?.(run)
  }, [props, run])

  async function handleSend() {
    const next = await submitUserTurn({ ...run, provider: providerId as VoucherRun['provider'] }, inputValue)
    setRun(next)
    setInputValue('')
  }

  function handleConfirm() {
    setRun(confirmRun({ ...run }))
  }

  function handleReplay() {
    setRun(replayRun(run))
  }

  function handleFixtureChange(nextFixtureId: (typeof V1_SCENARIO_FIXTURE_IDS)[number]) {
    setFixtureId(nextFixtureId)
    setRun(createInitialRun({ fixtureId: nextFixtureId, provider: 'stub' }))
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <h1>Policy Bonfire: DTS From Hell</h1>
        <ProviderSelector value={providerId} onChange={setProviderId} />
        <label>
          Scenario
          <select
            data-testid="scenario-selector"
            value={fixtureId}
            onChange={(event) => handleFixtureChange(event.target.value as (typeof V1_SCENARIO_FIXTURE_IDS)[number])}
          >
            {V1_SCENARIO_FIXTURE_IDS.map((id) => (
              <option key={id} value={id}>
                {id}
              </option>
            ))}
          </select>
        </label>
      </header>
      <SafetyBoundaryNotice />
      <div className="layout">
        <ChatPane
          run={run}
          inputValue={inputValue}
          onInputChange={setInputValue}
          onSend={handleSend}
          onConfirm={handleConfirm}
          onReplay={handleReplay}
        />
        <div className="sidebar">
          <PolicyReviewPanel review={policyReview} />
          <MockDbCard run={run} />
          <MockAuditCard run={run} />
        </div>
      </div>
    </main>
  )
}
