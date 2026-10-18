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
          background: '#fbfaf7',
          color: '#37322c',
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
            background: '#fffdfa',
            border: '1px solid #ded6c9',
            borderRadius: '6px',
            padding: '24px',
            boxShadow: '0 8px 24px rgba(68, 52, 35, 0.10)'
          }}>
            <h2 style={{ fontSize: '16px', fontWeight: 600, color: '#a94d46', marginBottom: '8px' }}>
              Operational Session Interrupted
            </h2>
            <p style={{ fontSize: '13px', color: '#71695e', marginBottom: '16px', lineHeight: 1.5 }}>
              A rendering exception was safely caught. Your local SQLite data and append-only ledger are pristine and unaffected.
            </p>
            {this.state.error && (
              <pre style={{
                background: '#f7f5f0',
                border: '1px solid #ded6c9',
                borderRadius: '4px',
                padding: '10px 12px',
                fontSize: '11px',
                fontFamily: 'JetBrains Mono, monospace',
                color: '#37322c',
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
                background: '#b85d3c',
                color: '#fbfaf7',
                border: '1px solid #b85d3c',
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
