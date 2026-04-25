import { useState, useRef, useCallback } from 'react'

export default function ChatInput({ onSend, disabled, thinking }) {
  const [value, setValue] = useState('')
  const textareaRef = useRef(null)

  const handleSend = useCallback(() => {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }, [value, disabled, onSend])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleInput = (e) => {
    setValue(e.target.value)
    // Auto-resize textarea
    const ta = textareaRef.current
    if (ta) {
      ta.style.height = 'auto'
      ta.style.height = Math.min(ta.scrollHeight, 120) + 'px'
    }
  }

  const placeholder = disabled && !thinking
    ? 'Load a website first using the sidebar →'
    : thinking
      ? 'AI is thinking…'
      : 'Ask me anything'

  return (
    <div className="chat-input-bar">
      <div className={`chat-input-wrap${disabled ? ' disabled' : ''}`}>
        <textarea
          id="chat-input"
          ref={textareaRef}
          className="chat-text-input"
          placeholder={placeholder}
          value={value}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          rows={1}
        />
        <button
          id="chat-send-btn"
          className="chat-send-btn"
          onClick={handleSend}
          disabled={disabled || !value.trim()}
          title="Send (Enter)"
        >
          {thinking ? (
            <div className="spin" style={{ borderColor: 'rgba(255,255,255,0.3)', borderTopColor: 'white' }} />
          ) : (
            '↑'
          )}
        </button>
      </div>
    </div>
  )
}
