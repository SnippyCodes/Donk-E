import React from 'react'
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
  const flatVals = data.matrix.flat()
  const maxVal = Math.max(...flatVals, 1)

  const getColor = (val: number) => {
    if (val === 0) return 'rgba(255, 255, 255, 0.02)'
    const intensity = Math.min(1, Math.max(0.15, val / maxVal))
    return `rgba(56, 189, 248, ${intensity})`
  }

  return (
    <div className="visual-block-card heatmap-block">
      <div className="visual-block-header">
        <div className="visual-block-title">
          <Grid size={18} color="#38bdf8" />
          <span>{data.title}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '11px', color: 'var(--text-muted)' }}>
          <span>Low</span>
          <div style={{ width: '40px', height: '8px', borderRadius: '4px', background: 'linear-gradient(90deg, rgba(56,189,248,0.1), #38bdf8)' }} />
          <span>High ({maxVal})</span>
        </div>
      </div>

      <div style={{ overflowX: 'auto', padding: '6px 0' }}>
        <table style={{ borderCollapse: 'collapse', fontSize: '11px', fontFamily: 'var(--font-mono)' }}>
          <thead>
            <tr>
              <th style={{ padding: '6px 12px', textAlign: 'left', color: 'var(--text-muted)' }}>Area</th>
              {data.x_labels.map(xl => (
                <th key={xl} style={{ padding: '6px 8px', textAlign: 'center', color: 'var(--text-muted)', minWidth: '38px' }}>
                  {xl}
                </th>
              ))}
              {data.totals && (
                <th style={{ padding: '6px 10px', textAlign: 'center', color: '#38bdf8' }}>Total</th>
              )}
            </tr>
          </thead>
          <tbody>
            {data.y_labels.map((yl, rIdx) => {
              const row = data.matrix[rIdx] || []
              const total = data.totals ? data.totals[yl] : row.reduce((a, b) => a + b, 0)
              return (
                <tr key={yl}>
                  <td style={{ padding: '6px 12px', color: 'var(--text-secondary)', fontWeight: 600 }}>{yl}</td>
                  {row.map((val, cIdx) => (
                    <td
                      key={cIdx}
                      style={{
                        padding: '4px',
                        textAlign: 'center',
                      }}
                    >
                      <div style={{
                        background: getColor(val),
                        borderRadius: '4px',
                        padding: '6px 4px',
                        color: val > 0 ? (val / maxVal > 0.5 ? '#032030' : '#f8fafc') : '#475569',
                        fontWeight: val > 0 ? 700 : 400,
                        border: val > 0 ? '1px solid rgba(56, 189, 248, 0.3)' : '1px solid rgba(255,255,255,0.03)'
                      }}>
                        {val}
                      </div>
                    </td>
                  ))}
                  {data.totals && (
                    <td style={{ padding: '6px 10px', textAlign: 'center', color: '#38bdf8', fontWeight: 700 }}>
                      {total}
                    </td>
                  )}
                </tr>
              )
            })}
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
