import React from 'react'
import { Activity, AlertTriangle, CheckCircle2, XCircle, Calendar, ShieldCheck, User } from 'lucide-react'

export interface StatusCardProps {
  asset_id: string
  name: string
  well_type: string
  area_name: string
  is_producing: boolean
  metrics: {
    wellhead_temp_c: number
    ambient_temp_c: number
    delta_temp_c: number
    threshold_temp_delta: number
  }
  system_status: {
    recorded_status: string
    status_is_stale: boolean
  }
  latest_inspection: {
    inspection_id: string
    date: string
    inspector: string
  }
  reason?: string
  evidence_ids?: string[]
}

export const StatusCard: React.FC<{ data: StatusCardProps }> = ({ data }) => {
  if (!data) return null
  const isProducing = !!data.is_producing
  const isStale = !!data.system_status?.status_is_stale
  const metrics = data.metrics || {
    wellhead_temp_c: 0,
    ambient_temp_c: 0,
    delta_temp_c: 0,
    threshold_temp_delta: 15,
  }
  const latestInsp = data.latest_inspection || {
    inspection_id: 'N/A',
    date: 'N/A',
    inspector: 'Field Inspector',
  }

  return (
    <div
      className="rounded-xl bg-[#121215] border border-zinc-800/80 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.04)] p-4 text-zinc-100 font-sans my-3"
      id={`status-${data.asset_id}`}
    >
      {/* Top Asset Title & Live Producing Badge */}
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-zinc-800/70">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
            <Activity className="w-3.5 h-3.5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono font-bold text-sm text-zinc-100">{data.asset_id}</span>
              <span className="text-xs text-zinc-400 font-medium">({data.name || 'Well'})</span>
              <span className="px-1.5 py-0.2 rounded bg-zinc-900 border border-zinc-800 text-[10px] font-mono text-zinc-400 uppercase">
                {data.well_type}
              </span>
            </div>
            <div className="text-[11px] text-zinc-500 font-mono">{data.area_name}</div>
          </div>
        </div>

        <div
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-mono font-semibold tracking-wide border ${
            isProducing
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
              : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
          }`}
        >
          {isProducing ? <CheckCircle2 className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
          <span>{isProducing ? 'PRODUCING' : 'STOPPED / NON-PRODUCING'}</span>
        </div>
      </div>

      {/* 4-Column Metric Bento Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 my-3">
        {/* 1. Wellhead Temp */}
        <div className="p-3 rounded-lg bg-[#09090b] border border-zinc-800/80">
          <div className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 mb-1">Wellhead Temp</div>
          <div className="text-lg font-mono font-bold text-zinc-100 tabular-nums">
            {typeof metrics.wellhead_temp_c === 'number' ? `${metrics.wellhead_temp_c.toFixed(1)}°C` : 'N/A'}
          </div>
          <div className="text-[10px] text-zinc-500 mt-0.5">Sensor Reading</div>
        </div>

        {/* 2. Ambient Temp */}
        <div className="p-3 rounded-lg bg-[#09090b] border border-zinc-800/80">
          <div className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 mb-1">Ambient Air</div>
          <div className="text-lg font-mono font-bold text-zinc-400 tabular-nums">
            {typeof metrics.ambient_temp_c === 'number' ? `${metrics.ambient_temp_c.toFixed(1)}°C` : 'N/A'}
          </div>
          <div className="text-[10px] text-zinc-500 mt-0.5">Atmospheric</div>
        </div>

        {/* 3. Temp Delta (ΔT) */}
        <div
          className={`p-3 rounded-lg bg-[#09090b] border ${
            isProducing ? 'border-emerald-500/30' : 'border-rose-500/30'
          }`}
        >
          <div className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 mb-1">Thermal Margin ΔT</div>
          <div
            className={`text-lg font-mono font-bold tabular-nums ${
              isProducing ? 'text-emerald-400' : 'text-rose-400'
            }`}
          >
            {typeof metrics.delta_temp_c === 'number' ? `+${metrics.delta_temp_c.toFixed(1)}°C` : 'N/A'}
          </div>
          <div className="text-[10px] text-zinc-500 mt-0.5">Operating Delta</div>
        </div>

        {/* 4. Rule Threshold */}
        <div className="p-3 rounded-lg bg-[#09090b] border border-zinc-800/80">
          <div className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 mb-1">SOP Threshold</div>
          <div className="text-lg font-mono font-bold text-amber-400 tabular-nums">
            ≥ {typeof metrics.threshold_temp_delta === 'number' ? `${metrics.threshold_temp_delta.toFixed(1)}°C` : '15.0°C'}
          </div>
          <div className="text-[10px] text-zinc-500 mt-0.5">{data.well_type} Manual Limit</div>
        </div>
      </div>

      {/* Discrepancy warning if telemetry contradicts recorded_status */}
      {isStale && (
        <div className="flex items-start gap-2.5 p-2.5 mb-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs">
          <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5 text-amber-400" />
          <div className="leading-snug">
            <strong className="font-semibold text-amber-200">Stale Metadata Detected:</strong> System database records show well as{' '}
            <code className="px-1 py-0.5 rounded bg-zinc-900 border border-amber-500/30 text-amber-200 font-mono text-[11px]">
              {data.system_status?.recorded_status || 'active'}
            </code>
            , but empirical telemetry delta is only{' '}
            <span className="font-mono font-semibold">{metrics.delta_temp_c?.toFixed(1)}°C</span> (below the{' '}
            {metrics.threshold_temp_delta}°C SOP requirement).
          </div>
        </div>
      )}

      {/* Operational Reason & Inspector Info */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 p-2.5 rounded-lg bg-[#09090b] border border-zinc-800/80 text-xs">
        <div className="flex items-center gap-1.5">
          <span className="text-zinc-500 font-mono text-[11px]">Cause / Reason:</span>
          <span className="text-zinc-200 font-medium">
            {data.reason || 'No recorded reason'}
          </span>
        </div>
        <div className="flex items-center gap-2 text-zinc-400 font-mono text-[11px] sm:justify-end">
          <Calendar className="w-3.5 h-3.5 text-zinc-500" />
          <span>{latestInsp.date}</span>
          <span className="text-zinc-600">·</span>
          <User className="w-3.5 h-3.5 text-zinc-500" />
          <span>{latestInsp.inspector}</span>
        </div>
      </div>

      {/* Evidence Chips */}
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
