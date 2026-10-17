import React from 'react'
import { AlertOctagon, HelpCircle, ShieldCheck, GitCompare, User } from 'lucide-react'

export interface ConflictBlockProps {
  title: string
  asset_id: string
  item: string
  claims: Array<{
    source: string
    statement: string
    timestamp?: string
    evidence_id?: string
  }>
  recommendation: string
  evidence_ids: string[]
}

export const ConflictBlock: React.FC<{ data: ConflictBlockProps }> = ({ data }) => {
  return (
    <div style={{
      background: '#121215',
      border: '1px solid rgba(39, 39, 42, 0.8)',
      borderLeft: '3px solid #f59e0b',
      boxShadow: 'inset 0 1px 0 0 rgba(255, 255, 255, 0.04), 0 1px 3px rgba(0, 0, 0, 0.5)',
      borderRadius: '8px',
      padding: '16px',
      margin: '8px 0',
      display: 'flex',
      flexDirection: 'column',
      gap: '12px'
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '8px',
        paddingBottom: '10px',
        borderBottom: '1px solid #1f1f23'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{
            width: '24px',
            height: '24px',
            borderRadius: '6px',
            background: 'rgba(245, 158, 11, 0.1)',
            border: '1px solid rgba(245, 158, 11, 0.25)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#f59e0b'
          }}>
            <AlertOctagon size={14} />
          </div>
          <span style={{ fontSize: '13px', fontWeight: 600, color: '#f4f4f5' }}>
            {data.title} <span style={{ fontFamily: "'JetBrains Mono', monospace", color: '#f59e0b' }}>({data.asset_id})</span>
          </span>
        </div>

        <span style={{
          fontSize: '11px',
          fontFamily: "'JetBrains Mono', monospace",
          padding: '2px 8px',
          borderRadius: '4px',
          background: 'rgba(245, 158, 11, 0.1)',
          color: '#f59e0b',
          fontWeight: 600,
          border: '1px solid rgba(245, 158, 11, 0.25)',
          display: 'inline-flex',
          alignItems: 'center',
          gap: '5px'
        }}>
          <GitCompare size={12} />
          CONFLICT DETECTED
        </span>
      </div>

      <div style={{ fontSize: '12px', color: '#a1a1aa' }}>
        Disputed Field Item / Parameter: <strong style={{ color: '#f4f4f5', fontFamily: "'JetBrains Mono', monospace" }}>{data.item}</strong>
      </div>

      {/* Disputing Claims Comparison Grid (Layer 1 vs Layer 2) */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '10px',
      }}>
        {data.claims.map((claim, idx) => (
          <div
            key={idx}
            style={{
              background: '#09090b',
              border: '1px solid #27272a',
              borderRadius: '6px',
              padding: '12px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              gap: '8px'
            }}
          >
            <div>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '6px',
                borderBottom: '1px solid #1f1f23',
                paddingBottom: '4px'
              }}>
                <span style={{
                  fontSize: '10.5px',
                  fontWeight: 600,
                  color: '#71717a',
                  textTransform: 'uppercase',
                  letterSpacing: '0.4px',
                  fontFamily: "'JetBrains Mono', monospace"
                }}>
                  {idx === 0 ? 'Layer 1: Empirical Sensor / Ingest' : 'Layer 2: Runtime Ledger Override'}
                </span>
                {claim.evidence_id && (
                  <span style={{
                    fontSize: '10px',
                    fontFamily: "'JetBrains Mono', monospace",
                    padding: '1px 5px',
                    borderRadius: '3px',
                    background: '#18181b',
                    border: '1px solid #27272a',
                    color: '#d4d4d8'
                  }}>
                    [{claim.evidence_id}]
                  </span>
                )}
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '5px', marginBottom: '6px' }}>
                <User size={12} color="#a1a1aa" />
                <strong style={{ fontSize: '12px', color: '#f4f4f5' }}>{claim.source}</strong>
              </div>

              <div style={{
                fontSize: '12px',
                color: '#d4d4d8',
                lineHeight: 1.5,
                background: '#121215',
                padding: '8px 10px',
                borderRadius: '5px',
                border: '1px solid #1f1f23',
                fontStyle: 'italic'
              }}>
                "{claim.statement}"
              </div>
            </div>

            {claim.timestamp && (
              <div style={{
                fontSize: '10px',
                color: '#71717a',
                fontFamily: "'JetBrains Mono', monospace"
              }}>
                Recorded: {claim.timestamp} UTC
              </div>
            )}
          </div>
        ))}
      </div>

      {/* System Recommendation Protocol */}
      <div style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: '10px',
        padding: '10px 12px',
        background: '#09090b',
        border: '1px solid #27272a',
        borderRadius: '6px',
        fontSize: '12px',
        color: '#a1a1aa'
      }}>
        <HelpCircle size={15} style={{ flexShrink: 0, marginTop: '2px', color: '#f59e0b' }} />
        <div>
          <strong style={{ color: '#f4f4f5' }}>Industrial Protocol:</strong> {data.recommendation}
        </div>
      </div>

      {/* Verified Evidence Footer */}
      {data.evidence_ids && data.evidence_ids.length > 0 && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          flexWrap: 'wrap',
          paddingTop: '6px',
          borderTop: '1px solid #1f1f23'
        }}>
          <ShieldCheck size={13} color="#71717a" style={{ flexShrink: 0 }} />
          <span style={{ fontSize: '11px', color: '#71717a', fontFamily: "'JetBrains Mono', monospace" }}>
            Audit Evidence ({data.evidence_ids.length}):
          </span>
          {data.evidence_ids.map(eid => (
            <span
              key={eid}
              style={{
                fontSize: '11px',
                fontFamily: "'JetBrains Mono', monospace",
                padding: '1px 6px',
                borderRadius: '4px',
                background: '#18181b',
                border: '1px solid #27272a',
                color: '#d4d4d8'
              }}
            >
              [{eid}]
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
