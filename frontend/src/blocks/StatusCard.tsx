import React from 'react'
import { Activity, AlertTriangle, CheckCircle2, XCircle, Calendar, ShieldCheck } from 'lucide-react'

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
    <div className="visual-block-card status-card" id={`status-${data.asset_id}`}>
      <div className="visual-block-header">
        <div className="visual-block-title">
          <Activity size={18} color="#38bdf8" />
          <span>{data.asset_id} — {data.name}</span>
          <span style={{
            fontSize: '11px',
            padding: '2px 8px',
            borderRadius: '12px',
            background: 'rgba(255,255,255,0.06)',
            color: '#94a3b8',
            fontFamily: 'var(--font-mono)'
          }}>
            {data.well_type}
          </span>
        </div>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          padding: '4px 12px',
          borderRadius: '20px',
          fontSize: '12px',
          fontWeight: 600,
          background: isProducing ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
          color: isProducing ? '#10b981' : '#ef4444',
          border: `1px solid ${isProducing ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`
        }}>
          {isProducing ? <CheckCircle2 size={14} /> : <XCircle size={14} />}
          <span>{isProducing ? 'PRODUCING OIL' : 'STOPPED / NOT PRODUCING'}</span>
        </div>
      </div>

      {/* Metrics Row */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
        gap: '12px',
        margin: '16px 0',
      }}>
        <div style={{
          background: 'rgba(0,0,0,0.25)',
          padding: '12px',
          borderRadius: '8px',
          border: '1px solid var(--border-subtle)'
        }}>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>Wellhead Temp</div>
          <div style={{ fontSize: '18px', fontWeight: 700, color: '#f8fafc' }}>
            {typeof metrics.wellhead_temp_c === 'number' ? `${metrics.wellhead_temp_c.toFixed(1)}°C` : 'N/A'}
          </div>
        </div>

        <div style={{
          background: 'rgba(0,0,0,0.25)',
          padding: '12px',
          borderRadius: '8px',
          border: '1px solid var(--border-subtle)'
        }}>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>Ambient Air Temp</div>
          <div style={{ fontSize: '18px', fontWeight: 700, color: '#94a3b8' }}>
            {typeof metrics.ambient_temp_c === 'number' ? `${metrics.ambient_temp_c.toFixed(1)}°C` : 'N/A'}
          </div>
        </div>

        <div style={{
          background: 'rgba(0,0,0,0.25)',
          padding: '12px',
          borderRadius: '8px',
          border: `1px solid ${isProducing ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)'}`
        }}>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>Temp Delta (ΔT)</div>
          <div style={{
            fontSize: '18px',
            fontWeight: 700,
            color: isProducing ? '#10b981' : '#ef4444'
          }}>
            {typeof metrics.delta_temp_c === 'number' ? `+${metrics.delta_temp_c.toFixed(1)}°C` : 'N/A'}
          </div>
        </div>

        <div style={{
          background: 'rgba(0,0,0,0.25)',
          padding: '12px',
          borderRadius: '8px',
          border: '1px solid var(--border-subtle)'
        }}>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>Rule Threshold</div>
          <div style={{ fontSize: '18px', fontWeight: 700, color: '#38bdf8' }}>
            ≥ {typeof metrics.threshold_temp_delta === 'number' ? `${metrics.threshold_temp_delta.toFixed(1)}°C` : '15.0°C'}
          </div>
        </div>
      </div>

      {/* Discrepancy warning if telemetry contradicts recorded_status */}
      {isStale && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          padding: '10px 14px',
          borderRadius: '8px',
          background: 'rgba(245, 158, 11, 0.1)',
          border: '1px solid rgba(245, 158, 11, 0.3)',
          color: '#fbbf24',
          fontSize: '12px',
          marginBottom: '16px'
        }}>
          <AlertTriangle size={16} />
          <div>
            <strong>Status Discrepancy:</strong> System records show well as <em>{data.system_status?.recorded_status || 'active'}</em>, but telemetry delta is below {metrics.threshold_temp_delta}°C threshold.
          </div>
        </div>
      )}

      {/* Operational Reason & Inspector Info */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '12px',
        padding: '12px 14px',
        background: 'rgba(255,255,255,0.02)',
        borderRadius: '8px',
        fontSize: '12px',
        border: '1px solid var(--border-subtle)'
      }}>
        <div>
          <span style={{ color: 'var(--text-muted)' }}>Operational Reason: </span>
          <span style={{ color: '#f8fafc', fontWeight: 500 }}>
            {data.reason || 'No recorded reason'}
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Calendar size={13} color="#94a3b8" />
          <span style={{ color: 'var(--text-muted)' }}>{latestInsp.date} by {latestInsp.inspector}</span>
        </div>
      </div>

      {/* Evidence Chips */}
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
