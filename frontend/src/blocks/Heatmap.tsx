import React, { useState } from 'react'
import { Grid, ShieldCheck } from 'lucide-react'

export interface HeatmapProps {
  title: string
  x_labels: string[]
  y_labels: string[]
  matrix: number[][]
  totals?: Record<string, number>
  evidence_ids?: string[]
}

export const HeatmapBlock: React.FC<{ data: HeatmapProps }> = ({ data }) => {
  const [hoveredCell, setHoveredCell] = useState<{ y: string; x: string; val: number } | null>(null)
  const flatVals = data.matrix.flat()
  const maxVal = Math.max(...flatVals, 1)

  const getCellBg = (val: number) => {
    if (val === 0) return '#09090b'
    const intensity = Math.min(1, Math.max(0.15, val / maxVal))
    // Linear / Slate-amber industrial heat intensity
    const r = Math.round(245 * intensity)
    const g = Math.round(158 * intensity)
    const b = Math.round(11 * intensity)
    return `rgba(${r}, ${g}, ${b}, ${0.15 + intensity * 0.7})`
  }

  const getCellTextColor = (val: number) => {
    if (val === 0) return '#52525b'
    const intensity = val / maxVal
    return intensity > 0.6 ? '#09090b' : '#f4f4f5'
  }

  return (
    <div style={{
      background: '#121215',
      border: '1px solid rgba(39, 39, 42, 0.8)',
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
            background: '#18181b',
            border: '1px solid #27272a',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#f59e0b'
          }}>
            <Grid size={14} />
          </div>
          <span style={{ fontSize: '13px', fontWeight: 600, color: '#f4f4f5' }}>
            {data.title}
          </span>
        </div>

        {/* Legend & Hover Readout */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          fontSize: '11px',
          color: '#a1a1aa',
          fontFamily: "'JetBrains Mono', monospace"
        }}>
          {hoveredCell ? (
            <span style={{
              background: '#18181b',
              border: '1px solid #f59e0b',
              borderRadius: '4px',
              padding: '2px 8px',
              color: '#f59e0b',
              fontWeight: 600
            }}>
              {hoveredCell.y} · {hoveredCell.x}: <strong style={{ color: '#ffffff' }}>{hoveredCell.val} spills</strong>
            </span>
          ) : (
            <>
              <span>0 (Zero)</span>
              <div style={{
                width: '50px',
                height: '6px',
                borderRadius: '3px',
                background: 'linear-gradient(90deg, #18181b, rgba(245, 158, 11, 0.85))'
              }} />
              <span style={{ color: '#f59e0b', fontWeight: 600 }}>{maxVal} (Peak)</span>
            </>
          )}
        </div>
      </div>

      {/* Heatmap Matrix Table */}
      <div style={{
        overflowX: 'auto',
        border: '1px solid #27272a',
        borderRadius: '6px',
        background: '#09090b'
      }}>
        <table style={{
          width: '100%',
          borderCollapse: 'collapse',
          fontSize: '11.5px',
          fontFamily: "'JetBrains Mono', monospace"
        }}>
          <thead>
            <tr style={{ background: '#121215', borderBottom: '1px solid #27272a' }}>
              <th style={{
                padding: '8px 12px',
                textAlign: 'left',
                color: '#a1a1aa',
                fontWeight: 600,
                fontSize: '11px',
                textTransform: 'uppercase',
                letterSpacing: '0.4px'
              }}>
                Geographic Area
              </th>
              {data.x_labels.map(xl => (
                <th key={xl} style={{
                  padding: '8px 6px',
                  textAlign: 'center',
                  color: '#a1a1aa',
                  minWidth: '38px',
                  fontWeight: 600,
                  fontSize: '11px'
                }}>
                  {xl}
                </th>
              ))}
              {data.totals && (
                <th style={{
                  padding: '8px 12px',
                  textAlign: 'center',
                  color: '#f4f4f5',
                  fontWeight: 700,
                  fontSize: '11px',
                  textTransform: 'uppercase',
                  letterSpacing: '0.4px'
                }}>
                  Total
                </th>
              )}
            </tr>
          </thead>
          <tbody>
            {data.y_labels.map((yl, rIdx) => {
              const row = data.matrix[rIdx] || []
              const total = data.totals ? data.totals[yl] : row.reduce((a, b) => a + b, 0)
              return (
                <tr key={yl} style={{ borderBottom: '1px solid #1f1f23' }}>
                  <td style={{
                    padding: '8px 12px',
                    color: '#d4d4d8',
                    fontWeight: 600,
                    background: '#121215',
                    whiteSpace: 'nowrap'
                  }}>
                    {yl}
                  </td>
                  {row.map((val, cIdx) => {
                    const isHovered = hoveredCell?.y === yl && hoveredCell?.x === data.x_labels[cIdx]
                    return (
                      <td
                        key={cIdx}
                        style={{
                          padding: '4px',
                          textAlign: 'center',
                          background: '#09090b'
                        }}
                        onMouseEnter={() => setHoveredCell({ y: yl, x: data.x_labels[cIdx], val })}
                        onMouseLeave={() => setHoveredCell(null)}
                      >
                        <div style={{
                          background: getCellBg(val),
                          color: getCellTextColor(val),
                          borderRadius: '4px',
                          padding: '4px 2px',
                          fontWeight: val > 0 ? 700 : 400,
                          border: isHovered
                            ? '1px solid #ffffff'
                            : (val > 0 ? '1px solid rgba(245, 158, 11, 0.3)' : '1px solid #1f1f23'),
                          fontSize: '11px',
                          cursor: 'pointer',
                          transform: isHovered ? 'scale(1.15)' : 'scale(1)',
                          transition: 'all 0.12s ease',
                          boxShadow: isHovered ? '0 2px 8px rgba(0,0,0,0.8)' : 'none'
                        }} className="tabular-nums">
                          {val}
                        </div>
                      </td>
                    )
                  })}
                  {data.totals && (
                    <td style={{
                      padding: '8px 12px',
                      textAlign: 'center',
                      color: '#f4f4f5',
                      fontWeight: 700,
                      background: '#121215'
                    }} className="tabular-nums">
                      {total}
                    </td>
                  )}
                </tr>
              )
            })}
          </tbody>
        </table>
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
            Aggregated Sensor Evidence ({data.evidence_ids.length}):
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
