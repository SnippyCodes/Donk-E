import React from 'react'
import { AlertOctagon, HelpCircle, ShieldCheck } from 'lucide-react'

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
    <div className="visual-block-card conflict-block" style={{ borderLeft: '4px solid #f59e0b' }}>
      <div className="visual-block-header">
        <div className="visual-block-title" style={{ color: '#fbbf24' }}>
          <AlertOctagon size={18} color="#f59e0b" />
          <span>{data.title} ({data.asset_id})</span>
        </div>
        <span style={{
          fontSize: '11px',
          padding: '2px 8px',
          borderRadius: '12px',
          background: 'rgba(245, 158, 11, 0.15)',
          color: '#fbbf24',
          fontWeight: 600,
          border: '1px solid rgba(245, 158, 11, 0.3)'
        }}>
          CONFLICT DETECTED
        </span>
      </div>

      <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '14px' }}>
        Disputed Field Item: <strong style={{ color: '#f8fafc' }}>{data.item}</strong>
      </div>

      {/* Disputing Claims Comparison Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '12px',
        marginBottom: '16px'
      }}>
        {data.claims.map((claim, idx) => (
          <div
            key={idx}
            style={{
              background: 'rgba(0, 0, 0, 0.3)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '8px',
              padding: '12px 14px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              gap: '8px'
            }}
          >
            <div>
              <div style={{ fontSize: '12px', fontWeight: 600, color: '#38bdf8', marginBottom: '4px' }}>
                Claim {idx + 1}: {claim.source}
              </div>
              <div style={{ fontSize: '13px', color: '#e2e8f0', lineHeight: 1.5 }}>
                "{claim.statement}"
              </div>
            </div>
            {claim.timestamp && (
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                Recorded: {claim.timestamp}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* System Recommendation */}
      <div style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: '8px',
        padding: '10px 14px',
        background: 'rgba(56, 189, 248, 0.08)',
        border: '1px solid rgba(56, 189, 248, 0.2)',
        borderRadius: '8px',
        fontSize: '12px',
        color: '#bae6fd'
      }}>
        <HelpCircle size={15} style={{ flexShrink: 0, marginTop: '2px' }} />
        <div>
          <strong>System Protocol:</strong> {data.recommendation}
        </div>
      </div>

      {/* Evidence Chips */}
      {data.evidence_ids && data.evidence_ids.length > 0 && (
        <div style={{ marginTop: '14px', display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
          <ShieldCheck size={14} color="#38bdf8" />
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Disputed Evidence:</span>
          {data.evidence_ids.map(eid => (
            <span key={eid} className="citation-badge">[{eid}]</span>
          ))}
        </div>
      )}
    </div>
  )
}
