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
      background: '#fffdfa',
      border: '1px solid rgba(222, 214, 201, 0.8)',
      borderLeft: '3px solid #b85d3c',
      boxShadow: 'inset 0 1px 0 0 rgba(255, 255, 255, 0.04), 0 1px 3px rgba(68, 52, 35, 0.10)',
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
        borderBottom: '1px solid #e8e0d4'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{
            width: '24px',
            height: '24px',
            borderRadius: '6px',
            background: 'rgba(184, 93, 60, 0.1)',
            border: '1px solid rgba(184, 93, 60, 0.25)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#b85d3c'
          }}>
            <AlertOctagon size={14} />
          </div>
          <span style={{ fontSize: '13px', fontWeight: 600, color: '#28231e' }}>
            {data.title} <span style={{ fontFamily: "'JetBrains Mono', monospace", color: '#b85d3c' }}>({data.asset_id})</span>
          </span>
        </div>

        <span style={{
          fontSize: '11px',
          fontFamily: "'JetBrains Mono', monospace",
          padding: '2px 8px',
          borderRadius: '4px',
          background: 'rgba(184, 93, 60, 0.1)',
          color: '#b85d3c',
          fontWeight: 600,
          border: '1px solid rgba(184, 93, 60, 0.25)',
          display: 'inline-flex',
          alignItems: 'center',
          gap: '5px'
        }}>
          <GitCompare size={12} />
          CONFLICT DETECTED
        </span>
      </div>

      <div style={{ fontSize: '12px', color: '#71695e' }}>
        Disputed Field Item / Parameter: <strong style={{ color: '#28231e', fontFamily: "'JetBrains Mono', monospace" }}>{data.item}</strong>
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
              background: '#f7f5f0',
              border: '1px solid #ded6c9',
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
                borderBottom: '1px solid #e8e0d4',
                paddingBottom: '4px'
              }}>
                <span style={{
                  fontSize: '10.5px',
                  fontWeight: 600,
                  color: '#7a7268',
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
                    background: '#f0ebe3',
                    border: '1px solid #ded6c9',
                    color: '#3f3932'
                  }}>
                    [{claim.evidence_id}]
                  </span>
                )}
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '5px', marginBottom: '6px' }}>
                <User size={12} color="#71695e" />
                <strong style={{ fontSize: '12px', color: '#28231e' }}>{claim.source}</strong>
              </div>

              <div style={{
                fontSize: '12px',
                color: '#3f3932',
                lineHeight: 1.5,
                background: '#fffdfa',
                padding: '8px 10px',
                borderRadius: '5px',
                border: '1px solid #e8e0d4',
                fontStyle: 'italic'
              }}>
                "{claim.statement}"
              </div>
            </div>

            {claim.timestamp && (
              <div style={{
                fontSize: '10px',
                color: '#7a7268',
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
        background: '#f7f5f0',
        border: '1px solid #ded6c9',
        borderRadius: '6px',
        fontSize: '12px',
        color: '#71695e'
      }}>
        <HelpCircle size={15} style={{ flexShrink: 0, marginTop: '2px', color: '#b85d3c' }} />
        <div>
          <strong style={{ color: '#28231e' }}>Industrial Protocol:</strong> {data.recommendation}
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
          borderTop: '1px solid #e8e0d4'
        }}>
          <ShieldCheck size={13} color="#7a7268" style={{ flexShrink: 0 }} />
          <span style={{ fontSize: '11px', color: '#7a7268', fontFamily: "'JetBrains Mono', monospace" }}>
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
                background: '#f0ebe3',
                border: '1px solid #ded6c9',
                color: '#3f3932'
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
