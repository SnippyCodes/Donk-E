import React, { useState } from 'react'
import { TrendingUp, ShieldCheck } from 'lucide-react'

export interface LineChartProps {
  title: string
  x_axis?: string
  series?: Array<{
    name: string
    color?: string
    data?: Array<any>
    dates?: string[]
  }>
  markers?: Array<{
    x?: string
    date?: string
    label?: string
    color?: string
  }>
  evidence_ids?: string[]
}

export const LineChartBlock: React.FC<{ data: LineChartProps }> = ({ data }) => {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null)

  if (!data || !data.series || data.series.length === 0) return null

  const extractY = (d: any): number => {
    if (typeof d === 'number') return d
    if (d && typeof d === 'object') {
      if (typeof d.y === 'number') return d.y
      if (typeof d.value === 'number') return d.value
      if (typeof d.val === 'number') return d.val
    }
    const parsed = parseFloat(String(d))
    return isNaN(parsed) ? 0 : parsed
  }

  const allPoints = data.series.flatMap(s => (Array.isArray(s.data) ? s.data : []))
  if (allPoints.length === 0) return null

  // Extract X-axis dates
  const firstSeries = data.series[0]
  const xLabels: string[] = firstSeries?.dates && Array.isArray(firstSeries.dates) && firstSeries.dates.length > 0
    ? firstSeries.dates
    : (firstSeries?.data || []).map((d: any, idx: number) => {
        if (d && typeof d === 'object') return String(d.x || d.date || idx)
        return `W${idx + 1}`
      })

  const yValues = allPoints.map(p => extractY(p))
  const minY = yValues.length > 0 ? Math.floor(Math.min(...yValues) - 2) : 0
  const maxY = yValues.length > 0 ? Math.ceil(Math.max(...yValues) + 2) : 60

  const width = 760
  const height = 240
  const padLeft = 46
  const padRight = 24
  const padTop = 20
  const padBottom = 34

  const chartW = width - padLeft - padRight
  const chartH = height - padTop - padBottom

  const getX = (idx: number) => padLeft + (idx / Math.max(xLabels.length - 1, 1)) * chartW
  const getY = (val: number) => padTop + chartH - ((val - minY) / Math.max(maxY - minY, 1)) * chartH

  // Non-producing marker dates
  const markerDates = new Set(data.markers?.map(m => m.date || m.x).filter(Boolean) || [])

  // Current hover metrics
  const hoveredDate = hoveredIndex !== null ? xLabels[hoveredIndex] : null
  const wellheadSeries = data.series[0]
  const airSeries = data.series[1]
  const hoveredWellhead = hoveredIndex !== null && wellheadSeries?.data ? extractY(wellheadSeries.data[hoveredIndex]) : null
  const hoveredAir = hoveredIndex !== null && airSeries?.data ? extractY(airSeries.data[hoveredIndex]) : null
  const hoveredDelta = hoveredWellhead !== null && hoveredAir !== null ? (hoveredWellhead - hoveredAir) : null
  const hoveredIsStopped = hoveredDate ? markerDates.has(hoveredDate) : false

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
      gap: '12px',
      position: 'relative'
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
            <TrendingUp size={14} />
          </div>
          <span style={{ fontSize: '13px', fontWeight: 600, color: '#28231e' }}>
            {data.title || 'Telemetry Line Chart'}
          </span>
        </div>

        {/* Legend */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '14px',
          fontSize: '11px',
          fontFamily: "'JetBrains Mono', monospace",
          flexWrap: 'wrap'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div style={{ width: '12px', height: '2px', background: '#28231e', borderRadius: '1px' }} />
            <span style={{ color: '#3f3932' }}>Wellhead Temp</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div style={{ width: '12px', height: '2px', borderTop: '2px dashed #7a7268' }} />
            <span style={{ color: '#71695e' }}>Air Temp</span>
          </div>
          {markerDates.size > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: 'rgba(169, 77, 70, 0.2)',
                border: '1.5px solid #a94d46'
              }} />
              <span style={{ color: '#a94d46', fontWeight: 500 }}>
                Not Producing ({markerDates.size})
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Interactive Tooltip Card */}
      {hoveredIndex !== null && hoveredWellhead !== null && (
        <div style={{
          background: '#f0ebe3',
          border: '1px solid #c6bbaa',
          borderRadius: '6px',
          padding: '6px 12px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px',
          fontSize: '11px',
          fontFamily: "'JetBrains Mono', monospace",
          boxShadow: '0 4px 16px rgba(68, 52, 35, 0.10)'
        }}>
          <div>
            <span style={{ color: '#7a7268' }}>Date: </span>
            <strong style={{ color: '#28231e' }}>{hoveredDate}</strong>
          </div>
          <div>
            <span style={{ color: '#7a7268' }}>Wellhead: </span>
            <strong style={{ color: '#28231e' }}>{hoveredWellhead.toFixed(1)}°C</strong>
          </div>
          {hoveredAir !== null && (
            <div>
              <span style={{ color: '#7a7268' }}>Air: </span>
              <strong style={{ color: '#71695e' }}>{hoveredAir.toFixed(1)}°C</strong>
            </div>
          )}
          {hoveredDelta !== null && (
            <div>
              <span style={{ color: '#7a7268' }}>Delta: </span>
              <strong style={{ color: hoveredDelta >= 15.0 ? '#55785e' : '#a94d46' }}>
                {hoveredDelta >= 0 ? `+${hoveredDelta.toFixed(1)}°C` : `${hoveredDelta.toFixed(1)}°C`}
              </strong>
            </div>
          )}
          <span style={{
            padding: '1px 6px',
            borderRadius: '4px',
            fontSize: '10px',
            fontWeight: 600,
            background: hoveredIsStopped ? 'rgba(169, 77, 70, 0.15)' : 'rgba(85, 120, 94, 0.15)',
            color: hoveredIsStopped ? '#a94d46' : '#55785e',
            border: hoveredIsStopped ? '1px solid rgba(169, 77, 70, 0.3)' : '1px solid rgba(85, 120, 94, 0.3)',
          }}>
            {hoveredIsStopped ? 'NOT PRODUCING' : 'PRODUCING OIL'}
          </span>
        </div>
      )}

      {/* SVG Canvas */}
      <div style={{
        width: '100%',
        overflowX: 'auto',
        background: '#f7f5f0',
        borderRadius: '6px',
        border: '1px solid #e8e0d4',
        padding: '8px 0',
        position: 'relative'
      }}>
        <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', maxHeight: '250px', display: 'block' }}>
          {/* Subtle Grid Lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((pct, idx) => {
            const y = padTop + chartH * pct
            const val = maxY - (maxY - minY) * pct
            return (
              <g key={idx}>
                <line x1={padLeft} y1={y} x2={width - padRight} y2={y} stroke="#ded6c9" strokeDasharray="3 3" strokeWidth={1} />
                <text
                  x={padLeft - 8}
                  y={y + 3.5}
                  fill="#7a7268"
                  fontSize="10"
                  textAnchor="end"
                  fontFamily="'JetBrains Mono', monospace"
                  className="tabular-nums"
                >
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
              <g key={`band-${idx}`}>
                <rect
                  x={x - colW / 2}
                  y={padTop}
                  width={colW}
                  height={chartH}
                  fill="rgba(169, 77, 70, 0.08)"
                  stroke="rgba(169, 77, 70, 0.25)"
                  strokeDasharray="2 2"
                />
                <circle
                  cx={x}
                  cy={padTop + 8}
                  r={3.5}
                  fill="#f7f5f0"
                  stroke="#a94d46"
                  strokeWidth={1.5}
                />
              </g>
            )
          })}

          {/* Active Hover Guideline */}
          {hoveredIndex !== null && (
            <line
              x1={getX(hoveredIndex)}
              y1={padTop}
              x2={getX(hoveredIndex)}
              y2={padTop + chartH}
              stroke="#b85d3c"
              strokeWidth={1}
              strokeDasharray="2 2"
            />
          )}

          {/* Series Lines */}
          {data.series.map((s, sIdx) => {
            const sData = Array.isArray(s.data) ? s.data : []
            const isWellhead = sIdx === 0 || s.name.toLowerCase().includes('wellhead')
            const strokeColor = isWellhead ? '#28231e' : '#7a7268'
            const strokeDash = isWellhead ? 'none' : '4 4'
            const strokeW = isWellhead ? 2.2 : 1.5

            const points = sData.map((d, idx) => `${getX(idx)},${getY(extractY(d))}`).join(' ')

            return (
              <g key={s.name || `series-${sIdx}`}>
                <polyline
                  fill="none"
                  stroke={strokeColor}
                  strokeWidth={strokeW}
                  strokeDasharray={strokeDash}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  points={points}
                />
                {sData.map((d, idx) => {
                  const yVal = extractY(d)
                  const dateStr = (s.dates && s.dates[idx]) || xLabels[idx] || ''
                  const isNotProducing = isWellhead && markerDates.has(dateStr)
                  const isHovered = hoveredIndex === idx

                  return (
                    <circle
                      key={idx}
                      cx={getX(idx)}
                      cy={getY(yVal)}
                      r={isHovered ? 6 : (isNotProducing ? 4.5 : 3)}
                      fill={isHovered ? '#b85d3c' : (isNotProducing ? '#f7f5f0' : strokeColor)}
                      stroke={isHovered ? '#ffffff' : (isNotProducing ? '#a94d46' : '#fffdfa')}
                      strokeWidth={isHovered ? 2 : (isNotProducing ? 2 : 1.5)}
                      style={{ cursor: 'pointer', transition: 'all 0.15s ease' }}
                      onMouseEnter={() => setHoveredIndex(idx)}
                      onMouseLeave={() => setHoveredIndex(null)}
                    />
                  )
                })}
              </g>
            )
          })}

          {/* Interactive Invisible Hover Bars for easy mouse targeting */}
          {xLabels.map((_, idx) => {
            const x = getX(idx)
            const colW = chartW / Math.max(xLabels.length - 1, 1)
            return (
              <rect
                key={`hit-${idx}`}
                x={x - colW / 2}
                y={padTop}
                width={colW}
                height={chartH}
                fill="transparent"
                style={{ cursor: 'pointer' }}
                onMouseEnter={() => setHoveredIndex(idx)}
              />
            )
          })}

          {/* X Axis Labels */}
          {xLabels.map((date, idx) => {
            if (idx % 2 !== 0 && xLabels.length > 8) return null
            const x = getX(idx)
            const isMarked = markerDates.has(date)
            const isHovered = hoveredIndex === idx
            return (
              <text
                key={`x-${idx}`}
                x={x}
                y={height - padBottom + 16}
                fill={isHovered ? '#b85d3c' : (isMarked ? '#a94d46' : '#7a7268')}
                fontSize="9.5"
                fontWeight={isHovered || isMarked ? 700 : 400}
                textAnchor="middle"
                fontFamily="'JetBrains Mono', monospace"
              >
                {date.length > 5 ? date.slice(5) : date}
              </text>
            )
          })}
        </svg>
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
