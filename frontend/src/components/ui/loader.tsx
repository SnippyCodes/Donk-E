import React from 'react'

export interface LoaderOneProps {
  className?: string
  text?: string
}

export const LoaderOne: React.FC<LoaderOneProps> = ({
  className = '',
  text = 'Consulting deterministic data layer, rules.yaml & Gemma 4 engine...',
}) => {
  return (
    <div
      className={`loader-one-container ${className}`}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        padding: '10px 14px',
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-color)',
        borderRadius: 'var(--radius-md)',
        width: 'fit-content',
        color: 'var(--text-secondary)',
        fontFamily: 'var(--font-mono)',
        fontSize: '12px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
        <span
          className="loader-dot"
          style={{
            width: '7px',
            height: '7px',
            borderRadius: '50%',
            background: 'var(--text-primary)',
            animation: 'loaderDotPulse 1.2s ease-in-out infinite',
            animationDelay: '0s',
          }}
        />
        <span
          className="loader-dot"
          style={{
            width: '7px',
            height: '7px',
            borderRadius: '50%',
            background: 'var(--text-secondary)',
            animation: 'loaderDotPulse 1.2s ease-in-out infinite',
            animationDelay: '0.2s',
          }}
        />
        <span
          className="loader-dot"
          style={{
            width: '7px',
            height: '7px',
            borderRadius: '50%',
            background: 'var(--text-muted)',
            animation: 'loaderDotPulse 1.2s ease-in-out infinite',
            animationDelay: '0.4s',
          }}
        />
      </div>
      <span style={{ letterSpacing: '0.2px' }}>{text}</span>
    </div>
  )
}
