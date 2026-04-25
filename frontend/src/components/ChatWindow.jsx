import { useEffect, useRef } from 'react'
import DataTable from './DataTable'

export default function ChatWindow({ messages, thinking, siteLoaded }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, thinking])

  if (messages.length === 0 && !thinking) {
    return (
      <div className="chat-window">
        <div className="chat-empty">
          <div className="chat-empty-icon">🕸️</div>
          {siteLoaded ? (
            <>
              <h3>Site loaded — ask me anything!</h3>
              <p>
                Try asking:<br />
                • "Give me all quotes by Mark Twain"<br />
                • "What products do they sell and at what price?"<br />
                • "List all team members and their roles"
              </p>
            </>
          ) : (
            <>
              <h3>Load a website to get started</h3>
            </>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="chat-window" id="chat-window">
      {messages.map((msg) => (
        <div
          key={msg.id}
          className={`chat-bubble${msg.role === 'user' ? ' user' : ''}`}
        >
          <div className={`chat-avatar ${msg.role === 'user' ? 'avatar-user' : 'avatar-ai'}`}>
            {msg.role === 'user' ? '👤' : '🤖'}
          </div>
          <div className={`chat-content${msg.role === 'user' ? ' user-msg' : ''}`}>
            <span dangerouslySetInnerHTML={{ __html: msg.content }} />
            {msg.data && msg.data.length > 0 && (
              <DataTable records={msg.data} />
            )}
          </div>
        </div>
      ))}

      {thinking && (
        <div className="thinking-bubble">
          <div className="chat-avatar avatar-ai">🤖</div>
          <div className="thinking-dots">
            <span /><span /><span />
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  )
}
