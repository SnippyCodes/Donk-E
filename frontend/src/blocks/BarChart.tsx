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
            <BarChart3 size={14} />
          </div>
          <span style={{ fontSize: '13px', fontWeight: 600, color: '#f4f4f5' }}>
            {data.title}
          </span>
        </div>

        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          padding: '2px 8px',
          borderRadius: '4px',
          background: '#18181b',
          border: '1px solid #27272a',
          fontSize: '11px',
          fontFamily: "'JetBrains Mono', monospace",
          color: '#a1a1aa'
        }}>
          Metric Unit: <strong style={{ color: '#f4f4f5' }}>{data.unit}</strong>
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
                color: isHovered ? '#f59e0b' : '#d4d4d8',
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
                background: '#09090b',
                border: isHovered ? '1px solid #f59e0b' : '1px solid #27272a',
                borderRadius: '5px',
                height: '26px',
                overflow: 'hidden',
                position: 'relative',
                transition: 'border-color 0.15s ease'
              }}>
                <div style={{
                  width: `${pct}%`,
                  height: '100%',
                  background: isHovered ? '#f59e0b' : (idx === 0 ? '#d97706' : '#3f3f46'),
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
                    color: isHovered || idx === 0 ? '#09090b' : '#f4f4f5',
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
          borderTop: '1px solid #1f1f23'
        }}>
          <ShieldCheck size={13} color="#71717a" style={{ flexShrink: 0 }} />
          <span style={{ fontSize: '11px', color: '#71717a', fontFamily: "'JetBrains Mono', monospace" }}>
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
