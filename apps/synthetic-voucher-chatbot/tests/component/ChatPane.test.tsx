import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { ChatPane } from '../../src/components/ChatPane'
import { createInitialRun } from '../../src/app/createInitialRun'

describe('ChatPane', () => {
  it('renders stable controls', () => {
    render(
      <ChatPane
        run={createInitialRun()}
        inputValue=""
        onInputChange={() => {}}
        onSend={() => {}}
        onConfirm={() => {}}
        onReplay={() => {}}
      />,
    )
    expect(screen.getByTestId('chat-pane')).toBeInTheDocument()
    expect(screen.getByTestId('chat-input')).toBeInTheDocument()
    expect(screen.getByTestId('send-button')).toBeInTheDocument()
  })
})
