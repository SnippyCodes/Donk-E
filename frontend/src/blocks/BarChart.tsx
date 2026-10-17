import React from 'react'
import { BarChart3, ShieldCheck } from 'lucide-react'

export interface BarChartProps {
  title: string
  categories: string[]
  values: number[]
  unit: string
  evidence_ids?: string[]
}

export const BarChartBlock: React.FC<{ data: BarChartProps }> = ({ data }) => {
  const maxVal = Math.max(...data.values, 1)

  return (
    <div className="visual-block-card bar-chart-block">
      <div className="visual-block-header">
        <div className="visual-block-title">
          <BarChart3 size={18} color="#38bdf8" />
          <span>{data.title}</span>
        </div>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
          Unit: <strong style={{ color: '#38bdf8' }}>{data.unit}</strong>
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '10px' }}>
        {data.categories.map((cat, idx) => {
          const val = data.values[idx] || 0
          const pct = Math.min(100, Math.max(5, (val / maxVal) * 100))
          return (
            <div key={cat} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{
                width: '90px',
                fontSize: '12px',
                fontFamily: 'var(--font-mono)',
                color: 'var(--text-secondary)',
                textAlign: 'right',
                flexShrink: 0
              }}>
                {cat}
              </div>
              <div style={{
                flex: 1,
                background: 'rgba(255,255,255,0.04)',
                borderRadius: '6px',
                height: '24px',
                overflow: 'hidden',
                position: 'relative'
              }}>
                <div style={{
                  width: `${pct}%`,
                  height: '100%',
                  background: 'linear-gradient(90deg, #0284c7, #38bdf8)',
                  borderRadius: '6px',
                  transition: 'width 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'flex-end',
                  paddingRight: '8px'
                }}>
                  <span style={{
                    fontSize: '11px',
                    fontWeight: 700,
                    color: '#032030',
                    fontFamily: 'var(--font-mono)'
                  }}>
                    {val} {data.unit}
                  </span>
                </div>
              </div>
            </div>
          )
        })}
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
