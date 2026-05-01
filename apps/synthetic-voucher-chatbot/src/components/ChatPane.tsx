import type { VoucherRun } from '../domain/types'
import { DeterminationBanner } from './DeterminationBanner'

export function ChatPane(props: {
  run: VoucherRun
  inputValue: string
  onInputChange: (value: string) => void
  onSend: () => void
  onConfirm: () => void
  onReplay: () => void
}) {
  return (
    <section data-testid="chat-pane" className="chat-pane">
      <div className="messages">
        {props.run.chatMessages.map((message) => (
          <p key={message.id}>{message.text}</p>
        ))}
      </div>
      <DeterminationBanner determination={props.run.determination} />
      {props.run.status === 'confirming' && (
        <button data-testid="confirm-button" onClick={props.onConfirm}>
          Confirm
        </button>
      )}
      {props.run.status === 'determined' && (
        <button data-testid="replay-button" onClick={props.onReplay}>
          Replay
        </button>
      )}
      <input
        data-testid="chat-input"
        value={props.inputValue}
        onChange={(event) => props.onInputChange(event.target.value)}
      />
      <button data-testid="send-button" onClick={props.onSend}>
        Send
      </button>
    </section>
  )
}
