import { createElement } from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { VoucherChatApp } from '../app/VoucherChatApp'
import type { FixtureRecord, VoucherRun } from '../domain/types'
import { FIXTURES } from '../domain/fixtures'

export async function playFixtureTranscript(
  fixtureId: FixtureRecord['id'],
  options?: { alsoConfirm?: boolean; providerId?: string },
) {
  const user = userEvent.setup()
  let latestRun: VoucherRun | undefined

  render(
    createElement(VoucherChatApp, {
      initialFixtureId: fixtureId,
      initialProviderId: options?.providerId,
      onRunChange: (run: VoucherRun) => {
        latestRun = run
      },
    }),
  )

  for (const reply of FIXTURES[fixtureId].transcript) {
    const input = await screen.findByTestId('chat-input')
    await user.clear(input)
    await user.type(input, reply)
    await user.click(await screen.findByTestId('send-button'))
  }

  async function confirm() {
    await user.click(await screen.findByTestId('confirm-button'))
  }

  if (options?.alsoConfirm) {
    await confirm()
  }

  return {
    screen,
    run: latestRun!,
    dbEvents: latestRun!.dbEvents,
    auditEvents: latestRun!.auditEvents,
    confirm,
  }
}
