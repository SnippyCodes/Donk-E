import React from 'react'
import { Table as TableIcon, ShieldCheck } from 'lucide-react'

export interface TableBlockProps {
  title: string
  columns: Array<{ key: string; label: string } | string>
  rows: Array<Record<string, any>>
  summary_stats?: Record<string, any>
  evidence_ids?: string[]
}

export const TableBlock: React.FC<{ data: TableBlockProps }> = ({ data }) => {
  const normalizedColumns = (data.columns || []).map((col, idx) => {
    if (typeof col === 'string') {
      return { key: col, label: col }
    }
    return {
      key: col?.key || col?.label || `col_${idx}`,
      label: col?.label || col?.key || `Column ${idx + 1}`,
    }
  })

  const rows = data.rows || []

  return (
    <div className="visual-block-card table-block">
      <div className="visual-block-header">
        <div className="visual-block-title">
          <TableIcon size={18} color="#38bdf8" />
          <span>{data.title || 'Data Table'}</span>
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
              {normalizedColumns.map((col, cIdx) => (
                <th key={`${col.key}-${cIdx}`} style={{ padding: '10px 14px', fontWeight: 600 }}>
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={Math.max(normalizedColumns.length, 1)} style={{ padding: '16px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  No records found.
                </td>
              </tr>
            ) : (
              rows.map((row, idx) => (
                <tr
                  key={idx}
                  style={{
                    borderBottom: '1px solid rgba(255,255,255,0.04)',
                    transition: 'background 0.15s ease',
                    background: idx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.015)'
                  }}
                >
                  {normalizedColumns.map((col, cIdx) => {
                    const val = row[col.key] ?? row[col.label] ?? ''
                    const keyLower = (col.key || '').toLowerCase()
                    const isDelta = keyLower.includes('delta') || keyLower.includes('temp')
                    const isEvidence = keyLower.includes('evidence')

                    return (
                      <td key={`${col.key}-${cIdx}`} style={{ padding: '12px 14px', color: 'var(--text-primary)' }}>
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
                            {val >= 0 ? `+${val.toFixed(1)}°C` : `${val.toFixed(1)}°C`}
                          </span>
                        ) : (
                          <span>{val !== null && val !== undefined && val !== '' ? String(val) : '—'}</span>
                        )}
                      </td>
                    )
                  })}
                </tr>
              ))
            )}
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
