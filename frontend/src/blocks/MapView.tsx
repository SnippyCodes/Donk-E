import React, { useState } from 'react'
import { MapPin, Navigation, ShieldCheck } from 'lucide-react'

export interface MapViewProps {
  title: string
  center: { lat: number; lng?: number; lon?: number }
  pins: Array<{
    asset_id?: string
    well_id?: string
    id?: string
    title?: string
    lat: number
    lng?: number
    lon?: number
    volume_bbl?: number
    date?: string
    details?: string
    severity?: string
    inspection_id?: string
  }>
  evidence_ids?: string[]
}

export const MapViewBlock: React.FC<{ data: MapViewProps }> = ({ data }) => {
  const [selectedPin, setSelectedPin] = useState<any | null>(null)

  const width = 720
  const height = 280
  const pad = 44

  const centerLat = Number(data?.center?.lat ?? 32.152)
  const centerLon = Number(data?.center?.lng ?? (data?.center as any)?.lon ?? -102.164)

  const rawPins = Array.isArray(data?.pins) ? data.pins : []
  const normalizedPins = rawPins.map((p, idx) => {
    const lat = Number(p.lat ?? centerLat)
    const lng = Number(p.lng ?? p.lon ?? centerLon)
    const assetId = p.asset_id || p.well_id || (p.title ? p.title.split(' ')[0] : `WELL-${idx + 1}`)
    let vol = p.volume_bbl
    if (vol === undefined && p.details) {
      const match = String(p.details).match(/([\d.]+)\s*bbl/i)
      if (match) vol = parseFloat(match[1])
    }
    return {
      ...p,
      assetId,
      lat,
      lng,
      volume_bbl: vol,
      date: p.date || (p.title && p.title.includes('(') ? p.title.split('(')[1].replace(')', '') : ''),
    }
  })

  const lats = normalizedPins.map(p => p.lat)
  const lngs = normalizedPins.map(p => p.lng)

  const minLat = lats.length > 0 ? Math.min(...lats, centerLat - 0.02) : centerLat - 0.02
  const maxLat = lats.length > 0 ? Math.max(...lats, centerLat + 0.02) : centerLat + 0.02
  const minLng = lngs.length > 0 ? Math.min(...lngs, centerLon - 0.02) : centerLon - 0.02
  const maxLng = lngs.length > 0 ? Math.max(...lngs, centerLon + 0.02) : centerLon + 0.02

  const getX = (lng: number) => pad + ((lng - minLng) / Math.max(maxLng - minLng, 0.001)) * (width - pad * 2)
  const getY = (lat: number) => height - pad - ((lat - minLat) / Math.max(maxLat - minLat, 0.001)) * (height - pad * 2)

  return (
    <div className="rounded-xl bg-[#fffdfa] border border-zinc-800/80 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.04)] p-4 text-zinc-100 font-sans my-3">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-zinc-800/70">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
            <MapPin className="w-3.5 h-3.5" />
          </div>
          <div>
            <div className="text-xs font-semibold text-zinc-100 tracking-tight">{data.title || 'Geographic Telemetry Map'}</div>
            <div className="text-[10px] text-zinc-500 font-mono">Radar Projection: WGS84 Geo-Coordinates</div>
          </div>
        </div>
        <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-zinc-900 border border-zinc-800 text-[11px] font-mono text-zinc-400 tabular-nums">
          <Navigation className="w-3 h-3 text-zinc-500" />
          <span>Center: {centerLat.toFixed(4)}, {centerLon.toFixed(4)}</span>
        </div>
      </div>

      {/* SVG Canvas */}
      <div className="relative w-full overflow-hidden rounded-lg bg-[#f7f5f0] border border-zinc-800/80">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto max-h-[300px] select-none">
          {/* Subtle Radar/Grid Coordinates */}
          <line x1={0} y1={height / 2} x2={width} y2={height / 2} stroke="#ded6c9" strokeDasharray="3 3" />
          <line x1={width / 2} y1={0} x2={width / 2} y2={height} stroke="#ded6c9" strokeDasharray="3 3" />
          <circle cx={width / 2} cy={height / 2} r={height * 0.38} fill="none" stroke="#ded6c9" strokeDasharray="2 2" />
          <circle cx={width / 2} cy={height / 2} r={height * 0.18} fill="none" stroke="#e8e0d4" />

          {/* Center Marker */}
          <circle cx={width / 2} cy={height / 2} r={3} fill="#7a7268" />
          <text x={width / 2 + 6} y={height / 2 - 6} fill="#857b6e" fontSize="9" fontFamily="var(--font-mono)">AREA CENTER</text>

          {/* Plot Pins */}
          {normalizedPins.map((pin, idx) => {
            const x = getX(pin.lng)
            const y = getY(pin.lat)
            const isHovered = selectedPin?.assetId === pin.assetId
            const isReportable = (pin.volume_bbl || 0) >= 5.0
            const pinColor = isReportable ? '#a94d46' : '#b85d3c'

            return (
              <g
                key={idx}
                className="cursor-pointer transition-all duration-150"
                onMouseEnter={() => setSelectedPin(pin)}
                onMouseLeave={() => setSelectedPin(null)}
              >
                {/* Ping wave for reportable */}
                {isReportable && (
                  <circle cx={x} cy={y} r={12} fill="none" stroke="#a94d46" strokeWidth={1} opacity={0.4} />
                )}
                <circle
                  cx={x}
                  cy={y}
                  r={isHovered ? 7 : 5}
                  fill={pinColor}
                  stroke="#f7f5f0"
                  strokeWidth={2}
                />
                <text
                  x={x}
                  y={y - 9}
                  fill={isHovered ? '#28231e' : '#71695e'}
                  fontSize="10"
                  fontWeight={isHovered ? 600 : 500}
                  textAnchor="middle"
                  fontFamily="var(--font-mono)"
                >
                  {pin.assetId}
                </text>
              </g>
            )
          })}
        </svg>

        {/* Selected Pin Tooltip Card */}
        {selectedPin && (
          <div className="absolute bottom-3 right-3 bg-[#fffdfa] border border-zinc-700/80 rounded-lg p-2.5 text-xs font-mono shadow-2xl pointer-events-none z-10 max-w-[240px]">
            <div className="flex items-center justify-between gap-2 border-b border-zinc-800 pb-1 mb-1.5">
              <span className="font-semibold text-zinc-100">{selectedPin.assetId}</span>
              {selectedPin.date && <span className="text-[10px] text-zinc-500">{selectedPin.date}</span>}
            </div>
            <div className="text-[11px] text-zinc-400 tabular-nums">
              GPS: {selectedPin.lat.toFixed(4)}, {selectedPin.lng.toFixed(4)}
            </div>
            {selectedPin.volume_bbl !== undefined && (
              <div className={`mt-1 font-semibold ${selectedPin.volume_bbl >= 5.0 ? 'text-rose-400' : 'text-amber-400'}`}>
                Spill Volume: {selectedPin.volume_bbl.toFixed(1)} bbl {selectedPin.volume_bbl >= 5.0 ? '(Reportable)' : ''}
              </div>
            )}
            {selectedPin.inspection_id && (
              <div className="mt-1 text-[10px] text-zinc-500">
                Inspection: {selectedPin.inspection_id}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Verified Evidence Footer */}
      {data.evidence_ids && data.evidence_ids.length > 0 && (
        <div className="mt-3 pt-2.5 border-t border-zinc-800/60 flex items-center gap-2 flex-wrap text-xs">
          <ShieldCheck className="w-3.5 h-3.5 text-zinc-500 shrink-0" />
          <span className="text-zinc-500 font-mono text-[11px]">Verified Citations:</span>
          {data.evidence_ids.map(eid => (
            <span
              key={eid}
              className="px-1.5 py-0.5 rounded bg-zinc-800/80 border border-zinc-700 text-[11px] font-mono text-amber-300"
            >
              [{eid}]
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
