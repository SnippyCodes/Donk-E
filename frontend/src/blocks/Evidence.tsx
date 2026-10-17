import React from 'react'
import { BookOpen, FileText, ShieldCheck, ExternalLink } from 'lucide-react'

export interface EvidenceBlockProps {
  title: string
  evidence_items: Array<{
    id: string
    title: string
    snippet?: string
    source?: string
  }>
  evidence_ids: string[]
}

export const EvidenceBlock: React.FC<{ data: EvidenceBlockProps }> = ({ data }) => {
  return (
    <div className="visual-block-card evidence-block">
      <div className="visual-block-header">
        <div className="visual-block-title">
          <BookOpen size={18} color="#38bdf8" />
          <span>{data.title}</span>
        </div>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
          {data.evidence_items.length} Grounded References
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {data.evidence_items.map((item, idx) => (
          <div
            key={idx}
            style={{
              background: 'rgba(0, 0, 0, 0.25)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '8px',
              padding: '12px 14px',
              transition: 'border-color 0.2s ease',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <FileText size={15} color="#38bdf8" />
                <strong style={{ fontSize: '13px', color: '#f8fafc' }}>{item.title}</strong>
              </div>
              <span className="citation-badge">[{item.id}]</span>
            </div>

            {item.snippet && (
              <div style={{
                fontSize: '12px',
                color: 'var(--text-secondary)',
                lineHeight: 1.5,
                background: 'rgba(255, 255, 255, 0.02)',
                padding: '8px 10px',
                borderRadius: '6px',
                borderLeft: '2px solid #38bdf8'
              }}>
                {item.snippet}
              </div>
            )}

            {item.source && (
              <div style={{
                marginTop: '6px',
                fontSize: '10px',
                color: 'var(--text-muted)',
                fontFamily: 'var(--font-mono)',
                display: 'flex',
                alignItems: 'center',
                gap: '4px'
              }}>
                <ExternalLink size={11} />
                <span>Source: {item.source}</span>
              </div>
            )}
          </div>
        ))}
      </div>

      {data.evidence_ids && data.evidence_ids.length > 0 && (
        <div style={{ marginTop: '14px', display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
          <ShieldCheck size={14} color="#38bdf8" />
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Citation Index:</span>
          {data.evidence_ids.map(eid => (
            <span key={eid} className="citation-badge">[{eid}]</span>
          ))}
        </div>
      )}
    </div>
  )
}
