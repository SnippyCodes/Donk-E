import React from 'react'
import { Table as TableIcon, ShieldCheck } from 'lucide-react'

export interface TableBlockProps {
  title: string
  columns: Array<{ key: string; label: string }>
  rows: Array<Record<string, any>>
  summary_stats?: Record<string, any>
  evidence_ids?: string[]
}

export const TableBlock: React.FC<{ data: TableBlockProps }> = ({ data }) => {
  return (
    <div className="visual-block-card table-block">
      <div className="visual-block-header">
        <div className="visual-block-title">
          <TableIcon size={18} color="#38bdf8" />
          <span>{data.title}</span>
        </div>
        {data.summary_stats && Object.keys(data.summary_stats).length > 0 && (
          <div style={{ display: 'flex', gap: '12px', fontSize: '12px' }}>
            {Object.entries(data.summary_stats).map(([k, v]) => (
              <span key={k} style={{ color: 'var(--text-muted)' }}>
                {k.replace(/_/g, ' ')}: <strong style={{ color: '#38bdf8' }}>{String(v)}</strong>
              </span>
            ))}
          </div>
        )}
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table style={{
          width: '100%',
          borderCollapse: 'collapse',
          fontSize: '13px',
          textAlign: 'left'
        }}>
          <thead>
            <tr style={{
              background: 'rgba(0,0,0,0.3)',
              borderBottom: '1px solid var(--border-subtle)',
              color: 'var(--text-muted)',
              fontSize: '11px',
              textTransform: 'uppercase',
              letterSpacing: '0.5px'
            }}>
              {data.columns.map(col => (
                <th key={col.key} style={{ padding: '10px 14px', fontWeight: 600 }}>
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.rows.map((row, idx) => (
              <tr
                key={idx}
                style={{
                  borderBottom: '1px solid rgba(255,255,255,0.04)',
                  transition: 'background 0.15s ease',
                  background: idx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.015)'
                }}
              >
                {data.columns.map(col => {
                  const val = row[col.key]
                  const isDelta = col.key.includes('delta') || col.key.includes('temp')
                  const isEvidence = col.key === 'evidence' || col.key === 'evidence_ids'
                  return (
                    <td key={col.key} style={{ padding: '12px 14px', color: 'var(--text-primary)' }}>
                      {isEvidence && Array.isArray(val) ? (
                        <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                          {val.map((eid: string) => (
                            <span key={eid} className="citation-badge">[{eid}]</span>
                          ))}
                        </div>
                      ) : isDelta && typeof val === 'number' ? (
                        <span style={{
                          fontFamily: 'var(--font-mono)',
                          color: val < 15.0 ? '#f87171' : '#34d399',
                          fontWeight: 600
                        }}>
                          +{val.toFixed(1)}°C
                        </span>
                      ) : (
                        <span>{val !== null && val !== undefined ? String(val) : '—'}</span>
                      )}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {data.evidence_ids && data.evidence_ids.length > 0 && (
        <div style={{ marginTop: '14px', display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
          <ShieldCheck size={14} color="#38bdf8" />
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Verified Evidence:</span>
          {data.evidence_ids.map(eid => (
            <span key={eid} className="citation-badge">[{eid}]</span>
          ))}
        </div>
      )}
    </div>
  )
}
