import { createInitialRun } from './createInitialRun'
import { REQUIRED_FIELD_ORDER, SAFETY_FALLBACK_MESSAGE } from '../domain/constants'
import { collectField, validateFieldPatch } from '../domain/fieldCollector'
import { FIXTURES } from '../domain/fixtures'
import { createAuditEvent, createDbEvent } from '../domain/mockEvents'
import { determineVoucher } from '../domain/rules'
import { classifySafetyBoundary } from '../domain/safetyBoundary'
import { getProvider } from '../providers/providerRegistry'
import { stubProvider } from '../providers/stubProvider'
import type { ChatMessage, SyntheticVoucher, VoucherRun } from '../domain/types'
import type { ProviderOutput } from '../providers/types'

function nextMessageId(run: VoucherRun): string {
  return `msg-${run.chatMessages.length + 1}`
}

function appendMessage(run: VoucherRun, role: ChatMessage['role'], text: string) {
  run.chatMessages.push({ id: nextMessageId(run), role, text })
}

function nextField(voucher: SyntheticVoucher) {
  return REQUIRED_FIELD_ORDER.find((field) => voucher[field] === undefined)
}

function fieldPrompt(field: keyof SyntheticVoucher): string {
  return `Please provide ${field} for this synthetic voucher.`
}

function sanitizeProviderOutput(output: ProviderOutput, run: VoucherRun): ProviderOutput {
  const boundaryOk = classifySafetyBoundary(output.assistantMessage)
  if (!boundaryOk) {
    run.boundaryViolation = true
    run.auditEvents.push(
      createAuditEvent(run, 'provider', 'safety.synthetic_boundary_repaired', `provider=${run.provider} ; kind=safety_boundary`),
    )
    return { ...output, assistantMessage: SAFETY_FALLBACK_MESSAGE, safetyBoundaryOk: false }
  }
  return { ...output, safetyBoundaryOk: true }
}

function mergeExtractedFields(run: VoucherRun, extractedFields?: Partial<SyntheticVoucher>) {
  if (!extractedFields) return
  for (const [field, value] of Object.entries(extractedFields) as [keyof SyntheticVoucher, unknown][]) {
    const result = validateFieldPatch(field, value)
    if ('rejectionReason' in result) continue
    run.voucher = { ...run.voucher, ...result }
  }
}

export async function submitUserTurn(run: VoucherRun, input: string): Promise<VoucherRun> {
  appendMessage(run, 'user', input)
  const field = nextField(run.voucher)
  if (field) {
    const collected = collectField(run.voucher, field, input)
    if ('rejectionReason' in collected) {
      appendMessage(run, 'assistant', collected.rejectionReason)
      run.auditEvents.push(createAuditEvent(run, 'chatbot', 'chat.field_requested', field))
      return { ...run }
    }
    run.voucher = { ...run.voucher, ...collected }
    run.dbEvents.push(createDbEvent(run, 'fake_db.begin_tx', { status: run.status }))
    run.dbEvents.push(createDbEvent(run, 'fake_db.upsert_voucher', collected))
    run.dbEvents.push(createDbEvent(run, 'fake_db.commit_tx', collected))
    run.auditEvents.push(createAuditEvent(run, 'user', 'chat.field_captured', field))
  }

  const provider = getProvider(run.provider)
  let providerOutput: ProviderOutput
  try {
    providerOutput = sanitizeProviderOutput(
      await provider.complete({
        systemPrompt: 'Synthetic-only local demo.',
        messages: run.chatMessages,
        voucherState: run.voucher,
        allowedDeterminations: ['accepted', 'rejected', 'request_more_info', 'escalated'],
      }),
      run,
    )
  } catch {
    run.auditEvents.push(createAuditEvent(run, 'provider', 'provider.fallback_to_stub', `provider=${run.provider} ; kind=timeout`))
    providerOutput = await stubProvider.complete({
      systemPrompt: 'Synthetic-only local demo.',
      messages: run.chatMessages,
      voucherState: run.voucher,
      allowedDeterminations: ['accepted', 'rejected', 'request_more_info', 'escalated'],
    })
  }

  mergeExtractedFields(run, providerOutput.extractedFields)
  appendMessage(run, 'assistant', providerOutput.assistantMessage)

  const missingField = nextField(run.voucher)
  if (missingField) {
    run.auditEvents.push(createAuditEvent(run, 'chatbot', 'chat.field_requested', missingField))
    appendMessage(run, 'assistant', fieldPrompt(missingField))
  } else {
    run.status = 'confirming'
    appendMessage(run, 'assistant', 'Please confirm the synthetic voucher summary.')
  }

  return { ...run }
}

export function confirmRun(run: VoucherRun): VoucherRun {
  run.status = 'submitted'
  run.auditEvents.push(createAuditEvent(run, 'user', 'voucher.summary_confirmed', 'synthetic summary confirmed'))
  run.dbEvents.push(createDbEvent(run, 'fake_db.set_status', { status: 'submitted' }))
  const fixture = run.activeFixtureId ? FIXTURES[run.activeFixtureId] : undefined
  run.determination = determineVoucher(run.voucher, {
    boundaryViolation: run.boundaryViolation,
    fixture,
  })
  run.status = 'determined'
  run.dbEvents.push(createDbEvent(run, 'fake_db.commit_tx', { status: 'determined' }))
  run.auditEvents.push(createAuditEvent(run, 'rule_engine', 'voucher.determination_rendered', 'synthetic determination rendered'))
  return { ...run }
}

export function replayRun(run: VoucherRun): VoucherRun {
  return createInitialRun({ provider: run.provider, fixtureId: run.activeFixtureId })
}
