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
    if (val === 0) return '#f7f5f0'
    const intensity = Math.min(1, Math.max(0.15, val / maxVal))
    // Linear / Slate-amber industrial heat intensity
    const r = Math.round(245 * intensity)
    const g = Math.round(158 * intensity)
    const b = Math.round(11 * intensity)
    return `rgba(${r}, ${g}, ${b}, ${0.15 + intensity * 0.7})`
  }

  const getCellTextColor = (val: number) => {
    if (val === 0) return '#857b6e'
    const intensity = val / maxVal
    return intensity > 0.6 ? '#f7f5f0' : '#28231e'
  }

  return (
    <div style={{
      background: '#fffdfa',
      border: '1px solid rgba(222, 214, 201, 0.8)',
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
            background: '#f0ebe3',
            border: '1px solid #ded6c9',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#b85d3c'
          }}>
            <Grid size={14} />
          </div>
          <span style={{ fontSize: '13px', fontWeight: 600, color: '#28231e' }}>
            {data.title}
          </span>
        </div>

        {/* Legend & Hover Readout */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          fontSize: '11px',
          color: '#71695e',
          fontFamily: "'JetBrains Mono', monospace"
        }}>
          {hoveredCell ? (
            <span style={{
              background: '#f0ebe3',
              border: '1px solid #b85d3c',
              borderRadius: '4px',
              padding: '2px 8px',
              color: '#b85d3c',
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
                background: '#b85d3c'
              }} />
              <span style={{ color: '#b85d3c', fontWeight: 600 }}>{maxVal} (Peak)</span>
            </>
          )}
        </div>
      </div>

      {/* Heatmap Matrix Table */}
      <div style={{
        overflowX: 'auto',
        border: '1px solid #ded6c9',
        borderRadius: '6px',
        background: '#f7f5f0'
      }}>
        <table style={{
          width: '100%',
          borderCollapse: 'collapse',
          fontSize: '11.5px',
          fontFamily: "'JetBrains Mono', monospace"
        }}>
          <thead>
            <tr style={{ background: '#fffdfa', borderBottom: '1px solid #ded6c9' }}>
              <th style={{
                padding: '8px 12px',
                textAlign: 'left',
                color: '#71695e',
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
                  color: '#71695e',
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
                  color: '#28231e',
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
                <tr key={yl} style={{ borderBottom: '1px solid #e8e0d4' }}>
                  <td style={{
                    padding: '8px 12px',
                    color: '#3f3932',
                    fontWeight: 600,
                    background: '#fffdfa',
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
                          background: '#f7f5f0'
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
                            : (val > 0 ? '1px solid rgba(184, 93, 60, 0.3)' : '1px solid #e8e0d4'),
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
                      color: '#28231e',
                      fontWeight: 700,
                      background: '#fffdfa'
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
          borderTop: '1px solid #e8e0d4'
        }}>
          <ShieldCheck size={13} color="#7a7268" style={{ flexShrink: 0 }} />
          <span style={{ fontSize: '11px', color: '#7a7268', fontFamily: "'JetBrains Mono', monospace" }}>
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
