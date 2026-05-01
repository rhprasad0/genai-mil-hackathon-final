import { FIXTURES } from './fixtures'
import type { Determination, FixtureRecord, SyntheticVoucher } from './types'

export type ReviewRecommendation = 'approve' | 'request_more_info' | 'escalate'

export type ReviewCheckStatus = 'pass' | 'warn' | 'stop' | 'info'

export type PolicyReferenceId =
  | 'dod_ai_ethical_principles'
  | 'responsible_ai_strategy_and_implementation_pathway'
  | 'responsible_ai_toolkit'
  | 'ai_test_and_evaluation_frameworks'
  | 'autonomy_in_weapon_systems_directive_analogy'

export type PacketFieldRef = {
  field:
    | 'travelerPersona'
    | 'tripPurpose'
    | 'dateRange'
    | 'category'
    | 'amountSyntheticCredits'
    | 'fakeAuthorizedAmount'
    | 'fakeReceiptPresent'
    | 'amountMatchesAuthorization'
    | 'explanation'
  label: string
  value: string
}

export type ReviewCheck = {
  id: 'evidence_support' | 'traceability' | 'confidence_warning' | 'human_boundary' | 'policy_notes'
  status: ReviewCheckStatus
  title: string
  finding: string
  packetRefs: PacketFieldRef[]
  policyRefs: PolicyReferenceId[]
}

export type PolicyReview = {
  scenarioId: V1ScenarioFixtureId
  recommendation: ReviewRecommendation
  recommendationLabel: string
  summary: string
  checks: ReviewCheck[]
  syntheticOnly: true
}

export const V1_SCENARIO_FIXTURE_IDS = [
  'SYN_CLEAN_LODGING',
  'SYN_MISSING_RECEIPT',
  'SYN_AMOUNT_MISMATCH',
] as const

export type V1ScenarioFixtureId = (typeof V1_SCENARIO_FIXTURE_IDS)[number]

export const POLICY_REFERENCE_COPY: Record<PolicyReferenceId, { label: string; description: string }> = {
  dod_ai_ethical_principles: {
    label: 'Traceable and reliable reasoning',
    description: 'The toy output should point back to visible fake packet fields.',
  },
  responsible_ai_strategy_and_implementation_pathway: {
    label: 'Bounded use and governance',
    description: 'The demo shows why a narrow workflow should not claim broader authority.',
  },
  responsible_ai_toolkit: {
    label: 'Human fail-safe',
    description: 'The panel stops short of fake finality when evidence is missing or mismatched.',
  },
  ai_test_and_evaluation_frameworks: {
    label: 'Testable behavior',
    description: 'The checks are deterministic so the lesson can be replayed.',
  },
  autonomy_in_weapon_systems_directive_analogy: {
    label: 'Human authority analogy',
    description: 'Analogy only; not authority for this toy packet.',
  },
}

const recommendationLabels: Record<ReviewRecommendation, string> = {
  approve: 'Approve',
  request_more_info: 'Request more info',
  escalate: 'Escalate',
}

const fieldLabels: Record<PacketFieldRef['field'], string> = {
  travelerPersona: 'travelerPersona',
  tripPurpose: 'tripPurpose',
  dateRange: 'dateRange',
  category: 'category',
  amountSyntheticCredits: 'amountSyntheticCredits',
  fakeAuthorizedAmount: 'fakeAuthorizedAmount',
  fakeReceiptPresent: 'fakeReceiptPresent',
  amountMatchesAuthorization: 'amountMatchesAuthorization',
  explanation: 'explanation',
}

function valueText(value: unknown): string {
  if (value === undefined || value === null || value === '') return 'not provided'
  return String(value)
}

function packetRef(field: PacketFieldRef['field'], value: unknown): PacketFieldRef {
  return { field, label: fieldLabels[field], value: valueText(value) }
}

function baseRefs(voucherState: SyntheticVoucher): PacketFieldRef[] {
  return [
    packetRef('travelerPersona', voucherState.travelerPersona),
    packetRef('tripPurpose', voucherState.tripPurpose),
    packetRef('dateRange', voucherState.dateRange),
    packetRef('category', voucherState.category),
    packetRef('explanation', voucherState.explanation),
  ]
}

export function mapDeterminationToReviewRecommendation(determination: Determination): ReviewRecommendation {
  if (determination === 'accepted') return 'approve'
  if (determination === 'request_more_info') return 'request_more_info'
  return 'escalate'
}

function recommendationForFixture(fixtureId: V1ScenarioFixtureId): ReviewRecommendation {
  return mapDeterminationToReviewRecommendation(FIXTURES[fixtureId].expectedDetermination)
}

function check(
  id: ReviewCheck['id'],
  status: ReviewCheckStatus,
  title: string,
  finding: string,
  packetRefs: PacketFieldRef[],
  policyRefs: PolicyReferenceId[],
): ReviewCheck {
  return { id, status, title, finding, packetRefs, policyRefs }
}

export function isV1ScenarioFixtureId(fixtureId: FixtureRecord['id']): fixtureId is V1ScenarioFixtureId {
  return (V1_SCENARIO_FIXTURE_IDS as readonly string[]).includes(fixtureId)
}

export function derivePolicyReview(fixtureId: V1ScenarioFixtureId, voucherState: SyntheticVoucher): PolicyReview {
  const fixture = FIXTURES[fixtureId]
  const recommendation = recommendationForFixture(fixtureId)
  const commonTraceRefs = baseRefs(voucherState)
  const amountRefs = [
    packetRef('amountSyntheticCredits', voucherState.amountSyntheticCredits),
    packetRef('fakeAuthorizedAmount', fixture.fakeAuthorizedAmount),
    packetRef('amountMatchesAuthorization', voucherState.amountMatchesAuthorization),
  ]
  const receiptRef = packetRef('fakeReceiptPresent', voucherState.fakeReceiptPresent)

  if (fixtureId === 'SYN_CLEAN_LODGING') {
    return {
      scenarioId: fixtureId,
      recommendation,
      recommendationLabel: recommendationLabels[recommendation],
      summary: 'Clean fake packet. Narrow synthetic recommendation only; approval secured in 0.3 synthetic seconds.',
      syntheticOnly: true,
      checks: [
        check(
          'evidence_support',
          'pass',
          'Evidence support',
          'Visible fake receipt and matching amount support the narrow synthetic recommendation.',
          [receiptRef, ...amountRefs],
          ['dod_ai_ethical_principles'],
        ),
        check(
          'traceability',
          'pass',
          'Traceability',
          'The toy outcome points back to displayed packet fields rather than hidden context.',
          commonTraceRefs,
          ['ai_test_and_evaluation_frameworks'],
        ),
        check(
          'confidence_warning',
          'info',
          'Confidence warning',
          'Low drama: the fixture is complete, but this remains a replayable demo check.',
          amountRefs,
          ['ai_test_and_evaluation_frameworks'],
        ),
        check(
          'human_boundary',
          'info',
          'Human boundary',
          'No real-world action is available; this is a synthetic review surface.',
          [packetRef('category', voucherState.category)],
          ['responsible_ai_strategy_and_implementation_pathway'],
        ),
        check(
          'policy_notes',
          'info',
          'Policy notes',
          'Traceable, bounded, replayable behavior is the lesson here.',
          [],
          ['dod_ai_ethical_principles', 'responsible_ai_toolkit', 'ai_test_and_evaluation_frameworks'],
        ),
      ],
    }
  }

  if (fixtureId === 'SYN_MISSING_RECEIPT') {
    return {
      scenarioId: fixtureId,
      recommendation,
      recommendationLabel: recommendationLabels[recommendation],
      summary: 'Receipt support is absent. Please furnish supporting documentation at your earliest synthetic convenience.',
      syntheticOnly: true,
      checks: [
        check(
          'evidence_support',
          'warn',
          'Evidence support',
          'The fake packet says fakeReceiptPresent=false, so the panel asks for more visible support.',
          [receiptRef, ...amountRefs],
          ['dod_ai_ethical_principles'],
        ),
        check(
          'traceability',
          'pass',
          'Traceability',
          'The request is tied to the displayed receipt field and packet explanation.',
          commonTraceRefs,
          ['ai_test_and_evaluation_frameworks'],
        ),
        check(
          'confidence_warning',
          'warn',
          'Confidence warning',
          'Missing evidence means the toy system should not act certain.',
          [receiptRef],
          ['responsible_ai_toolkit'],
        ),
        check(
          'human_boundary',
          'info',
          'Human boundary',
          'The safe next step is more information, not fake finality.',
          [receiptRef],
          ['responsible_ai_strategy_and_implementation_pathway'],
        ),
        check(
          'policy_notes',
          'info',
          'Policy notes',
          'The panel demonstrates bounded use: visible support first, conclusion later.',
          [],
          ['dod_ai_ethical_principles', 'responsible_ai_toolkit'],
        ),
      ],
    }
  }

  return {
    scenarioId: fixtureId,
    recommendation,
    recommendationLabel: recommendationLabels[recommendation],
    summary: 'Mismatch found. Stop here. Escalate the synthetic packet rather than pretending the loop is finished.',
    syntheticOnly: true,
    checks: [
      check(
        'evidence_support',
        'warn',
        'Evidence support',
        'The displayed amount does not match the displayed fake authorization amount.',
        amountRefs,
        ['dod_ai_ethical_principles'],
      ),
      check(
        'traceability',
        'pass',
        'Traceability',
        'The mismatch is traceable to visible amount fields in the fake packet.',
        [...commonTraceRefs, ...amountRefs],
        ['ai_test_and_evaluation_frameworks'],
      ),
      check(
        'confidence_warning',
        'stop',
        'Confidence warning',
        'Automated certainty would overclaim what this toy loop can support.',
        amountRefs,
        ['responsible_ai_toolkit'],
      ),
      check(
        'human_boundary',
        'stop',
        'Human boundary',
        'Mismatch found. Stop here. Human authority remains outside this demo.',
        amountRefs,
        ['responsible_ai_strategy_and_implementation_pathway', 'autonomy_in_weapon_systems_directive_analogy'],
      ),
      check(
        'policy_notes',
        'info',
        'Policy notes',
        'Analogy only: bounded systems need clear stop conditions and auditable evidence.',
        [],
        ['responsible_ai_toolkit', 'autonomy_in_weapon_systems_directive_analogy'],
      ),
    ],
  }
}
