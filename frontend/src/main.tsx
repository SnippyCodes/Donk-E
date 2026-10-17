import React from 'react'
import ReactDOM from 'react-dom/client'
import { App } from './App'
import './index.css'

class AppErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('App-level error caught by ErrorBoundary:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '100vh',
          background: '#0d1117',
          color: '#f0f6fc',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '24px',
          fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
        }}>
          <div style={{
            maxWidth: '560px',
            width: '100%',
            background: '#161b22',
            border: '1px solid #30363d',
            borderRadius: '6px',
            padding: '24px',
            boxShadow: '0 8px 24px rgba(0,0,0,0.6)'
          }}>
            <h2 style={{ fontSize: '16px', fontWeight: 600, color: '#f85149', marginBottom: '8px' }}>
              Operational Session Interrupted
            </h2>
            <p style={{ fontSize: '13px', color: '#8b949e', marginBottom: '16px', lineHeight: 1.5 }}>
              A rendering exception was safely caught. Your local SQLite data and append-only ledger are pristine and unaffected.
            </p>
            {this.state.error && (
              <pre style={{
                background: '#010409',
                border: '1px solid #21262d',
                borderRadius: '4px',
                padding: '10px 12px',
                fontSize: '11px',
                fontFamily: 'JetBrains Mono, monospace',
                color: '#f0f6fc',
                overflowX: 'auto',
                marginBottom: '16px'
              }}>
                {this.state.error.message}
              </pre>
            )}
            <button
              onClick={() => {
                this.setState({ hasError: false, error: null })
                window.location.reload()
              }}
              style={{
                background: '#f0f6fc',
                color: '#0d1117',
                border: '1px solid #f0f6fc',
                borderRadius: '4px',
                padding: '6px 14px',
                fontSize: '12px',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              Reload Operational Session
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AppErrorBoundary>
      <App />
    </AppErrorBoundary>
  </React.StrictMode>,
)
