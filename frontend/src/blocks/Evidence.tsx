import React, { useState } from 'react'
import { BookOpen, FileText, ShieldCheck, ExternalLink, ChevronDown, ChevronRight } from 'lucide-react'

export interface EvidenceBlockProps {
  title: string
  evidence_items: Array<{
    id: string
    title: string
    snippet?: string
    source?: string
    url?: string
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
            <BookOpen size={14} />
          </div>
          <span style={{ fontSize: '13px', fontWeight: 600, color: '#28231e' }}>
            {data.title}
          </span>
        </div>

        <span style={{
          fontSize: '11px',
          color: '#71695e',
          fontFamily: "'JetBrains Mono', monospace",
          padding: '2px 8px',
          borderRadius: '4px',
          background: '#f0ebe3',
          border: '1px solid #ded6c9'
        }}>
          {data.evidence_items.length} Grounded Documents
        </span>
      </div>

      {/* Grounded Evidence List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {data.evidence_items.map((item, idx) => {
          const isOpen = expanded[idx] !== false
          let safeUrl: string | undefined
          try {
            const parsedUrl = item.url ? new URL(item.url) : null
            if (parsedUrl && (parsedUrl.protocol === 'https:' || parsedUrl.protocol === 'http:')) safeUrl = parsedUrl.toString()
          } catch {
            safeUrl = undefined
          }
          return (
            <div
              key={idx}
              style={{
                background: '#f7f5f0',
                border: '1px solid #ded6c9',
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
                  background: isOpen ? '#fffdfa' : '#f7f5f0',
                  borderBottom: isOpen ? '1px solid #e8e0d4' : 'none'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {isOpen ? <ChevronDown size={14} color="#71695e" /> : <ChevronRight size={14} color="#71695e" />}
                  <FileText size={14} color="#b85d3c" />
                  {safeUrl ? (
                    <a href={safeUrl} target="_blank" rel="noopener noreferrer" onClick={event => event.stopPropagation()} style={{ fontSize: '12.5px', color: '#477b7a', textDecoration: 'none' }}>{item.title}</a>
                  ) : (
                    <strong style={{ fontSize: '12.5px', color: '#28231e' }}>{item.title}</strong>
                  )}
                </div>

                <span style={{
                  fontSize: '11px',
                  fontFamily: "'JetBrains Mono', monospace",
                  padding: '1px 6px',
                  borderRadius: '4px',
                  background: '#f0ebe3',
                  border: '1px solid #ded6c9',
                  color: '#b85d3c'
                }}>
                  [{item.id}]
                </span>
              </div>

              {isOpen && (
                <div style={{ padding: '12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {item.snippet && (
                    <div style={{
                      fontSize: '12px',
                      color: '#3f3932',
                      lineHeight: 1.55,
                      background: '#fffdfa',
                      padding: '10px 12px',
                      borderRadius: '5px',
                      borderLeft: '2px solid #b85d3c',
                      border: '1px solid #e8e0d4',
                      borderLeftWidth: '3px',
                      borderLeftColor: '#b85d3c',
                      fontFamily: "'JetBrains Mono', monospace"
                    }}>
                      {item.snippet}
                    </div>
                  )}

                  {item.source && (
                    <div style={{
                      fontSize: '10.5px',
                      color: '#7a7268',
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
          borderTop: '1px solid #e8e0d4'
        }}>
          <ShieldCheck size={13} color="#7a7268" style={{ flexShrink: 0 }} />
          <span style={{ fontSize: '11px', color: '#7a7268', fontFamily: "'JetBrains Mono', monospace" }}>
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
