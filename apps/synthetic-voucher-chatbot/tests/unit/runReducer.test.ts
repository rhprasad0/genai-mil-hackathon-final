import { describe, expect, it } from 'vitest'
import { SEED_BOT_MESSAGES } from '../../src/domain/constants'
import { FIXTURES } from '../../src/domain/fixtures'
import { confirmRun, replayRun } from '../../src/app/runReducer'
import { createInitialRun } from '../../src/app/createInitialRun'

describe('run lifecycle basics', () => {
  it('creates an initial run with expected defaults', () => {
    const runA = createInitialRun()
    const runB = createInitialRun()
    expect(runA.status).toBe('collecting')
    expect(runA.provider).toBe('stub')
    expect(runA.dbEvents).toEqual([])
    expect(runA.auditEvents).toEqual([])
    expect(runA.chatMessages).toHaveLength(SEED_BOT_MESSAGES.length)
    expect(runA.determination).toBeUndefined()
    expect(runA.runId).toMatch(/^SYN-RUN-\d{4}$/)
    expect(runA.voucherId).toMatch(/^SYN-VCH-\d{4}$/)
    expect(runA.runId).not.toBe(runB.runId)
    expect(runA.voucherId).not.toBe(runB.voucherId)
  })

  it('resets ids and state on replay', () => {
    const run = createInitialRun({ fixtureId: 'SYN_CLEAN_LODGING' })
    run.voucher = { ...FIXTURES.SYN_CLEAN_LODGING }
    const determined = confirmRun(run)
    const replayed = replayRun(determined)
    expect(replayed.runId).not.toBe(determined.runId)
    expect(replayed.voucherId).not.toBe(determined.voucherId)
    expect(replayed.dbEvents).toEqual([])
    expect(replayed.auditEvents).toEqual([])
    expect(replayed.voucher).toEqual({})
    expect(replayed.determination).toBeUndefined()
  })
})
