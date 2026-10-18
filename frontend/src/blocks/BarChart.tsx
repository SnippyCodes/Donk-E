import React, { useState } from 'react'
import { BarChart3, ShieldCheck } from 'lucide-react'

export interface BarChartProps {
  title: string
  categories: string[]
  values: number[]
  unit: string
  evidence_ids?: string[]
}

export const BarChartBlock: React.FC<{ data: BarChartProps }> = ({ data }) => {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null)
  const maxVal = Math.max(...data.values, 1)

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
            <BarChart3 size={14} />
          </div>
          <span style={{ fontSize: '13px', fontWeight: 600, color: '#28231e' }}>
            {data.title}
          </span>
        </div>

        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          padding: '2px 8px',
          borderRadius: '4px',
          background: '#f0ebe3',
          border: '1px solid #ded6c9',
          fontSize: '11px',
          fontFamily: "'JetBrains Mono', monospace",
          color: '#71695e'
        }}>
          Metric Unit: <strong style={{ color: '#28231e' }}>{data.unit}</strong>
        </div>
      </div>

      {/* Aligned Interactive Bar Rows */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '4px' }}>
        {data.categories.map((cat, idx) => {
          const val = data.values[idx] || 0
          const pct = Math.min(100, Math.max(6, (val / maxVal) * 100))
          const isHovered = hoveredIdx === idx

          return (
            <div
              key={cat}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                cursor: 'pointer',
                padding: '2px 4px',
                borderRadius: '4px',
                background: isHovered ? 'rgba(255, 255, 255, 0.02)' : 'transparent',
                transition: 'all 0.15s ease'
              }}
              onMouseEnter={() => setHoveredIdx(idx)}
              onMouseLeave={() => setHoveredIdx(null)}
            >
              <div style={{
                width: '130px',
                fontSize: '11.5px',
                fontFamily: "'JetBrains Mono', monospace",
                color: isHovered ? '#b85d3c' : '#3f3932',
                fontWeight: isHovered ? 600 : 400,
                textAlign: 'right',
                flexShrink: 0,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap'
              }} title={cat}>
                {cat}
              </div>
              <div style={{
                flex: 1,
                background: '#f7f5f0',
                border: isHovered ? '1px solid #b85d3c' : '1px solid #ded6c9',
                borderRadius: '5px',
                height: '26px',
                overflow: 'hidden',
                position: 'relative',
                transition: 'border-color 0.15s ease'
              }}>
                <div style={{
                  width: `${pct}%`,
                  height: '100%',
                  background: isHovered ? '#b85d3c' : (idx === 0 ? '#a64e33' : '#c6bbaa'),
                  borderRadius: '3px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'flex-end',
                  paddingRight: '8px',
                  transition: 'all 0.25s ease'
                }}>
                  <span style={{
                    fontSize: '11px',
                    fontWeight: 700,
                    color: isHovered || idx === 0 ? '#f7f5f0' : '#28231e',
                    fontFamily: "'JetBrains Mono', monospace"
                  }} className="tabular-nums">
                    {val} {data.unit}
                  </span>
                </div>
              </div>
            </div>
          )
        })}
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
            Verified Evidence ({data.evidence_ids.length}):
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
