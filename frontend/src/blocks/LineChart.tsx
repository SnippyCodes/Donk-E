import React, { useState } from 'react'
import { TrendingUp, ShieldCheck } from 'lucide-react'

export interface LineChartProps {
  title: string
  x_axis: string
  series: Array<{
    name: string
    color: string
    data: Array<{ x: string; y: number }>
  }>
  markers?: Array<{
    x: string
    label: string
    color?: string
  }>
  evidence_ids?: string[]
}

export const LineChartBlock: React.FC<{ data: LineChartProps }> = ({ data }) => {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null)

  const allPoints = data.series.flatMap(s => s.data)
  if (allPoints.length === 0) return null

  const xLabels = data.series[0]?.data.map(d => d.x) || []
  const yValues = allPoints.map(p => p.y)
  const minY = Math.floor(Math.min(...yValues) - 2)
  const maxY = Math.ceil(Math.max(...yValues) + 2)

  const width = 720
  const height = 280
  const padLeft = 45
  const padRight = 25
  const padTop = 25
  const padBottom = 40

  const chartW = width - padLeft - padRight
  const chartH = height - padTop - padBottom

  const getX = (idx: number) => padLeft + (idx / Math.max(xLabels.length - 1, 1)) * chartW
  const getY = (val: number) => padTop + chartH - ((val - minY) / Math.max(maxY - minY, 1)) * chartH

  // Markers map for quick lookup
  const markerDates = new Set(data.markers?.map(m => m.x) || [])

  return (
    <div className="visual-block-card line-chart-block">
      <div className="visual-block-header">
        <div className="visual-block-title">
          <TrendingUp size={18} color="#38bdf8" />
          <span>{data.title}</span>
        </div>
        <div style={{ display: 'flex', gap: '16px', fontSize: '12px' }}>
          {data.series.map(s => (
            <div key={s.name} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: s.color }} />
              <span style={{ color: 'var(--text-secondary)' }}>{s.name}</span>
            </div>
          ))}
          {data.markers && data.markers.length > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{ width: '10px', height: '10px', borderRadius: '2px', background: '#ef4444' }} />
              <span style={{ color: '#ef4444' }}>Not Producing</span>
            </div>
          )}
        </div>
      </div>

      <div style={{ width: '100%', overflowX: 'auto' }}>
        <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', maxHeight: '300px' }}>
          {/* Horizontal Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((pct, idx) => {
            const y = padTop + chartH * pct
            const val = maxY - (maxY - minY) * pct
            return (
              <g key={idx}>
                <line x1={padLeft} y1={y} x2={width - padRight} y2={y} stroke="rgba(255,255,255,0.06)" strokeDasharray="4 4" />
                <text x={padLeft - 8} y={y + 4} fill="#64748b" fontSize="10" textAnchor="end" fontFamily="var(--font-mono)">
                  {val.toFixed(0)}°C
                </text>
              </g>
            )
          })}

          {/* Non-producing shaded column bands */}
          {xLabels.map((date, idx) => {
            if (!markerDates.has(date)) return null
            const x = getX(idx)
            const colW = chartW / Math.max(xLabels.length - 1, 1)
            return (
              <rect
                key={`band-${idx}`}
                x={x - colW / 2}
                y={padTop}
                width={colW}
                height={chartH}
                fill="rgba(239, 68, 68, 0.15)"
                stroke="rgba(239, 68, 68, 0.3)"
              />
            )
          })}

          {/* Series lines */}
          {data.series.map(s => {
            const points = s.data.map((d, idx) => `${getX(idx)},${getY(d.y)}`).join(' ')
            return (
              <g key={s.name}>
                <polyline
                  fill="none"
                  stroke={s.color}
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  points={points}
                />
                {s.data.map((d, idx) => (
                  <circle
                    key={idx}
                    cx={getX(idx)}
                    cy={getY(d.y)}
                    r={hoveredIndex === idx ? 5 : 3}
                    fill={s.color}
                    stroke="#0a0e17"
                    strokeWidth="1.5"
                    onMouseEnter={() => setHoveredIndex(idx)}
                    onMouseLeave={() => setHoveredIndex(null)}
                  />
                ))}
              </g>
            )
          })}

          {/* X Axis Labels */}
          {xLabels.map((date, idx) => {
            if (idx % 2 !== 0 && xLabels.length > 8) return null
            const x = getX(idx)
            return (
              <text
                key={`x-${idx}`}
                x={x}
                y={height - padBottom + 18}
                fill="#64748b"
                fontSize="9"
                textAnchor="middle"
                fontFamily="var(--font-mono)"
              >
                {date.slice(5)}
              </text>
            )
          })}
        </svg>
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
