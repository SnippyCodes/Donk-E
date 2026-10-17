import React, { useRef } from 'react'
import { Send, Camera, Mic, MicOff } from 'lucide-react'

export interface GooeyInputProps {
  value: string
  onChange: (val: string) => void
  onSubmit: (e: React.FormEvent) => void
  onAttachClick?: () => void
  onToggleRecording?: () => void
  isRecording?: boolean
  isLoading?: boolean
  placeholder?: string
  className?: string
}

export const GooeyInput: React.FC<GooeyInputProps> = ({
  value,
  onChange,
  onSubmit,
  onAttachClick,
  onToggleRecording,
  isRecording = false,
  isLoading = false,
  placeholder = 'Ask about well status, downtime, spills, temperature trends, or SOP compliance...',
  className = '',
}) => {
  const inputRef = useRef<HTMLInputElement>(null)

  return (
    <div className={`gooey-input-wrapper ${className}`} style={{ width: '100%', position: 'relative' }}>
      {/* SVG Gooey Filter Definition */}
      <svg style={{ position: 'absolute', width: 0, height: 0, pointerEvents: 'none' }}>
        <defs>
          <filter id="gooey-filter">
            <feGaussianBlur in="SourceGraphic" stdDeviation="4" result="blur" />
            <feColorMatrix
              in="blur"
              mode="matrix"
              values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 18 -7"
              result="goo"
            />
            <feComposite in="SourceGraphic" in2="goo" operator="atop" />
          </filter>
        </defs>
      </svg>

      <form
        onSubmit={onSubmit}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-md)',
          padding: '6px 10px 6px 14px',
          transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
        }}
        onFocus={() => {
          const el = document.getElementById('gooey-input-container')
          if (el) el.style.borderColor = 'var(--border-active)'
        }}
        onBlur={() => {
          const el = document.getElementById('gooey-input-container')
          if (el) el.style.borderColor = 'var(--border-color)'
        }}
        id="gooey-input-container"
      >
        {/* Left Action Buttons (Upload & Voice) */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          {onAttachClick && (
            <button
              type="button"
              title="Attach Field Inspection Photo"
              onClick={onAttachClick}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                padding: '6px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                borderRadius: 'var(--radius-sm)',
                transition: 'color 0.15s ease, background-color 0.15s ease',
              }}
              onMouseEnter={e => {
                e.currentTarget.style.color = 'var(--text-primary)'
                e.currentTarget.style.backgroundColor = 'var(--bg-subtle)'
              }}
              onMouseLeave={e => {
                e.currentTarget.style.color = 'var(--text-muted)'
                e.currentTarget.style.backgroundColor = 'transparent'
              }}
            >
              <Camera size={16} />
            </button>
          )}

          {onToggleRecording && (
            <button
              type="button"
              title={isRecording ? 'Listening... click to stop' : 'Voice Query (Speech-to-Text)'}
              onClick={onToggleRecording}
              style={{
                background: isRecording ? 'var(--status-danger-bg)' : 'transparent',
                border: isRecording ? '1px solid var(--status-danger-border)' : 'none',
                color: isRecording ? 'var(--status-danger)' : 'var(--text-muted)',
                cursor: 'pointer',
                padding: '6px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                borderRadius: 'var(--radius-sm)',
                transition: 'all 0.15s ease',
              }}
              onMouseEnter={e => {
                if (!isRecording) {
                  e.currentTarget.style.color = 'var(--text-primary)'
                  e.currentTarget.style.backgroundColor = 'var(--bg-subtle)'
                }
              }}
              onMouseLeave={e => {
                if (!isRecording) {
                  e.currentTarget.style.color = 'var(--text-muted)'
                  e.currentTarget.style.backgroundColor = 'transparent'
                }
              }}
            >
              {isRecording ? <MicOff size={16} /> : <Mic size={16} />}
            </button>
          )}
        </div>

        {/* Input Text Field */}
        <input
          ref={inputRef}
          id="chat-input-box"
          type="text"
          value={value}
          onChange={e => onChange(e.target.value)}
          placeholder={isRecording ? 'Listening to voice...' : placeholder}
          disabled={isLoading}
          style={{
            flex: 1,
            background: 'transparent',
            border: 'none',
            outline: 'none',
            color: 'var(--text-primary)',
            fontFamily: 'var(--font-sans)',
            fontSize: '13px',
            lineHeight: 1.5,
          }}
        />

        {/* Submit Arrow Button */}
        <button
          id="chat-send-button"
          type="submit"
          disabled={!value.trim() || isLoading}
          style={{
            background: value.trim() && !isLoading ? 'var(--text-primary)' : 'var(--bg-subtle)',
            color: value.trim() && !isLoading ? 'var(--bg-canvas)' : 'var(--text-muted)',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-sm)',
            width: '30px',
            height: '30px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: value.trim() && !isLoading ? 'pointer' : 'not-allowed',
            transition: 'all 0.15s ease',
            flexShrink: 0,
          }}
        >
          <Send size={13} />
        </button>
      </form>
    </div>
  )
}
