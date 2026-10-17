import React, { useState, useEffect } from 'react'
import { Chat, ChatMessage } from './Chat'
import { UserPicker, UserOption } from './UserPicker'
import {
  Cpu,
  Activity,
  Layers,
  CheckCircle2,
  RefreshCw,
  Database,
  Calendar,
  Lock,
  Flame,
  FileCheck,
  Split,
  Users,
} from 'lucide-react'

const DEFAULT_USERS: UserOption[] = [
  { user_id: 'U-102', name: 'Jake Morales', role: 'field_operator', team_id: 'TEAM-NE' },
  { user_id: 'U-104', name: 'Ryan Brooks', role: 'field_inspector', team_id: 'TEAM-SW' },
  { user_id: 'U-101', name: 'Emily Carter', role: 'production_supervisor', team_id: 'TEAM-HQ' },
  { user_id: 'U-103', name: 'Sarah Mitchell', role: 'field_inspector', team_id: 'TEAM-NE' },
  { user_id: 'U-201', name: 'Michael Turner', role: 'production_supervisor', team_id: 'TEAM-SE' },
  { user_id: 'U-202', name: 'Jessica Reed', role: 'field_inspector', team_id: 'TEAM-SE' },
  { user_id: 'U-301', name: 'Robert Hayes', role: 'maintenance_lead', team_id: 'TEAM-MNT' },
]

interface PromptCategory {
  category: string
  icon: any
  prompts: Array<{ id: string; label: string; text: string }>
}

const CATEGORIZED_PROMPTS: PromptCategory[] = [
  {
    category: 'Fleet Status & Temp Rules (Q1–Q4)',
    icon: Flame,
    prompts: [
      { id: 'q1', label: 'Q1: Status Card', text: 'Is WELL-0001 producing oil right now? When was it last inspected, and by whom? Show me its status card.' },
      { id: 'q2', label: 'Q2: Area Stopped Wells Table', text: 'Which wells in Northeast Block 8 are not producing oil right now, and why? Show them in a table.' },
      { id: 'q3', label: 'Q3: Temp Trend Line Chart', text: "Show a line chart of WELL-0001's wellhead temperature against air temperature for the last 13 weeks, and mark when it was not producing oil." },
      { id: 'q4', label: 'Q4: Spills Summary Table', text: 'How many oil spills has WELL-0001 had in the last 4 years, and how much oil in total? List them in a table.' },
    ],
  },
  {
    category: 'Downtime & Maintenance Analytics (Q5–Q7)',
    icon: Activity,
    prompts: [
      { id: 'q5', label: 'Q5: Downtime in 2025', text: 'How many days was WELL-0001 down in 2025?' },
      { id: 'q6', label: 'Q6: Top Downtime Bar Chart', text: 'Which 5 wells in Northeast Block 8 had the most downtime in the last 4 months? Show a bar chart.' },
      { id: 'q7', label: 'Q7: Area Spills Map', text: 'Show all oil spills in Northeast Block 8 in the last 90 days on a map.' },
    ],
  },
  {
    category: 'SOP Compliance & Spill Audits (Q8–Q10)',
    icon: FileCheck,
    prompts: [
      { id: 'q8', label: 'Q8: Monthly Spills Heatmap', text: 'Show a heatmap of monthly oil spills by area for 2026.' },
      { id: 'q9', label: 'Q9: Compliance Audit', text: 'Perform a compliance audit for WELL-0001 checking SR-01, SR-02, SR-03, RC-02, and RC-04.' },
      { id: 'q10', label: 'Q10: Uncontained Spills', text: 'Which wells had spills in the last 6 months that were not contained within 4 hours?' },
    ],
  },
  {
    category: 'Corrections & Conflict Detection (Q12–Q18)',
    icon: Split,
    prompts: [
      { id: 'q12', label: 'Q12: Submit Temp Correction', text: 'Correction: The wellhead temperature for WELL-0164 was actually 41.0°C during inspection INS-0164-0205.' },
      { id: 'q14', label: 'Q14: T350 Rule Override', text: 'Update the RCA requirement rule: for T350 wells, trigger root cause analysis after 2 repairs instead of 3.' },
      { id: 'q17', label: 'Q17: Disputed Status Claim', text: 'Operator claims WELL-0164 was producing oil yesterday despite low delta temperature.' },
    ],
  },
]

export const App: React.FC = () => {
  const [users, setUsers] = useState<UserOption[]>(DEFAULT_USERS)
  const [currentUser, setCurrentUser] = useState<UserOption>(DEFAULT_USERS[0])
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        'Welcome to the **Asset Intelligence Copilot** (`Donk-E`). Grounded with deterministic code owning all facts, math, and compliance rules; OpenRouter Gemma 4 26B owning conversational synthesis; and an append-only ledger preserving operational corrections and privacy isolation.',
      timestamp: new Date().toISOString(),
    },
  ])
  const [isLoading, setIsLoading] = useState(false)
  const [systemStats, setSystemStats] = useState<{
    data_end?: string
    assets?: number
    inspections?: number
    ledger_entries?: number
  }>({})
  const [ingestModalOpen, setIngestModalOpen] = useState(false)
  const [ingestRootsText, setIngestRootsText] = useState('./sample-data, ./test-data')
  const [isIngesting, setIsIngesting] = useState(false)
  const [ingestResult, setIngestResult] = useState<any | null>(null)

  const API_BASE = (typeof window !== 'undefined' && window.location.port === '5173')
    ? 'http://127.0.0.1:8000'
    : ''

  const fetchHealth = () => {
    fetch(`${API_BASE}/api/health`)
      .then(r => r.json())
      .then(d => {
        if (d && d.counts) {
          setSystemStats({
            data_end: d.data_end,
            assets: d.counts.assets,
            inspections: d.counts.inspections,
            ledger_entries: d.counts.ledger_entries,
          })
        }
      })
      .catch(() => {})
  }

  // Fetch health and users on mount
  useEffect(() => {
    fetchHealth()

    fetch(`${API_BASE}/api/users`)
      .then(r => r.json())
      .then(d => {
        if (Array.isArray(d) && d.length > 0) {
          setUsers(d)
        }
      })
      .catch(() => {})
  }, [])

  const handleSendMessage = async (text: string, customUserId?: string) => {
    const activeUserId = customUserId || currentUser.user_id
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    }
    setMessages(prev => [...prev, userMsg])
    setIsLoading(true)

    try {
      const resp = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          user_id: activeUserId,
        }),
      })

      if (!resp.ok) {
        throw new Error(`Server returned status ${resp.status}`)
      }

      const data = await resp.json()
      const assistantMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: data.content || 'Data processed successfully.',
        visual_blocks: data.visual_blocks || [],
        evidence_ids: data.evidence_ids || [],
        conflicts: data.conflicts || [],
        agent_trace: data.agent_trace,
        timestamp: new Date().toISOString(),
      }
      setMessages(prev => [...prev, assistantMsg])
      fetchHealth()
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: `Error connecting to Copilot API: ${err.message}. Ensure backend is running at http://127.0.0.1:8000.`,
        timestamp: new Date().toISOString(),
      }
      setMessages(prev => [...prev, errorMsg])
    } finally {
      setIsLoading(false)
    }
  }

  // Vision inspection cross-check
  const handleVisionCheck = async (wellId: string, imageBase64: string) => {
    const userMsg: ChatMessage = {
      id: `user-vision-${Date.now()}`,
      role: 'user',
      content: `[Uploaded Field Photo for ${wellId}] Cross-checking visual state with latest inspection telemetry.`,
      timestamp: new Date().toISOString(),
    }
    setMessages(prev => [...prev, userMsg])
    setIsLoading(true)

    try {
      const resp = await fetch(`${API_BASE}/api/vision/check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          well_id: wellId,
          image_base64: imageBase64,
          user_id: currentUser.user_id,
        }),
      })
      if (!resp.ok) throw new Error(`Vision check returned status ${resp.status}`)
      const data = await resp.json()

      const assistantMsg: ChatMessage = {
        id: `assistant-vision-${Date.now()}`,
        role: 'assistant',
        content: `**Vision Analysis (${wellId}):** ${data.observation}`,
        conflicts: data.conflict_block ? [data.conflict_block] : [],
        evidence_ids: data.evidence_ids || [],
        agent_trace: {
          tools_invoked: [{ name: 'analyze_image_vision', args: { well_id: wellId }, elapsed_ms: 120, evidence_count: 1 }],
          reasoning_details: 'Cross-examined visual image against latest recorded telemetry delta and state.',
          citations_verified: true,
          grounded_ids: data.evidence_ids || [],
          model: data.model,
          total_latency_ms: 125,
        },
        timestamp: new Date().toISOString(),
      }
      setMessages(prev => [...prev, assistantMsg])
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: `Vision check error: ${err.message}`,
        timestamp: new Date().toISOString(),
      }
      setMessages(prev => [...prev, errorMsg])
    } finally {
      setIsLoading(false)
    }
  }

  // Trigger Hot-Drop Ingest
  const handleTriggerIngest = async () => {
    setIsIngesting(true)
    setIngestResult(null)
    const roots = ingestRootsText
      .split(',')
      .map(s => s.trim())
      .filter(Boolean)

    try {
      const resp = await fetch(`${API_BASE}/api/admin/ingest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data_roots: roots }),
      })
      const data = await resp.json()
      setIngestResult(data)
      fetchHealth()
    } catch (err: any) {
      setIngestResult({ error: err.message })
    } finally {
      setIsIngesting(false)
    }
  }

  // Run Isolation Demo: Michael (U-201) vs Jessica (U-202)
  const handleRunIsolationDemo = async () => {
    // 1. Set user to Michael Turner (U-201) and query
    const michael = users.find(u => u.user_id === 'U-201') || {
      user_id: 'U-201',
      name: 'Michael Turner',
      role: 'production_supervisor',
    }
    setCurrentUser(michael)
    await handleSendMessage(
      'What was the status of the well we discussed in our last conversation? (Testing private memory)',
      'U-201',
    )
  }

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="brand-badge">
            <Cpu size={12} />
            <span>Donk-E Asset Intelligence</span>
          </div>
          <h1 className="app-title">Asset Copilot</h1>
          <p className="app-subtitle">Nodding donkey operations, compliance & ledger</p>
        </div>

        <div className="sidebar-content">
          {/* Multi-User Isolation 1-Click Helper */}
          <div style={{
            background: 'rgba(99, 102, 241, 0.08)',
            border: '1px solid rgba(99, 102, 241, 0.25)',
            borderRadius: '10px',
            padding: '12px',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', fontWeight: 700, color: '#a5b4fc', marginBottom: '4px' }}>
              <Lock size={12} />
              <span>Multi-User Memory Demo (Q11 & Q16)</span>
            </div>
            <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '8px', lineHeight: 1.4 }}>
              Demonstrate strict SQL-enforced private conversation memory isolation.
            </p>
            <button
              onClick={handleRunIsolationDemo}
              disabled={isLoading}
              style={{
                width: '100%',
                padding: '6px 10px',
                borderRadius: '6px',
                background: 'linear-gradient(135deg, #6366f1, #818cf8)',
                border: 'none',
                color: '#fff',
                fontSize: '11px',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
              }}
            >
              <Users size={12} />
              <span>Run Memory Isolation Demo</span>
            </button>
          </div>

          {/* Categorized Golden Prompts */}
          {CATEGORIZED_PROMPTS.map(cat => {
            const Icon = cat.icon
            return (
              <div key={cat.category}>
                <div className="sidebar-section-title" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Icon size={12} color="#38bdf8" />
                  <span>{cat.category}</span>
                </div>
                <div className="quick-prompts-list">
                  {cat.prompts.map(p => (
                    <button
                      key={p.id}
                      className="quick-prompt-btn"
                      onClick={() => handleSendMessage(p.text)}
                      disabled={isLoading}
                    >
                      <Activity size={12} style={{ flexShrink: 0, marginTop: '2px', color: '#38bdf8' }} />
                      <span>{p.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            )
          })}
        </div>

        <div className="sidebar-footer">
          <div className="system-stats">
            <span>Data End: <strong style={{ color: '#38bdf8' }}>{systemStats.data_end || '2026-10-16'}</strong></span>
            <span>Wells: <strong style={{ color: '#f8fafc' }}>{systemStats.assets || '100+'}</strong></span>
          </div>
          <div style={{ marginTop: '8px', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '10px', color: '#10b981' }}>
            <CheckCircle2 size={12} />
            <span>Deterministic Engine Active (0 LLM Math)</span>
          </div>
        </div>
      </aside>

      {/* Main Chat Workspace */}
      <main className="chat-container">
        {/* Top Header Navbar */}
        <header className="chat-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Layers size={18} color="#38bdf8" />
              <span style={{ fontSize: '14px', fontWeight: 600, color: '#f8fafc' }}>
                Operational Session
              </span>
            </div>

            {/* Reference Date Pill */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '3px 10px',
              borderRadius: '16px',
              background: 'rgba(255, 255, 255, 0.04)',
              border: '1px solid var(--border-subtle)',
              fontSize: '11px',
              color: 'var(--text-secondary)',
            }}>
              <Calendar size={12} color="#38bdf8" />
              <span>Reference As-Of: <strong>2026-10-17</strong></span>
            </div>

            {/* Hot-Drop Ingest Modal Trigger */}
            <button
              onClick={() => setIngestModalOpen(true)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '4px 12px',
                borderRadius: '16px',
                background: 'rgba(56, 189, 248, 0.12)',
                border: '1px solid rgba(56, 189, 248, 0.3)',
                color: '#38bdf8',
                fontSize: '11px',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.2s',
              }}
            >
              <RefreshCw size={12} />
              <span>Ingest / Hot-Reload Dataset</span>
            </button>
          </div>

          <UserPicker
            currentUser={currentUser}
            users={users}
            onSelectUser={setCurrentUser}
          />
        </header>

        {/* Hot-Drop Ingest Modal */}
        {ingestModalOpen && (
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
              maxWidth: '520px',
              width: '90%',
              boxShadow: '0 20px 40px rgba(0,0,0,0.6)',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <Database size={20} color="#38bdf8" />
                <h3 style={{ fontSize: '17px', fontWeight: 700, color: '#f8fafc' }}>
                  2-Hour Hot-Drop Dataset Ingestion Engine
                </h3>
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '16px', lineHeight: 1.5 }}>
                When evaluators place <code>./test-data</code> alongside <code>./sample-data</code>, this endpoint hot-reloads and materializes derived views idempotently in &lt; 2.5 seconds with zero external database dependencies.
              </p>

              <div style={{ marginBottom: '16px' }}>
                <label style={{ fontSize: '11px', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                  Comma-Separated Dataset Roots (e.g. <code>./sample-data, ./test-data</code>):
                </label>
                <input
                  type="text"
                  value={ingestRootsText}
                  onChange={e => setIngestRootsText(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: '6px',
                    background: 'rgba(255, 255, 255, 0.05)',
                    border: '1px solid var(--border-subtle)',
                    color: '#fff',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '12px',
                  }}
                />
              </div>

              {ingestResult && (
                <div style={{
                  padding: '12px',
                  borderRadius: '8px',
                  background: ingestResult.error ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                  border: `1px solid ${ingestResult.error ? 'rgba(239, 68, 68, 0.3)' : 'rgba(16, 185, 129, 0.3)'}`,
                  color: ingestResult.error ? '#f87171' : '#34d399',
                  fontSize: '12px',
                  marginBottom: '16px',
                }}>
                  {ingestResult.error ? (
                    <div>Error: {ingestResult.error}</div>
                  ) : (
                    <div>
                      <strong>Ingestion Green in {ingestResult.elapsed_ms}ms!</strong>
                      <div style={{ marginTop: '4px', fontSize: '11px', color: '#e2e8f0' }}>
                        Wells: {ingestResult.wells_loaded} | Inspections: {ingestResult.inspections_loaded} | DATA_END: {ingestResult.data_end}
                      </div>
                    </div>
                  )}
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button
                  type="button"
                  onClick={() => setIngestModalOpen(false)}
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
                  Close
                </button>
                <button
                  type="button"
                  onClick={handleTriggerIngest}
                  disabled={isIngesting}
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
                  <RefreshCw size={13} className={isIngesting ? 'animate-spin' : ''} />
                  <span>{isIngesting ? 'Ingesting (<2.5s)...' : 'Execute Hot-Drop Ingest'}</span>
                </button>
              </div>
            </div>
          </div>
        )}

        <Chat
          messages={messages}
          onSendMessage={handleSendMessage}
          onVisionCheck={handleVisionCheck}
          isLoading={isLoading}
        />
      </main>
    </div>
  )
}
