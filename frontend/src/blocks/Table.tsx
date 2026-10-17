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
  const minTableWidth = Math.max(680, normalizedColumns.length * 140)

  const renderStatusBadge = (statusStr: string) => {
    const s = String(statusStr).toLowerCase()
    if (s.includes('breach') || s.includes('fail') || s.includes('uncontained') || s.includes('overdue')) {
      return (
        <span style={{
          display: 'inline-flex',
          alignItems: 'center',
          padding: '2px 7px',
          borderRadius: '4px',
          fontSize: '10.5px',
          fontFamily: "'JetBrains Mono', monospace",
          fontWeight: 600,
          background: 'rgba(244, 63, 94, 0.12)',
          color: '#f43f5e',
          border: '1px solid rgba(244, 63, 94, 0.28)',
          whiteSpace: 'nowrap'
        }}>
          {statusStr}
        </span>
      )
    }
    if (s.includes('met') || s.includes('pass') || s.includes('compliant') || s.includes('ok')) {
      return (
        <span style={{
          display: 'inline-flex',
          alignItems: 'center',
          padding: '2px 7px',
          borderRadius: '4px',
          fontSize: '10.5px',
          fontFamily: "'JetBrains Mono', monospace",
          fontWeight: 600,
          background: 'rgba(16, 185, 129, 0.12)',
          color: '#10b981',
          border: '1px solid rgba(16, 185, 129, 0.28)',
          whiteSpace: 'nowrap'
        }}>
          {statusStr}
        </span>
      )
    }
    if (s.includes('pending') || s.includes('action') || s.includes('open') || s.includes('warn') || s.includes('override')) {
      return (
        <span style={{
          display: 'inline-flex',
          alignItems: 'center',
          padding: '2px 7px',
          borderRadius: '4px',
          fontSize: '10.5px',
          fontFamily: "'JetBrains Mono', monospace",
          fontWeight: 600,
          background: 'rgba(245, 158, 11, 0.12)',
          color: '#f59e0b',
          border: '1px solid rgba(245, 158, 11, 0.28)',
          whiteSpace: 'nowrap'
        }}>
          {statusStr}
        </span>
      )
    }
    return (
      <span style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '1px 6px',
        borderRadius: '3px',
        fontSize: '11px',
        fontFamily: "'JetBrains Mono', monospace",
        background: '#18181b',
        border: '1px solid #27272a',
        color: '#e4e4e7',
        whiteSpace: 'nowrap'
      }}>
        {statusStr}
      </span>
    )
  }

  return (
    <div style={{
      background: '#121215',
      border: '1px solid rgba(39, 39, 42, 0.8)',
      boxShadow: 'inset 0 1px 0 0 rgba(255, 255, 255, 0.04), 0 2px 4px rgba(0, 0, 0, 0.4)',
      borderRadius: '8px',
      padding: '16px',
      margin: '10px 0',
      display: 'flex',
      flexDirection: 'column',
      gap: '12px',
      width: '100%',
      overflow: 'hidden'
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
            background: '#18181b',
            border: '1px solid #27272a',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#f4f4f5'
          }}>
            <TableIcon size={14} />
          </div>
          <div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: '#f4f4f5' }}>
              {data.title || 'Structured Intelligence Table'}
            </div>
            <div style={{ fontSize: '10.5px', color: '#71717a', fontFamily: "'JetBrains Mono', monospace" }}>
              Records: {rows.length} entries
            </div>
          </div>
        </div>

        {data.summary_stats && Object.keys(data.summary_stats).length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            {Object.entries(data.summary_stats).map(([k, v]) => (
              <span
                key={k}
                style={{
                  padding: '2px 8px',
                  borderRadius: '4px',
                  background: '#18181b',
                  border: '1px solid #27272a',
                  fontSize: '11px',
                  fontFamily: "'JetBrains Mono', monospace",
                  color: '#a1a1aa'
                }}
              >
                {k.replace(/_/g, ' ')}: <strong style={{ color: '#f4f4f5' }}>{String(v)}</strong>
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Horizontal Scrolling Table Container */}
      <div style={{
        overflowX: 'auto',
        borderRadius: '6px',
        border: '1px solid #27272a',
        background: '#09090b',
        width: '100%'
      }}>
        <table style={{
          width: '100%',
          minWidth: `${minTableWidth}px`,
          borderCollapse: 'collapse',
          fontSize: '12px',
          textAlign: 'left'
        }}>
          <thead>
            <tr style={{
              background: '#18181b',
              borderBottom: '1px solid #27272a',
              color: '#a1a1aa',
              fontSize: '10.5px',
              fontFamily: "'JetBrains Mono', monospace",
              textTransform: 'uppercase',
              letterSpacing: '0.4px',
              userSelect: 'none'
            }}>
              {normalizedColumns.map((col, cIdx) => (
                <th
                  key={`${col.key}-${cIdx}`}
                  style={{
                    padding: '8px 12px',
                    fontWeight: 600,
                    whiteSpace: 'nowrap',
                    borderRight: cIdx < normalizedColumns.length - 1 ? '1px solid #1f1f23' : 'none'
                  }}
                >
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td
                  colSpan={Math.max(normalizedColumns.length, 1)}
                  style={{
                    padding: '24px',
                    textAlign: 'center',
                    color: '#71717a',
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: '12px'
                  }}
                >
                  No records found in this operational query.
                </td>
              </tr>
            ) : (
              rows.map((row, idx) => (
                <tr
                  key={idx}
                  style={{
                    borderBottom: idx < rows.length - 1 ? '1px solid #1f1f23' : 'none',
                    background: idx % 2 === 1 ? 'rgba(255, 255, 255, 0.015)' : 'transparent',
                    transition: 'background 0.1s ease'
                  }}
                >
                  {normalizedColumns.map((col, cIdx) => {
                    const val = row[col.key] ?? row[col.label] ?? ''
                    const keyLower = (col.key || '').toLowerCase()
                    const isDelta = keyLower.includes('delta') || keyLower.includes('temp')
                    const isEvidence = keyLower.includes('evidence')
                    const isAsset = keyLower.includes('well') || keyLower.includes('asset') || keyLower.includes('id') || keyLower.includes('inspection')
                    const isStatus = keyLower.includes('status') || keyLower.includes('verdict') || keyLower.includes('type') || keyLower.includes('breach')
                    const isNumeric = typeof val === 'number'

                    return (
                      <td
                        key={`${col.key}-${cIdx}`}
                        style={{
                          padding: '8px 12px',
                          color: '#e4e4e7',
                          fontFamily: (isNumeric || isAsset || isDelta) ? "'JetBrains Mono', monospace" : "'Inter', sans-serif",
                          fontSize: (isNumeric || isAsset || isDelta) ? '11px' : '12px',
                          borderRight: cIdx < normalizedColumns.length - 1 ? '1px solid #1a1a1e' : 'none',
                          verticalAlign: 'middle',
                          whiteSpace: (isAsset || isNumeric || isStatus) ? 'nowrap' : 'normal',
                          lineHeight: 1.45
                        }}
                        className="tabular-nums"
                      >
                        {isEvidence && Array.isArray(val) ? (
                          <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                            {val.map((eid: string) => (
                              <span
                                key={eid}
                                style={{
                                  padding: '1px 5px',
                                  borderRadius: '3px',
                                  background: '#18181b',
                                  border: '1px solid #27272a',
                                  fontSize: '10px',
                                  fontFamily: "'JetBrains Mono', monospace",
                                  color: '#f59e0b',
                                  whiteSpace: 'nowrap'
                                }}
                              >
                                [{eid}]
                              </span>
                            ))}
                          </div>
                        ) : isDelta && typeof val === 'number' ? (
                          <span style={{
                            fontWeight: 600,
                            color: val < 15.0 ? '#f43f5e' : '#10b981',
                            whiteSpace: 'nowrap'
                          }}>
                            {val >= 0 ? `+${val.toFixed(1)}°C` : `${val.toFixed(1)}°C`}
                          </span>
                        ) : isStatus && typeof val === 'string' && val.length < 30 ? (
                          renderStatusBadge(val)
                        ) : (
                          <span>
                            {val === null || val === undefined || val === ''
                              ? '—'
                              : typeof val === 'object'
                              ? JSON.stringify(val)
                              : String(val)}
                          </span>
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

      {/* Verified Citations Footer */}
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
            Verified Citations ({data.evidence_ids.length}):
          </span>
          {data.evidence_ids.map(eid => (
            <span
              key={eid}
              style={{
                fontSize: '10.5px',
                fontFamily: "'JetBrains Mono', monospace",
                padding: '1px 5px',
                borderRadius: '3px',
                background: '#18181b',
                border: '1px solid #27272a',
                color: '#d4d4d8',
                whiteSpace: 'nowrap'
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
