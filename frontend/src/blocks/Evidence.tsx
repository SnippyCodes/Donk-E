import React, { useState } from 'react'
import { BookOpen, FileText, ShieldCheck, ExternalLink, ChevronDown, ChevronRight } from 'lucide-react'

export interface EvidenceBlockProps {
  title: string
  evidence_items: Array<{
    id: string
    title: string
    snippet?: string
    source?: string
  }>
  evidence_ids: string[]
}

export const EvidenceBlock: React.FC<{ data: EvidenceBlockProps }> = ({ data }) => {
  const [expanded, setExpanded] = useState<Record<number, boolean>>({ 0: true })

  const toggleItem = (idx: number) => {
    setExpanded(prev => ({ ...prev, [idx]: !prev[idx] }))
  }

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
            <BookOpen size={14} />
          </div>
          <span style={{ fontSize: '13px', fontWeight: 600, color: '#f4f4f5' }}>
            {data.title}
          </span>
        </div>

        <span style={{
          fontSize: '11px',
          color: '#a1a1aa',
          fontFamily: "'JetBrains Mono', monospace",
          padding: '2px 8px',
          borderRadius: '4px',
          background: '#18181b',
          border: '1px solid #27272a'
        }}>
          {data.evidence_items.length} Grounded Documents
        </span>
      </div>

      {/* Grounded Evidence List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {data.evidence_items.map((item, idx) => {
          const isOpen = expanded[idx] !== false
          return (
            <div
              key={idx}
              style={{
                background: '#09090b',
                border: '1px solid #27272a',
                borderRadius: '6px',
                overflow: 'hidden',
                transition: 'border-color 0.15s ease'
              }}
            >
              <div
                onClick={() => toggleItem(idx)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '10px 12px',
                  cursor: 'pointer',
                  userSelect: 'none',
                  background: isOpen ? '#121215' : '#09090b',
                  borderBottom: isOpen ? '1px solid #1f1f23' : 'none'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {isOpen ? <ChevronDown size={14} color="#a1a1aa" /> : <ChevronRight size={14} color="#a1a1aa" />}
                  <FileText size={14} color="#f59e0b" />
                  <strong style={{ fontSize: '12.5px', color: '#f4f4f5' }}>{item.title}</strong>
                </div>

                <span style={{
                  fontSize: '11px',
                  fontFamily: "'JetBrains Mono', monospace",
                  padding: '1px 6px',
                  borderRadius: '4px',
                  background: '#18181b',
                  border: '1px solid #27272a',
                  color: '#f59e0b'
                }}>
                  [{item.id}]
                </span>
              </div>

              {isOpen && (
                <div style={{ padding: '12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {item.snippet && (
                    <div style={{
                      fontSize: '12px',
                      color: '#d4d4d8',
                      lineHeight: 1.55,
                      background: '#121215',
                      padding: '10px 12px',
                      borderRadius: '5px',
                      borderLeft: '2px solid #f59e0b',
                      border: '1px solid #1f1f23',
                      borderLeftWidth: '3px',
                      borderLeftColor: '#f59e0b',
                      fontFamily: "'JetBrains Mono', monospace"
                    }}>
                      {item.snippet}
                    </div>
                  )}

                  {item.source && (
                    <div style={{
                      fontSize: '10.5px',
                      color: '#71717a',
                      fontFamily: "'JetBrains Mono', monospace",
                      display: 'flex',
                      alignItems: 'center',
                      gap: '5px'
                    }}>
                      <ExternalLink size={11} />
                      <span>Source Document: {item.source}</span>
                    </div>
                  )}
                </div>
              )}
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
            Citation Ledger Index:
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
