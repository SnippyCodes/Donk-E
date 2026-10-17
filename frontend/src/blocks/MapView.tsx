import React, { useState } from 'react'
import { MapPin, Navigation, ShieldCheck } from 'lucide-react'

export interface MapViewProps {
  title: string
  center: { lat: number; lng: number }
  pins: Array<{
    asset_id: string
    lat: number
    lng: number
    volume_bbl?: number
    date?: string
    severity?: string
  }>
  evidence_ids?: string[]
}

export const MapViewBlock: React.FC<{ data: MapViewProps }> = ({ data }) => {
  const [selectedPin, setSelectedPin] = useState<any | null>(null)

  const width = 720
  const height = 300
  const pad = 40

  const lats = data.pins.map(p => p.lat)
  const lngs = data.pins.map(p => p.lng)

  const minLat = Math.min(...lats, data.center.lat - 0.02)
  const maxLat = Math.max(...lats, data.center.lat + 0.02)
  const minLng = Math.min(...lngs, data.center.lng - 0.02)
  const maxLng = Math.max(...lngs, data.center.lng + 0.02)

  const getX = (lng: number) => pad + ((lng - minLng) / Math.max(maxLng - minLng, 0.001)) * (width - pad * 2)
  const getY = (lat: number) => height - pad - ((lat - minLat) / Math.max(maxLat - minLat, 0.001)) * (height - pad * 2)

  return (
    <div className="visual-block-card map-view-block">
      <div className="visual-block-header">
        <div className="visual-block-title">
          <MapPin size={18} color="#38bdf8" />
          <span>{data.title}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: 'var(--text-muted)' }}>
          <Navigation size={13} color="#38bdf8" />
          <span>Center: {data.center.lat.toFixed(4)}, {data.center.lng.toFixed(4)}</span>
        </div>
      </div>

      <div style={{ position: 'relative', width: '100%', overflow: 'hidden', borderRadius: '8px', background: '#070b12' }}>
        <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', maxHeight: '320px' }}>
          {/* Subtle Radar/Grid Circles & Lines */}
          <line x1={0} y1={height / 2} x2={width} y2={height / 2} stroke="rgba(56, 189, 248, 0.08)" strokeDasharray="3 3" />
          <line x1={width / 2} y1={0} x2={width / 2} y2={height} stroke="rgba(56, 189, 248, 0.08)" strokeDasharray="3 3" />
          <circle cx={width / 2} cy={height / 2} r={height * 0.35} fill="none" stroke="rgba(56, 189, 248, 0.05)" />

          {/* Plot Pins */}
          {data.pins.map((pin, idx) => {
            const x = getX(pin.lng)
            const y = getY(pin.lat)
            const isHovered = selectedPin?.asset_id === pin.asset_id
            const isReportable = (pin.volume_bbl || 0) >= 5.0
            const pinColor = isReportable ? '#ef4444' : '#f59e0b'

            return (
              <g
                key={idx}
                style={{ cursor: 'pointer' }}
                onMouseEnter={() => setSelectedPin(pin)}
                onMouseLeave={() => setSelectedPin(null)}
              >
                {/* Glow ring */}
                <circle cx={x} cy={y} r={isHovered ? 14 : 9} fill={pinColor} opacity={0.25} />
                <circle cx={x} cy={y} r={isHovered ? 7 : 5} fill={pinColor} stroke="#fff" strokeWidth={1.5} />
                <text x={x} y={y - 12} fill="#e2e8f0" fontSize="10" textAnchor="middle" fontFamily="var(--font-mono)">
                  {pin.asset_id}
                </text>
              </g>
            )
          })}
        </svg>

        {/* Selected Pin Tooltip Card */}
        {selectedPin && (
          <div style={{
            position: 'absolute',
            bottom: '12px',
            right: '12px',
            background: 'rgba(15, 23, 42, 0.95)',
            border: '1px solid rgba(56, 189, 248, 0.4)',
            borderRadius: '8px',
            padding: '10px 14px',
            fontSize: '12px',
            color: '#f8fafc',
            boxShadow: '0 4px 16px rgba(0,0,0,0.5)',
            pointerEvents: 'none'
          }}>
            <div><strong>{selectedPin.asset_id}</strong> ({selectedPin.date})</div>
            <div style={{ color: 'var(--text-muted)' }}>Coordinates: {selectedPin.lat.toFixed(4)}, {selectedPin.lng.toFixed(4)}</div>
            {selectedPin.volume_bbl !== undefined && (
              <div style={{ color: selectedPin.volume_bbl >= 5.0 ? '#ef4444' : '#f59e0b', fontWeight: 600 }}>
                Spill Volume: {selectedPin.volume_bbl} bbl
              </div>
            )}
          </div>
        )}
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
