import React from 'react'
import { Table as TableIcon, ShieldCheck } from 'lucide-react'

export interface TableBlockProps {
  title: string
  columns: Array<{ key: string; label: string } | string>
  rows: Array<Record<string, any>>
  summary_stats?: Record<string, any>
  evidence_ids?: string[]
}

export const TableBlock: React.FC<{ data: TableBlockProps }> = ({ data }) => {
  const normalizedColumns = (data.columns || []).map((col, idx) => {
    if (typeof col === 'string') {
      return { key: col, label: col }
    }
    return {
      key: col?.key || col?.label || `col_${idx}`,
      label: col?.label || col?.key || `Column ${idx + 1}`,
    }
  })

  const rows = data.rows || []

  const renderStatusBadge = (statusStr: string) => {
    const s = String(statusStr).toLowerCase()
    if (s.includes('breach') || s.includes('fail') || s.includes('uncontained') || s.includes('overdue')) {
      return (
        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
          {statusStr}
        </span>
      )
    }
    if (s.includes('met') || s.includes('pass') || s.includes('compliant') || s.includes('ok')) {
      return (
        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          {statusStr}
        </span>
      )
    }
    if (s.includes('pending') || s.includes('action') || s.includes('open') || s.includes('warn')) {
      return (
        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
          {statusStr}
        </span>
      )
    }
    return <span className="text-zinc-300 font-mono text-[11px]">{statusStr}</span>
  }

  return (
    <div className="rounded-xl bg-[#121215] border border-zinc-800/80 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.04)] p-4 text-zinc-100 font-sans my-3">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-zinc-800/70">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
            <TableIcon className="w-3.5 h-3.5" />
          </div>
          <div>
            <div className="text-xs font-semibold text-zinc-100 tracking-tight">{data.title || 'Structured Intelligence Table'}</div>
            <div className="text-[10px] text-zinc-500 font-mono">Records: {rows.length} entries</div>
          </div>
        </div>

        {data.summary_stats && Object.keys(data.summary_stats).length > 0 && (
          <div className="flex items-center gap-2.5 text-[11px] font-mono">
            {Object.entries(data.summary_stats).map(([k, v]) => (
              <span key={k} className="px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800 text-zinc-400">
                {k.replace(/_/g, ' ')}: <strong className="text-zinc-100 font-semibold">{String(v)}</strong>
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Table Container */}
      <div className="overflow-x-auto rounded-lg border border-zinc-800/80 bg-[#09090b]">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="bg-zinc-900/90 border-b border-zinc-800 text-[10px] font-mono uppercase tracking-wider text-zinc-400">
              {normalizedColumns.map((col, cIdx) => (
                <th key={`${col.key}-${cIdx}`} className="py-2.5 px-3 font-semibold select-none">
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/50">
            {rows.length === 0 ? (
              <tr>
                <td colSpan={Math.max(normalizedColumns.length, 1)} className="py-6 text-center text-zinc-500 text-xs font-mono">
                  No records found in this operational window.
                </td>
              </tr>
            ) : (
              rows.map((row, idx) => (
                <tr
                  key={idx}
                  className="hover:bg-zinc-800/30 transition-colors duration-100"
                >
                  {normalizedColumns.map((col, cIdx) => {
                    const val = row[col.key] ?? row[col.label] ?? ''
                    const keyLower = (col.key || '').toLowerCase()
                    const isDelta = keyLower.includes('delta') || keyLower.includes('temp')
                    const isEvidence = keyLower.includes('evidence')
                    const isAsset = keyLower.includes('well') || keyLower.includes('asset')
                    const isStatus = keyLower.includes('status') || keyLower.includes('verdict') || keyLower.includes('type')
                    const isNumeric = typeof val === 'number'

                    return (
                      <td
                        key={`${col.key}-${cIdx}`}
                        className={`py-2 px-3 text-zinc-200 ${isNumeric || isAsset || isDelta ? 'font-mono text-[11px] tabular-nums' : 'text-xs'}`}
                      >
                        {isEvidence && Array.isArray(val) ? (
                          <div className="flex gap-1 flex-wrap">
                            {val.map((eid: string) => (
                              <span key={eid} className="px-1.5 py-0.5 rounded bg-zinc-800/80 border border-zinc-700 text-[10px] font-mono text-amber-300">
                                [{eid}]
                              </span>
                            ))}
                          </div>
                        ) : isDelta && typeof val === 'number' ? (
                          <span className={`font-semibold ${val < 15.0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                            {val >= 0 ? `+${val.toFixed(1)}°C` : `${val.toFixed(1)}°C`}
                          </span>
                        ) : isStatus && typeof val === 'string' && val.length < 25 ? (
                          renderStatusBadge(val)
                        ) : (
                          <span>
                            {val === null || val === undefined || val === ''
                              ? '—'
                              : typeof val === 'object'
                              ? JSON.stringify(val)
                              : String(val)}
                          </span>
                        )}
                      </td>
                    )
                  })}
                </tr>
              ))
            )}
          </tbody>
        </table>
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
