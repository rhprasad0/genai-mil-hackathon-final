export type Determination = 'accepted' | 'rejected' | 'request_more_info' | 'escalated'

export type VoucherCategory = 'lodging' | 'meal' | 'transit' | 'misc'

export type SyntheticVoucher = {
  travelerPersona?: string
  tripPurpose?: string
  dateRange?: string
  category?: VoucherCategory
  amountSyntheticCredits?: number
  fakeReceiptPresent?: boolean
  amountMatchesAuthorization?: boolean
  explanation?: string
}

export type VoucherDetermination = {
  value: Determination
  reason: string
  missingFields: string[]
  ruleIds: string[]
}

export type ProviderId = 'stub' | 'openai' | 'anthropic' | 'gemini' | 'ollama_compatible'

export type ChatMessage = {
  id: string
  role: 'assistant' | 'user'
  text: string
}

export type MockDbEvent = {
  eventId: string
  runId: string
  voucherId: string
  operation:
    | 'fake_db.begin_tx'
    | 'fake_db.upsert_voucher'
    | 'fake_db.set_status'
    | 'fake_db.commit_tx'
  statePatch: Partial<SyntheticVoucher> | { status: VoucherRun['status'] }
  result: 'ok' | 'noop' | 'blocked'
  syntheticOnly: true
}

export type MockAuditEventName =
  | 'chat.field_requested'
  | 'chat.field_captured'
  | 'voucher.summary_confirmed'
  | 'voucher.determination_rendered'
  | 'provider.fallback_to_stub'
  | 'provider.output_schema_rejected'
  | 'safety.synthetic_boundary_repaired'

export type MockAuditEvent = {
  eventId: string
  runId: string
  actor: 'chatbot' | 'user' | 'rule_engine' | 'provider'
  name: MockAuditEventName
  note: string
}

export type FixtureRecord = {
  id:
    | 'SYN_CLEAN_LODGING'
    | 'SYN_MISSING_RECEIPT'
    | 'SYN_AMOUNT_MISMATCH'
    | 'SYN_AMBIGUOUS_MISC'
    | 'SYN_TRANSIT_SMALL'
  travelerPersona: string
  fakeVoucherSeed: string
  tripPurpose: string
  dateRange: string
  category: VoucherCategory
  amountSyntheticCredits: number
  fakeAuthorizedAmount?: number
  fakeGapClaim?: number
  fakeReceiptPresent: boolean
  amountMatchesAuthorization: boolean
  explanation?: string
  expectedDetermination: Determination
  expectedRuleIds: string[]
  transcript: string[]
}

export type VoucherRun = {
  runId: string
  voucherId: string
  status: 'collecting' | 'confirming' | 'submitted' | 'determined'
  provider: ProviderId
  voucher: SyntheticVoucher
  chatMessages: ChatMessage[]
  dbEvents: MockDbEvent[]
  auditEvents: MockAuditEvent[]
  determination?: VoucherDetermination
  boundaryViolation: boolean
  activeFixtureId?: FixtureRecord['id']
}
