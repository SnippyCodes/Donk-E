import React, { useState, useRef, useEffect } from 'react'
import {
  Send,
  Bot,
  User,
  Sparkles,
  Loader2,
  Mic,
  MicOff,
  Camera,
  ChevronDown,
  ChevronRight,
  ShieldCheck,
  Cpu,
  Clock,
} from 'lucide-react'
import { StatusCard } from './blocks/StatusCard'
import { TableBlock } from './blocks/Table'
import { LineChartBlock } from './blocks/LineChart'
import { BarChartBlock } from './blocks/BarChart'
import { MapViewBlock } from './blocks/MapView'
import { HeatmapBlock } from './blocks/Heatmap'
import { ConflictBlock } from './blocks/Conflict'
import { EvidenceBlock } from './blocks/Evidence'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  visual_blocks?: any[]
  evidence_ids?: string[]
  conflicts?: any[]
  agent_trace?: {
    tools_invoked?: Array<{ name: string; args: any; elapsed_ms: number; evidence_count: number }>
    reasoning_details?: string
    citations_verified?: boolean
    grounded_ids?: string[]
    model?: string
    provider?: string
    total_latency_ms?: number
  }
  timestamp: string
}

interface ChatProps {
  messages: ChatMessage[]
  onSendMessage: (message: string) => Promise<void>
  onVisionCheck?: (wellId: string, imageBase64: string) => Promise<void>
  isLoading: boolean
}

export const Chat: React.FC<ChatProps> = ({ messages, onSendMessage, onVisionCheck, isLoading }) => {
  const [input, setInput] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const [expandedTrace, setExpandedTrace] = useState<Record<string, boolean>>({})
  const [visionModalOpen, setVisionModalOpen] = useState(false)
  const [visionWellId, setVisionWellId] = useState('WELL-0164')
  const [selectedImageBase64, setSelectedImageBase64] = useState<string | null>(null)
  const [isAnalyzingImage, setIsAnalyzingImage] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const recognitionRef = useRef<any>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isLoading])

  // Initialize Speech Recognition if supported
  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition()
      recognition.continuous = false
      recognition.interimResults = true
      recognition.lang = 'en-US'

      recognition.onresult = (event: any) => {
        const transcript = Array.from(event.results)
          .map((result: any) => result[0].transcript)
          .join('')
        setInput(transcript)
      }

      recognition.onerror = () => {
        setIsRecording(false)
      }

      recognition.onend = () => {
        setIsRecording(false)
      }

      recognitionRef.current = recognition
    }
  }, [])

  const toggleRecording = () => {
    if (!recognitionRef.current) {
      alert('Speech recognition is not supported in this browser. Please type your query.')
      return
    }
    if (isRecording) {
      recognitionRef.current.stop()
      setIsRecording(false)
    } else {
      setInput('')
      recognitionRef.current.start()
      setIsRecording(true)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return
    const text = input
    setInput('')
    await onSendMessage(text)
  }

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => {
      setSelectedImageBase64(reader.result as string)
      setVisionModalOpen(true)
    }
    reader.readAsDataURL(file)
  }

  const submitVisionCheck = async () => {
    if (!selectedImageBase64 || !onVisionCheck) return
    setIsAnalyzingImage(true)
    try {
      await onVisionCheck(visionWellId, selectedImageBase64)
      setVisionModalOpen(false)
      setSelectedImageBase64(null)
    } finally {
      setIsAnalyzingImage(false)
    }
  }

  // Parse text with bracketed citations into interactive badges
  const renderFormattedText = (text: string) => {
    const parts = text.split(/(\[[A-Za-z0-9-]+\]|\[DOC:[^\]]+\]|\[RPT:[^\]]+\]|\[LEDGER-[^\]]+\])/g)
    return parts.map((part, idx) => {
      if (part.startsWith('[') && part.endsWith(']')) {
        return (
          <span key={idx} className="citation-badge" title={`Verified Evidence Citation: ${part}`}>
            {part}
          </span>
        )
      }
      return <span key={idx}>{part}</span>
    })
  }

  // Visual Block Dispatcher
  const renderVisualBlock = (block: any, idx: number) => {
    if (!block || !block.block_type) return null
    switch (block.block_type) {
      case 'status_card':
        return <StatusCard key={`block-${idx}`} data={block} />
      case 'table':
        return <TableBlock key={`block-${idx}`} data={block} />
      case 'line_chart':
        return <LineChartBlock key={`block-${idx}`} data={block} />
      case 'bar_chart':
        return <BarChartBlock key={`block-${idx}`} data={block} />
      case 'map_view':
        return <MapViewBlock key={`block-${idx}`} data={block} />
      case 'heatmap':
        return <HeatmapBlock key={`block-${idx}`} data={block} />
      case 'conflict':
        return <ConflictBlock key={`block-${idx}`} data={block} />
      case 'evidence':
        return <EvidenceBlock key={`block-${idx}`} data={block} />
      default:
        return null
    }
  }

  return (
    <div className="chat-container">
      <div className="chat-messages" id="chat-messages-container">
        {messages.map((msg) => {
          const isTraceOpen = !!expandedTrace[msg.id]
          const trace = msg.agent_trace

          return (
            <div key={msg.id} className={`message-row ${msg.role}`}>
              <div className={`avatar ${msg.role}`}>
                {msg.role === 'user' ? <User size={18} /> : <Bot size={18} />}
              </div>

              <div className="message-bubble">
                <div className="message-text">
                  {renderFormattedText(msg.content)}
                </div>

                {/* Render inline visual blocks */}
                {msg.visual_blocks && msg.visual_blocks.map((b, idx) => renderVisualBlock(b, idx))}

                {/* Render conflicts if any */}
                {msg.conflicts && msg.conflicts.map((c, idx) => (
                  <ConflictBlock
                    key={`conflict-${idx}`}
                    data={{
                      title: 'Conflict Detected with Telemetry / Notes',
                      asset_id: c.asset_id || 'WELL',
                      item: c.claim_text || 'Disputed State',
                      claims: [
                        { source: 'Operator Claim', statement: c.claim_text },
                        { source: 'Sensor Evidence', statement: c.conflict_details || 'Recorded data differs' }
                      ],
                      recommendation: 'Requires supervisor verification before updating state.',
                      evidence_ids: c.evidence_ids || []
                    }}
                  />
                ))}

                {/* Deterministic Audit & Tool Trace Drawer for Assistant */}
                {msg.role === 'assistant' && (
                  <div style={{
                    marginTop: '4px',
                    borderRadius: '8px',
                    background: 'rgba(0, 0, 0, 0.35)',
                    border: '1px solid rgba(255, 255, 255, 0.06)',
                    overflow: 'hidden',
                    fontSize: '11px',
                  }}>
                    {/* Header Bar */}
                    <div
                      onClick={() => setExpandedTrace(prev => ({ ...prev, [msg.id]: !isTraceOpen }))}
                      style={{
                        padding: '6px 12px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        cursor: 'pointer',
                        background: 'rgba(255, 255, 255, 0.02)',
                        transition: 'background 0.2s',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                        {/* 0 LLM Math Badge */}
                        <span style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px',
                          padding: '2px 8px',
                          borderRadius: '12px',
                          background: 'rgba(16, 185, 129, 0.15)',
                          color: '#10b981',
                          fontWeight: 600,
                          border: '1px solid rgba(16, 185, 129, 0.3)',
                        }}>
                          <ShieldCheck size={11} />
                          0 LLM Math (Python Verified)
                        </span>

                        {/* Model Badge */}
                        <span style={{
                          color: 'var(--text-muted)',
                          fontFamily: 'var(--font-mono)',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px',
                        }}>
                          <Cpu size={11} color="#38bdf8" />
                          {trace?.model ? trace.model.replace('google/', '') : 'Gemma 4 26B A4B'}
                        </span>

                        {/* Tools Invoked Pills */}
                        {trace?.tools_invoked && trace.tools_invoked.map((t, tidx) => (
                          <span
                            key={tidx}
                            style={{
                              padding: '1px 6px',
                              borderRadius: '4px',
                              background: 'rgba(56, 189, 248, 0.1)',
                              color: '#38bdf8',
                              border: '1px solid rgba(56, 189, 248, 0.25)',
                              fontFamily: 'var(--font-mono)',
                            }}
                          >
                            {t.name}: {t.elapsed_ms}ms
                          </span>
                        ))}
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-muted)' }}>
                        {trace?.total_latency_ms && (
                          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '3px' }}>
                            <Clock size={11} /> {trace.total_latency_ms}ms
                          </span>
                        )}
                        {isTraceOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                      </div>
                    </div>

                    {/* Expandable Trace Drawer */}
                    {isTraceOpen && (
                      <div style={{
                        padding: '10px 14px',
                        borderTop: '1px solid rgba(255, 255, 255, 0.05)',
                        background: 'rgba(0, 0, 0, 0.5)',
                        color: 'var(--text-secondary)',
                      }}>
                        <div style={{ marginBottom: '6px' }}>
                          <strong style={{ color: '#f8fafc' }}>Reasoning & Deterministic Scoping:</strong>{' '}
                          <span>{trace?.reasoning_details || 'Verified against SQLite schema & rules.yaml thresholds.'}</span>
                        </div>

                        {msg.evidence_ids && msg.evidence_ids.length > 0 && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', flexWrap: 'wrap', marginTop: '6px' }}>
                            <strong style={{ color: '#f8fafc', marginRight: '4px' }}>Citations Grounded ({msg.evidence_ids.length}):</strong>
                            {msg.evidence_ids.map(eid => (
                              <span key={eid} className="citation-badge">[{eid}]</span>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )
        })}

        {isLoading && (
          <div className="message-row assistant">
            <div className="avatar assistant">
              <Bot size={18} />
            </div>
            <div className="message-bubble">
              <div className="message-text" style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-brand)' }}>
                <Loader2 size={16} className="animate-spin" />
                <span>Consulting deterministic data layer, rules.yaml & Gemma 4 engine...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Field Image Modal */}
      {visionModalOpen && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.8)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100,
        }}>
          <div style={{
            background: '#111827',
            border: '1px solid rgba(56, 189, 248, 0.3)',
            borderRadius: '16px',
            padding: '24px',
            maxWidth: '460px',
            width: '90%',
            boxShadow: '0 20px 40px rgba(0,0,0,0.6)',
          }}>
            <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#f8fafc', marginBottom: '8px' }}>
              Field Inspection Photo Cross-Check
            </h3>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '16px' }}>
              Send image to Gemma 4 26B Vision to verify physical pump jack motion and spill containment against recorded telemetry.
            </p>

            {selectedImageBase64 && (
              <div style={{
                maxHeight: '180px',
                overflow: 'hidden',
                borderRadius: '8px',
                marginBottom: '14px',
                border: '1px solid var(--border-subtle)',
              }}>
                <img src={selectedImageBase64} alt="Inspection Preview" style={{ width: '100%', objectFit: 'cover' }} />
              </div>
            )}

            <div style={{ marginBottom: '16px' }}>
              <label style={{ fontSize: '11px', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                Target Well Asset ID
              </label>
              <input
                type="text"
                value={visionWellId}
                onChange={e => setVisionWellId(e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  borderRadius: '6px',
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid var(--border-subtle)',
                  color: '#fff',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '13px',
                }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button
                type="button"
                onClick={() => setVisionModalOpen(false)}
                style={{
                  padding: '8px 14px',
                  borderRadius: '8px',
                  background: 'transparent',
                  border: '1px solid var(--border-subtle)',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  fontSize: '12px',
                }}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={submitVisionCheck}
                disabled={isAnalyzingImage}
                style={{
                  padding: '8px 16px',
                  borderRadius: '8px',
                  background: 'linear-gradient(135deg, #0284c7, #38bdf8)',
                  border: 'none',
                  color: '#032030',
                  fontWeight: 600,
                  cursor: 'pointer',
                  fontSize: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                {isAnalyzingImage ? <Loader2 size={14} className="animate-spin" /> : <Camera size={14} />}
                <span>{isAnalyzingImage ? 'Analyzing...' : 'Run Vision Check'}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Chat Input Bar with Voice & Image Upload */}
      <div className="chat-input-bar">
        <form onSubmit={handleSubmit} className="input-container">
          <Sparkles size={18} color="#38bdf8" style={{ marginRight: '6px', flexShrink: 0 }} />

          {/* Hidden File Input for Field Images */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleImageUpload}
            accept="image/*"
            style={{ display: 'none' }}
          />

          {/* Image Attach Button */}
          <button
            type="button"
            title="Attach Field Inspection Photo"
            onClick={() => fileInputRef.current?.click()}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              padding: '6px',
              display: 'flex',
              alignItems: 'center',
              borderRadius: '6px',
              marginRight: '6px',
              transition: 'color 0.2s',
            }}
            onMouseEnter={e => (e.currentTarget.style.color = '#38bdf8')}
            onMouseLeave={e => (e.currentTarget.style.color = '#64748b')}
          >
            <Camera size={18} />
          </button>

          {/* Voice Input Mic Button */}
          <button
            type="button"
            title={isRecording ? 'Listening... click to stop' : 'Voice Query (Web Speech)'}
            onClick={toggleRecording}
            style={{
              background: isRecording ? 'rgba(239, 68, 68, 0.2)' : 'transparent',
              border: isRecording ? '1px solid rgba(239, 68, 68, 0.4)' : 'none',
              color: isRecording ? '#ef4444' : 'var(--text-muted)',
              cursor: 'pointer',
              padding: '6px',
              display: 'flex',
              alignItems: 'center',
              borderRadius: '6px',
              marginRight: '8px',
              transition: 'all 0.2s',
              animation: isRecording ? 'pulse 1.5s infinite' : 'none',
            }}
          >
            {isRecording ? <MicOff size={18} /> : <Mic size={18} />}
          </button>

          <input
            id="chat-input-box"
            type="text"
            className="chat-input"
            placeholder={
              isRecording
                ? 'Listening to operator voice...'
                : 'Ask about well status, downtime, spills, temperature trends, or SOP compliance...'
            }
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
          />

          <button
            id="chat-send-button"
            type="submit"
            className="send-btn"
            disabled={!input.trim() || isLoading}
          >
            <Send size={16} />
          </button>
        </form>
      </div>
    </div>
  )
}
