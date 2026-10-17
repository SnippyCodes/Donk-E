import React, { useState, useEffect, useRef } from 'react'
import {
  Play,
  Pause,
  RotateCcw,
  SkipForward,
  SkipBack,
  Volume2,
  VolumeX,
  ShieldCheck,
  ArrowRight,
} from 'lucide-react'

export interface BragTourProps {
  onJumpToChat: (prompt: string, userId?: string) => void
  onSwitchToConsole: () => void
}

interface Chapter {
  id: number
  title: string
  subtitle: string
  timeRange: string
  sentences: string[]
  narrationText: string
}

const CHAPTERS: Chapter[] = [
  {
    id: 1,
    title: 'Architecture & Zero-LLM-Math Invariant',
    subtitle: 'Deterministic Python/SQLite core with 100% regex report facts & FTS5 indexing',
    timeRange: '0:00 – 0:25',
    sentences: [
      'Welcome to the Donk-E Asset Intelligence Copilot.',
      'Our core engineering principle is absolute truth separation: deterministic Python and SQLite code own one hundred percent of the domain facts, Gemma 4 owns conversational synthesis, and an append-only ledger owns memory.',
      'Our multi-root ingest processed thirty-nine thousand inspections, five thousand repairs, and parsed one thousand five hundred and nine free-text repair reports with one hundred percent coverage in just 2.54 seconds with zero external LLM calls.',
      'Gemma 4 never counts, sums, or calculates dates. All metrics are computed strictly by deterministic domain queries.'
    ],
    narrationText:
      'Welcome to the Donk-E Asset Intelligence Copilot. Our core engineering principle is absolute truth separation: deterministic Python and SQLite code own one hundred percent of the domain facts, Gemma 4 owns conversational synthesis, and an append-only ledger owns memory. Our multi-root ingest processed thirty-nine thousand inspections, five thousand repairs, and parsed one thousand five hundred and nine free-text repair reports with one hundred percent coverage in just 2.54 seconds with zero external LLM calls. Gemma 4 never counts, sums, or calculates dates. All metrics are computed strictly by deterministic domain queries.'
  },
  {
    id: 2,
    title: 'Truth Hierarchy & Cross-Source Synthesis',
    subtitle: 'Thermal wellhead delta-T thresholds, stale status flagging & 7-day downtime rules',
    timeRange: '0:25 – 0:55',
    sentences: [
      'Notice how numbers, documents, and operator notes combine into an unambiguous truth hierarchy.',
      'In Question 1, recorded metadata claims Well 0001 is active. But our effective inspection engine checks the wellhead temperature delta.',
      'Because the delta is 3.2 degrees Celsius, well below the fifteen degree threshold from rules dot yaml, the copilot immediately flags the status as stale and surfaces Jake Morales\'s planned shut-in note.',
      'In Question 5, downtime calculation ignores self-reported maintenance hours and strictly computes seven days per non-producing inspection.',
      'And in Questions 9 and 10, the engine joins spills with free-text repair reports to catch four-hour containment breaches under SOP SR-02.'
    ],
    narrationText:
      'Notice how numbers, documents, and operator notes combine into an unambiguous truth hierarchy. In Question 1, recorded metadata claims Well 0001 is active. But our effective inspection engine checks the wellhead temperature delta. Because the delta is 3.2 degrees Celsius, well below the fifteen degree threshold from rules dot yaml, the copilot immediately flags the status as stale and surfaces Jake Morales\'s planned shut-in note. In Question 5, downtime calculation ignores self-reported maintenance hours and strictly computes seven days per non-producing inspection. And in Questions 9 and 10, the engine joins spills with free-text repair reports to catch four-hour containment breaches under SOP SR-02.'
  },
  {
    id: 3,
    title: 'Two-Level Memory & Scoped Overrides',
    subtitle: 'Append-only ledger with strict scope hierarchy and private per-user conversation isolation',
    timeRange: '0:55 – 1:25',
    sentences: [
      'Look at our two-level memory system.',
      'Raw database tables are permanently immutable. All corrections and operational claims append to our ledger.',
      'In Question 12, when Michael Turner corrects Well 0164\'s wellhead temperature to forty-one degrees, the ledger updates and re-evaluates Question 2 in under twenty milliseconds.',
      'In Question 13, Michael\'s spill volume correction to 5.4 barrels cascades into an overdue regulatory violation.',
      'In Question 14, Michael\'s two-repair RCA override applies strictly to T350 wells like Well 0120, without leaking to T200 wells.',
      'And in Question 16, code-enforced user privacy ensures Jessica Reed receives zero history from Michael\'s private session.'
    ],
    narrationText:
      'Look at our two-level memory system. Raw database tables are permanently immutable. All corrections and operational claims append to our ledger. In Question 12, when Michael Turner corrects Well 0164\'s wellhead temperature to forty-one degrees, the ledger updates and re-evaluates Question 2 in under twenty milliseconds. In Question 13, Michael\'s spill volume correction to 5.4 barrels cascades into an overdue regulatory violation. In Question 14, Michael\'s two-repair RCA override applies strictly to T350 wells like Well 0120, without leaking to T200 wells. And in Question 16, code-enforced user privacy ensures Jessica Reed receives zero history from Michael\'s private session.'
  },
  {
    id: 4,
    title: 'Conflict Honesty & Disputed Claims',
    subtitle: 'Contradictory operator claims marked unconfirmed and multi-note disputes surfaced transparently',
    timeRange: '1:25 – 1:50',
    sentences: [
      'Our copilot never hallucinates consensus when humans disagree.',
      'When operator claims contradict telemetry, the claims engine preserves the disagreement.',
      'In Question 17, Tyler Hughes claimed Well 0175 was running fine. But empirical inspection data showed a 0.4 degree delta, so the claim was marked unconfirmed and both sides were cited.',
      'In Question 18, when two operators disputed whether the August 20 spill at Well 0101 was crude oil or produced water, the copilot verified the repair work order and cited both notes transparently.'
    ],
    narrationText:
      'Our copilot never hallucinates consensus when humans disagree. When operator claims contradict telemetry, the claims engine preserves the disagreement. In Question 17, Tyler Hughes claimed Well 0175 was running fine. But empirical inspection data showed a 0.4 degree delta, so the claim was marked unconfirmed and both sides were cited. In Question 18, when two operators disputed whether the August 20 spill at Well 0101 was crude oil or produced water, the copilot verified the repair work order and cited both notes transparently.'
  },
  {
    id: 5,
    title: '4-Layer QA Pipeline & Failure Post-Mortem',
    subtitle: 'Deterministic 18/18 invariant validation in 2.44s and the 4 real bugs caught & resolved',
    timeRange: '1:50 – 2:15',
    sentences: [
      'Quality assurance is mathematically validated across four pillars: invariant gates, strict citation set membership, generative UI typing, and stateful memory carry-forward.',
      'All eighteen golden scenarios pass sequentially in 2.44 seconds.',
      'During real testing, our QA suite caught four critical failures: Gemma 4 native tool call token leakage, keyword argument drift, duplicate markdown tables, and rate-limit latency.',
      'We resolved each with an AST regex parser, universal parameter normalization, markdown table stripping, and inline visual consolidation.'
    ],
    narrationText:
      'Quality assurance is mathematically validated across four pillars: invariant gates, strict citation set membership, generative UI typing, and stateful memory carry-forward. All eighteen golden scenarios pass sequentially in 2.44 seconds. During real testing, our QA suite caught four critical failures: Gemma 4 native tool call token leakage, keyword argument drift, duplicate markdown tables, and rate-limit latency. We resolved each with an AST regex parser, universal parameter normalization, markdown table stripping, and inline visual consolidation.'
  },
  {
    id: 6,
    title: 'Live Interactive Copilot Triggers',
    subtitle: 'Rich generative UI blocks with zero-latency pre-compiled operator workflows',
    timeRange: '2:15 – 2:30',
    sentences: [
      'Finally, experience our generative UI blocks.',
      'Every response dynamically renders rich, typed components: from interactive temperature trend lines and downtime bar charts to geospatial spill maps, area heatmaps, and conflict blocks.',
      'Click any scenario button below to jump directly into the live operational console with pre-loaded prompts.'
    ],
    narrationText:
      'Finally, experience our generative UI blocks. Every response dynamically renders rich, typed components: from interactive temperature trend lines and downtime bar charts to geospatial spill maps, area heatmaps, and conflict blocks. Click any scenario button below to jump directly into the live operational console with pre-loaded prompts.'
  }
]

export const BragTour: React.FC<BragTourProps> = ({ onJumpToChat, onSwitchToConsole }) => {
  const [isPlaying, setIsPlaying] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [activeChapterIndex, setActiveChapterIndex] = useState(0)
  const [currentSentenceIndex, setCurrentSentenceIndex] = useState(0)
  const [speechRate, setSpeechRate] = useState<number>(1.05)
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([])
  const [selectedVoiceIndex, setSelectedVoiceIndex] = useState<number>(0)
  const [isMuted, setIsMuted] = useState(false)

  const isTourActiveRef = useRef(false)
  const synthRef = useRef<SpeechSynthesis | null>(null)
  const timerRef = useRef<any>(null)

  useEffect(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      synthRef.current = window.speechSynthesis
      const loadVoices = () => {
        const available = window.speechSynthesis.getVoices()
        if (available.length > 0) {
          // Filter english voices
          const english = available.filter(v => v.lang.startsWith('en'))
          const list = english.length > 0 ? english : available
          setVoices(list)

          // Pick natural sounding voice if available
          const preferredIdx = list.findIndex(
            v =>
              v.name.includes('Google') ||
              v.name.includes('Natural') ||
              v.name.includes('Aria') ||
              v.name.includes('Samantha') ||
              v.name.includes('Jenny')
          )
          if (preferredIdx !== -1) {
            setSelectedVoiceIndex(preferredIdx)
          }
        }
      }

      loadVoices()
      window.speechSynthesis.onvoiceschanged = loadVoices
    }

    return () => {
      if (synthRef.current) {
        synthRef.current.cancel()
      }
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [])

  // Scroll active chapter into view smoothly
  const scrollToChapter = (chapterId: number) => {
    const el = document.getElementById(`chapter-${chapterId}`)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }

  // Voice playback loop: speaks sentences sequentially
  const speakSentence = (chapterIdx: number, sentenceIdx: number) => {
    if (!isTourActiveRef.current) return

    const chapter = CHAPTERS[chapterIdx]
    if (!chapter) {
      handleStopTour()
      return
    }

    // Scroll to chapter card when beginning a chapter
    if (sentenceIdx === 0) {
      scrollToChapter(chapter.id)
    }

    const sentences = chapter.sentences
    if (sentenceIdx >= sentences.length) {
      // Advance to next chapter
      if (chapterIdx + 1 < CHAPTERS.length) {
        setActiveChapterIndex(chapterIdx + 1)
        setCurrentSentenceIndex(0)
        speakSentence(chapterIdx + 1, 0)
      } else {
        handleStopTour()
      }
      return
    }

    setActiveChapterIndex(chapterIdx)
    setCurrentSentenceIndex(sentenceIdx)

    if (isMuted || !synthRef.current) {
      // Timer-based fallback for muted / no audio mode
      const durationMs = Math.max(2500, (sentences[sentenceIdx].length / 15) * 1000 / speechRate)
      timerRef.current = setTimeout(() => {
        if (isTourActiveRef.current) {
          speakSentence(chapterIdx, sentenceIdx + 1)
        }
      }, durationMs)
      return
    }

    synthRef.current.cancel()
    const utterance = new SpeechSynthesisUtterance(sentences[sentenceIdx])
    utterance.rate = speechRate
    if (voices[selectedVoiceIndex]) {
      utterance.voice = voices[selectedVoiceIndex]
    }

    utterance.onend = () => {
      if (isTourActiveRef.current) {
        // Small pause between sentences
        timerRef.current = setTimeout(() => {
          speakSentence(chapterIdx, sentenceIdx + 1)
        }, 120)
      }
    }

    utterance.onerror = () => {
      if (isTourActiveRef.current) {
        speakSentence(chapterIdx, sentenceIdx + 1)
      }
    }

    synthRef.current.speak(utterance)
  }

  const handleStartTour = (startFromChapter = 0) => {
    if (synthRef.current) {
      synthRef.current.cancel()
    }
    if (timerRef.current) clearTimeout(timerRef.current)

    isTourActiveRef.current = true
    setIsPlaying(true)
    setIsPaused(false)
    setActiveChapterIndex(startFromChapter)
    setCurrentSentenceIndex(0)
    speakSentence(startFromChapter, 0)
  }

  const handlePauseResume = () => {
    if (!isPlaying) return
    if (isPaused) {
      setIsPaused(false)
      isTourActiveRef.current = true
      speakSentence(activeChapterIndex, currentSentenceIndex)
    } else {
      setIsPaused(true)
      isTourActiveRef.current = false
      if (synthRef.current) {
        synthRef.current.cancel()
      }
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }

  const handleNextChapter = () => {
    const nextIdx = Math.min(CHAPTERS.length - 1, activeChapterIndex + 1)
    if (isPlaying) {
      handleStartTour(nextIdx)
    } else {
      setActiveChapterIndex(nextIdx)
      setCurrentSentenceIndex(0)
      scrollToChapter(CHAPTERS[nextIdx].id)
    }
  }

  const handlePrevChapter = () => {
    const prevIdx = Math.max(0, activeChapterIndex - 1)
    if (isPlaying) {
      handleStartTour(prevIdx)
    } else {
      setActiveChapterIndex(prevIdx)
      setCurrentSentenceIndex(0)
      scrollToChapter(CHAPTERS[prevIdx].id)
    }
  }

  const handleStopTour = () => {
    isTourActiveRef.current = false
    setIsPlaying(false)
    setIsPaused(false)
    if (synthRef.current) {
      synthRef.current.cancel()
    }
    if (timerRef.current) clearTimeout(timerRef.current)
  }

  const activeChapter = CHAPTERS[activeChapterIndex]
  const currentSentence = activeChapter?.sentences[currentSentenceIndex] || activeChapter?.sentences[0]

  return (
    <div className="relative min-h-screen w-full bg-[#09090b] text-[#f4f4f5] pb-32">
      {/* 1. TOP NARRATION CONTROL BAR */}
      <div className="sticky top-0 z-40 w-full border-b border-[#27272a] bg-[#09090b]/95 backdrop-blur-md px-6 py-3">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
          {/* Left: Branding & Status */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm tracking-tight text-[#f4f4f5]">
                AUTO-TOUR &amp; ARCHITECTURE
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-[#18181b] border border-[#27272a] text-[#f59e0b]">
                ZERO-MIC DEMO
              </span>
            </div>

            <div className="hidden sm:flex items-center gap-2 text-xs font-mono text-[#a1a1aa] pl-3 border-l border-[#27272a]">
              <span>Chapter {activeChapterIndex + 1} of 6</span>
              <span>·</span>
              <span className="text-[#10b981]">{activeChapter.timeRange}</span>
            </div>
          </div>

          {/* Center: Playback Controls */}
          <div className="flex items-center gap-2">
            {!isPlaying ? (
              <button
                onClick={() => handleStartTour(0)}
                className="inline-flex items-center gap-2 px-4 py-1.5 rounded-md text-xs font-semibold bg-[#f4f4f5] text-[#09090b] hover:bg-white transition-all shadow-sm"
              >
                <Play size={13} className="fill-current" />
                <span>Start Auto-Narrated Tour (~2m 30s)</span>
              </button>
            ) : (
              <div className="flex items-center gap-1.5 bg-[#121215] border border-[#27272a] rounded-md p-1">
                <button
                  onClick={handlePrevChapter}
                  className="p-1.5 rounded hover:bg-[#27272a] text-[#a1a1aa] hover:text-[#f4f4f5]"
                  title="Previous Chapter"
                >
                  <SkipBack size={13} />
                </button>
                <button
                  onClick={handlePauseResume}
                  className="px-3 py-1 rounded text-xs font-semibold bg-[#27272a] hover:bg-[#3f3f46] text-[#f4f4f5] flex items-center gap-1.5"
                >
                  {isPaused ? <Play size={12} className="fill-current" /> : <Pause size={12} />}
                  <span>{isPaused ? 'Resume' : 'Pause'}</span>
                </button>
                <button
                  onClick={handleNextChapter}
                  className="p-1.5 rounded hover:bg-[#27272a] text-[#a1a1aa] hover:text-[#f4f4f5]"
                  title="Next Chapter"
                >
                  <SkipForward size={13} />
                </button>
                <button
                  onClick={handleStopTour}
                  className="p-1.5 rounded hover:bg-[#27272a] text-[#ef4444]"
                  title="Stop Tour"
                >
                  <RotateCcw size={13} />
                </button>
              </div>
            )}

            {/* Speed Selector */}
            <button
              onClick={() => {
                const nextRate = speechRate === 1.0 ? 1.05 : speechRate === 1.05 ? 1.15 : speechRate === 1.15 ? 1.25 : 1.0
                setSpeechRate(nextRate)
              }}
              className="px-2.5 py-1.5 rounded-md text-xs font-mono font-medium bg-[#121215] border border-[#27272a] text-[#a1a1aa] hover:text-[#f4f4f5]"
              title="Voice playback rate"
            >
              {speechRate}x
            </button>

            {/* Mute toggle for visual subtitles only */}
            <button
              onClick={() => setIsMuted(!isMuted)}
              className="p-2 rounded-md bg-[#121215] border border-[#27272a] text-[#a1a1aa] hover:text-[#f4f4f5]"
              title={isMuted ? 'Unmute Audio Voice' : 'Mute Voice (Subtitles Only)'}
            >
              {isMuted ? <VolumeX size={13} className="text-[#ef4444]" /> : <Volume2 size={13} />}
            </button>
          </div>

          {/* Right: Voice selector & Switch back to Console */}
          <div className="flex items-center gap-3">
            {voices.length > 0 && !isMuted && (
              <select
                value={selectedVoiceIndex}
                onChange={e => setSelectedVoiceIndex(Number(e.target.value))}
                className="max-w-[150px] truncate text-xs bg-[#121215] border border-[#27272a] text-[#a1a1aa] rounded-md px-2 py-1.5 focus:outline-none"
              >
                {voices.map((v, i) => (
                  <option key={i} value={i}>
                    {v.name.replace(/Microsoft|Google|Apple/g, '').trim()} ({v.lang})
                  </option>
                ))}
              </select>
            )}

            <button
              onClick={onSwitchToConsole}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium bg-[#18181b] border border-[#27272a] text-[#a1a1aa] hover:text-[#f4f4f5] hover:border-[#3f3f46] transition-all"
            >
              <span>Live Console</span>
              <ArrowRight size={13} />
            </button>
          </div>
        </div>
      </div>

      {/* 2. MAIN NARRATION CANVAS (6 STRUCTURED CHAPTERS) */}
      <div className="max-w-6xl mx-auto px-6 pt-8 space-y-12">
        {/* CHAPTER 1 */}
        <section
          id="chapter-1"
          className={`transition-all duration-300 rounded-lg p-6 bg-[#121215] border ${
            activeChapterIndex === 0
              ? 'border-[#f59e0b] shadow-[0_0_20px_rgba(245,158,11,0.12)]'
              : 'border-[#27272a]'
          }`}
        >
          <div className="flex items-center justify-between border-b border-[#27272a] pb-3 mb-4">
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-[#18181b] text-[#f59e0b] border border-[#27272a]">
                CHAPTER 1 (0:00 – 0:25)
              </span>
              <h2 className="text-base font-bold text-[#f4f4f5]">
                Architecture &amp; Zero-LLM-Math Invariant
              </h2>
            </div>
            {activeChapterIndex === 0 && isPlaying && (
              <span className="flex items-center gap-1.5 text-xs text-[#10b981] font-mono">
                <span className="h-2 w-2 rounded-full bg-[#10b981] animate-ping" />
                ON AIR
              </span>
            )}
          </div>

          <p className="text-xs text-[#a1a1aa] leading-relaxed mb-5">
            Gemma 4 never computes numbers, sums barrels, or counts calendar days. Fact calculation is strictly owned by SQLite and Python domain services.
          </p>

          {/* Metrics Row */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
            <div className="bg-[#18181b] border border-[#27272a] rounded p-3">
              <div className="text-[10px] font-mono text-[#a1a1aa] uppercase">Multi-Root Ingest</div>
              <div className="text-lg font-bold font-mono text-[#f4f4f5]">2.54s</div>
              <div className="text-[11px] text-[#10b981] font-mono">0 LLM Calls</div>
            </div>
            <div className="bg-[#18181b] border border-[#27272a] rounded p-3">
              <div className="text-[10px] font-mono text-[#a1a1aa] uppercase">Raw Inspections</div>
              <div className="text-lg font-bold font-mono text-[#f4f4f5]">39,567</div>
              <div className="text-[11px] text-[#a1a1aa] font-mono">Immutable SQLite</div>
            </div>
            <div className="bg-[#18181b] border border-[#27272a] rounded p-3">
              <div className="text-[10px] font-mono text-[#a1a1aa] uppercase">Repair Reports</div>
              <div className="text-lg font-bold font-mono text-[#f4f4f5]">1,509 / 1,509</div>
              <div className="text-[11px] text-[#10b981] font-mono">100% Regex Coverage</div>
            </div>
            <div className="bg-[#18181b] border border-[#27272a] rounded p-3">
              <div className="text-[10px] font-mono text-[#a1a1aa] uppercase">Derived Rebuild</div>
              <div className="text-lg font-bold font-mono text-[#f4f4f5]">&lt; 20 ms</div>
              <div className="text-[11px] text-[#a1a1aa] font-mono">eff_inspection / spills</div>
            </div>
          </div>

          {/* ASCII / Monospace Flow Diagram */}
          <div className="bg-[#09090b] border border-[#27272a] rounded p-4 font-mono text-[11px] leading-relaxed text-[#a1a1aa] overflow-x-auto">
            <div className="text-[#f59e0b] font-bold mb-1">DATASET_ROOTS (sample-data, test-data)</div>
            <div>&nbsp;&nbsp;└──▶ [Idempotent Loader: 2.54s] ──▶ RAW SQLITE TABLES (39,567 ins, 5,665 mnt, 90 reg, 140 notes)</div>
            <div>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── rules.yaml (Extracted thresholds with manual section citations)</div>
            <div>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── report_facts (1,509 free-text repair MD reports, 100% deterministic regex coverage)</div>
            <div>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└── docs_fts (SQLite FTS5 BM25 search index across SOPs &amp; engineering manuals)</div>
            <div className="mt-2 text-[#3b82f6] font-bold">APPEND-ONLY LEDGER (corrections, overrides, claims w/ author &amp; timestamp)</div>
            <div>&nbsp;&nbsp;└──▶ MATERIALIZED DERIVED VIEWS (&lt;20ms rebuild: eff_inspection, well_now, spills)</div>
            <div>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└──▶ GEMMA 4 AGENT LOOP ──▶ CITATION GUARDRAIL ──▶ GENERATIVE UI (8 Block Types)</div>
          </div>
        </section>

        {/* CHAPTER 2 */}
        <section
          id="chapter-2"
          className={`transition-all duration-300 rounded-lg p-6 bg-[#121215] border ${
            activeChapterIndex === 1
              ? 'border-[#f59e0b] shadow-[0_0_20px_rgba(245,158,11,0.12)]'
              : 'border-[#27272a]'
          }`}
        >
          <div className="flex items-center justify-between border-b border-[#27272a] pb-3 mb-4">
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-[#18181b] text-[#f59e0b] border border-[#27272a]">
                CHAPTER 2 (0:25 – 0:55)
              </span>
              <h2 className="text-base font-bold text-[#f4f4f5]">
                Truth Hierarchy &amp; Cross-Source Synthesis
              </h2>
            </div>
            {activeChapterIndex === 1 && isPlaying && (
              <span className="flex items-center gap-1.5 text-xs text-[#10b981] font-mono">
                <span className="h-2 w-2 rounded-full bg-[#10b981] animate-ping" />
                ON AIR
              </span>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-[#18181b] border border-[#27272a] rounded p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono font-bold text-[#f59e0b]">Q1: Stale Status Flag</span>
                <span className="text-[10px] font-mono bg-[#27272a] px-1.5 py-0.5 rounded text-[#a1a1aa]">WELL-0001</span>
              </div>
              <p className="text-xs text-[#a1a1aa] leading-relaxed">
                Recorded status claims <span className="text-[#ef4444] font-mono">active</span>, but empirical ΔT is <span className="font-mono text-[#f4f4f5]">3.2°C &lt; 15.0°C</span>. Copilot flags recorded status as stale and surfaces Jake Morales's <span className="font-mono text-[#3b82f6]">[CTX-0001-003]</span> rod string shut-in note.
              </p>
            </div>

            <div className="bg-[#18181b] border border-[#27272a] rounded p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono font-bold text-[#f59e0b]">Q5: Downtime Rule</span>
                <span className="text-[10px] font-mono bg-[#27272a] px-1.5 py-0.5 rounded text-[#a1a1aa]">21 Days</span>
              </div>
              <p className="text-xs text-[#a1a1aa] leading-relaxed">
                Calculated strictly as <b>7 days × 3 non-producing inspections</b> (24 Jul motor trip MNT-0001-021; 16 &amp; 23 Oct stuffing box leak MNT-0001-023), completely ignoring erroneous self-reported maintenance hours.
              </p>
            </div>

            <div className="bg-[#18181b] border border-[#27272a] rounded p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono font-bold text-[#f59e0b]">Q9 &amp; Q10: SR-02 4h Breach</span>
                <span className="text-[10px] font-mono bg-[#27272a] px-1.5 py-0.5 rounded text-[#a1a1aa]">Free-Text Joining</span>
              </div>
              <p className="text-xs text-[#a1a1aa] leading-relaxed">
                SOP SR-02 requires containment within 4 hours. By deterministically parsing free-text repair markdown files, copilot catches <span className="font-mono text-[#f4f4f5]">WELL-0082 (7.1h)</span> and <span className="font-mono text-[#f4f4f5]">WELL-0100 (8.1h)</span> breaches.
              </p>
            </div>
          </div>
        </section>

        {/* CHAPTER 3 */}
        <section
          id="chapter-3"
          className={`transition-all duration-300 rounded-lg p-6 bg-[#121215] border ${
            activeChapterIndex === 2
              ? 'border-[#f59e0b] shadow-[0_0_20px_rgba(245,158,11,0.12)]'
              : 'border-[#27272a]'
          }`}
        >
          <div className="flex items-center justify-between border-b border-[#27272a] pb-3 mb-4">
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-[#18181b] text-[#f59e0b] border border-[#27272a]">
                CHAPTER 3 (0:55 – 1:25)
              </span>
              <h2 className="text-base font-bold text-[#f4f4f5]">
                Two-Level Memory &amp; Scoped Overrides
              </h2>
            </div>
            {activeChapterIndex === 2 && isPlaying && (
              <span className="flex items-center gap-1.5 text-xs text-[#10b981] font-mono">
                <span className="h-2 w-2 rounded-full bg-[#10b981] animate-ping" />
                ON AIR
              </span>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-[#18181b] border border-[#27272a] rounded p-4 space-y-3">
              <div className="text-xs font-mono font-bold text-[#10b981] uppercase">
                Shared Append-Only Ledger (Q12–Q14)
              </div>
              <div className="text-xs text-[#a1a1aa] leading-relaxed">
                <b>• Q12 (WELL-0164 Temp):</b> Michael corrects temp 24.0°C ➔ 41.0°C. Derived table flips producing status and re-evaluating Q2 removes WELL-0164, leaving 3 stopped wells in &lt;20ms.<br/>
                <b>• Q13 (WELL-0151 Volume):</b> Michael corrects spill 4.5 ➔ 5.4 bbl. Crossing 5.0 bbl threshold triggers SR-01 breach and schedules SR-03 cleanup.<br/>
                <b>• Q14 (Scope Containment):</b> Michael overrides T350 pump jack RCA threshold to 2 repairs. Rule applies strictly to <span className="font-mono text-[#f4f4f5]">WELL-0120 (T350)</span>, strictly excluding <span className="font-mono text-[#a1a1aa]">WELL-0102 (T200)</span>.
              </div>
            </div>

            <div className="bg-[#18181b] border border-[#27272a] rounded p-4 space-y-3">
              <div className="text-xs font-mono font-bold text-[#3b82f6] uppercase">
                Private Per-User Isolation (Q11 vs Q16)
              </div>
              <div className="text-xs text-[#a1a1aa] leading-relaxed">
                <b>• Code-Enforced Isolation:</b> Active user identity is injected by the session header, never chosen by the LLM. All private queries enforce <span className="font-mono text-[#f4f4f5]">WHERE user_id = ?</span>.<br/>
                <b>• Q11 (Michael Turner Recall):</b> Michael queries "three wells we discussed yesterday" and copilot recalls NE-07 top wells (WELL-0121, WELL-0138, WELL-0107) and sums 2026 repair costs ($77,912).<br/>
                <b>• Q16 (Jessica Reed Isolation):</b> When Jessica asks the identical question, the engine strictly returns <span className="font-mono text-[#10b981]">"no earlier conversation"</span> with zero data leakage.
              </div>
            </div>
          </div>
        </section>

        {/* CHAPTER 4 */}
        <section
          id="chapter-4"
          className={`transition-all duration-300 rounded-lg p-6 bg-[#121215] border ${
            activeChapterIndex === 3
              ? 'border-[#f59e0b] shadow-[0_0_20px_rgba(245,158,11,0.12)]'
              : 'border-[#27272a]'
          }`}
        >
          <div className="flex items-center justify-between border-b border-[#27272a] pb-3 mb-4">
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-[#18181b] text-[#f59e0b] border border-[#27272a]">
                CHAPTER 4 (1:25 – 1:50)
              </span>
              <h2 className="text-base font-bold text-[#f4f4f5]">
                Conflict Honesty &amp; Disputed Claims
              </h2>
            </div>
            {activeChapterIndex === 3 && isPlaying && (
              <span className="flex items-center gap-1.5 text-xs text-[#10b981] font-mono">
                <span className="h-2 w-2 rounded-full bg-[#10b981] animate-ping" />
                ON AIR
              </span>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-[#18181b] border border-[#27272a] rounded p-4">
              <div className="text-xs font-mono font-bold text-[#ef4444] mb-2 uppercase">
                Q17: Telemetry vs Human Claim
              </div>
              <p className="text-xs text-[#a1a1aa] leading-relaxed mb-3">
                Tyler Hughes states <i>"WELL-0175 is running fine"</i>. The claims verification engine checks the latest inspection: ΔT is 0.4°C (&lt; 15°C threshold) and Michael Turner logged a shut-in.
              </p>
              <div className="bg-[#09090b] border border-[#27272a] rounded p-2.5 font-mono text-[11px] text-[#f4f4f5]">
                <span className="text-[#ef4444] font-bold">STATUS: UNCONFIRMED</span><br/>
                Surface both sides: Tyler's unverified assertion vs. Jessica Reed's empirical drone inspection [INS-0175-0193].
              </div>
            </div>

            <div className="bg-[#18181b] border border-[#27272a] rounded p-4">
              <div className="text-xs font-mono font-bold text-[#f59e0b] mb-2 uppercase">
                Q18: Disputed AI Spill Analysis (WELL-0101)
              </div>
              <p className="text-xs text-[#a1a1aa] leading-relaxed mb-3">
                Operator Ryan Brooks <span className="font-mono text-[#3b82f6]">[CTX-0101-002]</span> claims the 20 Aug spill was produced water, while HSE officer Chris Dalton <span className="font-mono text-[#3b82f6]">[CTX-0101-003]</span> recorded crude oil.
              </p>
              <div className="bg-[#09090b] border border-[#27272a] rounded p-2.5 font-mono text-[11px] text-[#f4f4f5]">
                <span className="text-[#10b981] font-bold">OUTCOME: REAL CRUDE CONFIRMED</span><br/>
                Verified via repair report [MNT-0101-029] flowline patch while transparently citing the water dispute.
              </div>
            </div>
          </div>
        </section>

        {/* CHAPTER 5 */}
        <section
          id="chapter-5"
          className={`transition-all duration-300 rounded-lg p-6 bg-[#121215] border ${
            activeChapterIndex === 4
              ? 'border-[#f59e0b] shadow-[0_0_20px_rgba(245,158,11,0.12)]'
              : 'border-[#27272a]'
          }`}
        >
          <div className="flex items-center justify-between border-b border-[#27272a] pb-3 mb-4">
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-[#18181b] text-[#f59e0b] border border-[#27272a]">
                CHAPTER 5 (1:50 – 2:15)
              </span>
              <h2 className="text-base font-bold text-[#f4f4f5]">
                4-Layer QA Pipeline &amp; Failure Post-Mortem
              </h2>
            </div>
            {activeChapterIndex === 4 && isPlaying && (
              <span className="flex items-center gap-1.5 text-xs text-[#10b981] font-mono">
                <span className="h-2 w-2 rounded-full bg-[#10b981] animate-ping" />
                ON AIR
              </span>
            )}
          </div>

          <div className="mb-4 flex items-center justify-between bg-[#18181b] border border-[#27272a] rounded p-3">
            <div className="flex items-center gap-3">
              <ShieldCheck size={20} className="text-[#10b981]" />
              <div>
                <div className="text-xs font-bold text-[#f4f4f5]">18 / 18 Golden Scenarios Verified Green</div>
                <div className="text-[11px] font-mono text-[#a1a1aa]">Full AgentLoop execution in 2.44s across Part A &amp; Part B</div>
              </div>
            </div>
            <span className="px-2.5 py-1 rounded text-xs font-mono font-bold bg-[#10b981]/10 text-[#10b981] border border-[#10b981]/30">
              100% PASS
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            <div className="bg-[#18181b] border border-[#27272a] rounded p-3">
              <div className="font-bold text-[#ef4444] mb-1">1. Gemma 4 &lt;|tool_call&gt; Token Leakage:</div>
              <p className="text-[#a1a1aa] leading-relaxed">
                Raw special tokens leaked in prose during tool calls. <b>Fixed:</b> AST regex parser in <span className="font-mono text-[#f4f4f5]">llm.py</span> intercepting tokens and forcing structured synthesis.
              </p>
            </div>
            <div className="bg-[#18181b] border border-[#27272a] rounded p-3">
              <div className="font-bold text-[#ef4444] mb-1">2. Keyword Argument Drift:</div>
              <p className="text-[#a1a1aa] leading-relaxed">
                Gemma alternated between <span className="font-mono text-[#f4f4f5]">window</span> and <span className="font-mono text-[#f4f4f5]">from_date/to_date</span>. <b>Fixed:</b> Universal <span className="font-mono text-[#f4f4f5]">**kwargs</span> normalization in <span className="font-mono text-[#f4f4f5]">registry.py</span> and fuzzy date parsing in <span className="font-mono text-[#f4f4f5]">resolver.py</span>.
              </p>
            </div>
            <div className="bg-[#18181b] border border-[#27272a] rounded p-3">
              <div className="font-bold text-[#ef4444] mb-1">3. Duplicate Inline Markdown Tables:</div>
              <p className="text-[#a1a1aa] leading-relaxed">
                Redundant ASCII tables rendered above React visuals. <b>Fixed:</b> Intelligent table stripper in <span className="font-mono text-[#f4f4f5]">guardrails.py</span> that strips raw pipe tables when visual blocks exist.
              </p>
            </div>
            <div className="bg-[#18181b] border border-[#27272a] rounded p-3">
              <div className="font-bold text-[#ef4444] mb-1">4. Cross-Scope Rule Contamination:</div>
              <p className="text-[#a1a1aa] leading-relaxed">
                T350 2-repair override risked leaking to T200 wells. <b>Fixed:</b> Hierarchical scope containment in <span className="font-mono text-[#f4f4f5]">params.py</span> (<span className="font-mono text-[#f4f4f5]">well &gt; well_type &gt; fleet</span>).
              </p>
            </div>
          </div>
        </section>

        {/* CHAPTER 6 */}
        <section
          id="chapter-6"
          className={`transition-all duration-300 rounded-lg p-6 bg-[#121215] border ${
            activeChapterIndex === 5
              ? 'border-[#f59e0b] shadow-[0_0_20px_rgba(245,158,11,0.12)]'
              : 'border-[#27272a]'
          }`}
        >
          <div className="flex items-center justify-between border-b border-[#27272a] pb-3 mb-4">
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-[#18181b] text-[#f59e0b] border border-[#27272a]">
                CHAPTER 6 (2:15 – 2:30)
              </span>
              <h2 className="text-base font-bold text-[#f4f4f5]">
                Live Interactive Copilot Triggers
              </h2>
            </div>
            {activeChapterIndex === 5 && isPlaying && (
              <span className="flex items-center gap-1.5 text-xs text-[#10b981] font-mono">
                <span className="h-2 w-2 rounded-full bg-[#10b981] animate-ping" />
                ON AIR
              </span>
            )}
          </div>

          <p className="text-xs text-[#a1a1aa] leading-relaxed mb-4">
            Test any golden scenario live in the chat workspace. Clicking below instantly switches to the Live Console and submits the grounded question:
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <button
              onClick={() => onJumpToChat("Is WELL-0001 producing oil right now? When was it last inspected, and by whom?", "U-201")}
              className="text-left bg-[#18181b] hover:bg-[#27272a] border border-[#27272a] hover:border-[#3f3f46] rounded p-3 transition-all group"
            >
              <div className="flex items-center justify-between text-xs font-mono font-bold text-[#f59e0b] mb-1">
                <span>Q1: Current Production Status</span>
                <span className="text-[10px] text-[#a1a1aa] group-hover:text-[#f4f4f5] flex items-center gap-1">
                  Launch <ArrowRight size={11} />
                </span>
              </div>
              <p className="text-xs text-[#a1a1aa]">Visual: <span className="font-mono text-[#f4f4f5]">status_card</span> · ΔT=3.2°C &lt; 15°C stale status check</p>
            </button>

            <button
              onClick={() => onJumpToChat("Show a line chart of WELL-0001's wellhead temperature against air temperature for the last 13 weeks, and mark when it was not producing oil.", "U-201")}
              className="text-left bg-[#18181b] hover:bg-[#27272a] border border-[#27272a] hover:border-[#3f3f46] rounded p-3 transition-all group"
            >
              <div className="flex items-center justify-between text-xs font-mono font-bold text-[#f59e0b] mb-1">
                <span>Q3: 13-Week Interactive Temp Trend</span>
                <span className="text-[10px] text-[#a1a1aa] group-hover:text-[#f4f4f5] flex items-center gap-1">
                  Launch <ArrowRight size={11} />
                </span>
              </div>
              <p className="text-xs text-[#a1a1aa]">Visual: <span className="font-mono text-[#f4f4f5]">line_chart</span> · Interactive hover crosshair &amp; live readouts</p>
            </button>

            <button
              onClick={() => onJumpToChat("Which 3 wells in Northeast Block 7 had the most downtime in the last 4 months? Show a bar chart.", "U-201")}
              className="text-left bg-[#18181b] hover:bg-[#27272a] border border-[#27272a] hover:border-[#3f3f46] rounded p-3 transition-all group"
            >
              <div className="flex items-center justify-between text-xs font-mono font-bold text-[#f59e0b] mb-1">
                <span>Q6: Top Downtime Bar Chart</span>
                <span className="text-[10px] text-[#a1a1aa] group-hover:text-[#f4f4f5] flex items-center gap-1">
                  Launch <ArrowRight size={11} />
                </span>
              </div>
              <p className="text-xs text-[#a1a1aa]">Visual: <span className="font-mono text-[#f4f4f5]">bar_chart</span> · WELL-0121 (49d), WELL-0138 (42d), WELL-0107 (42d)</p>
            </button>

            <button
              onClick={() => onJumpToChat("Show a heatmap of 2026 spills by geographic area and month.", "U-201")}
              className="text-left bg-[#18181b] hover:bg-[#27272a] border border-[#27272a] hover:border-[#3f3f46] rounded p-3 transition-all group"
            >
              <div className="flex items-center justify-between text-xs font-mono font-bold text-[#f59e0b] mb-1">
                <span>Q8: Area × Month Spills Heatmap</span>
                <span className="text-[10px] text-[#a1a1aa] group-hover:text-[#f4f4f5] flex items-center gap-1">
                  Launch <ArrowRight size={11} />
                </span>
              </div>
              <p className="text-xs text-[#a1a1aa]">Visual: <span className="font-mono text-[#f4f4f5]">heatmap</span> · 141 confirmed spills across SW-24, NE-07, SW-23, NE-08</p>
            </button>
          </div>
        </section>
      </div>

      {/* 3. SYNCHRONIZED SUBTITLE / TELEPROMPTER BANNER (FIXED AT BOTTOM) */}
      <div className="fixed bottom-0 left-0 right-0 z-50 bg-[#09090b]/95 border-t border-[#27272a] backdrop-blur-md px-6 py-3 shadow-[0_-8px_30px_rgba(0,0,0,0.6)]">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
          {/* Audio Indicator & Chapter Badge */}
          <div className="flex items-center gap-3 shrink-0">
            <div className="flex items-center gap-1 h-4">
              <span className={`w-1 rounded-full bg-[#f59e0b] ${isPlaying && !isPaused ? 'h-4 animate-pulse' : 'h-1.5'}`} />
              <span className={`w-1 rounded-full bg-[#f59e0b] ${isPlaying && !isPaused ? 'h-3 animate-pulse delay-75' : 'h-2'}`} />
              <span className={`w-1 rounded-full bg-[#f59e0b] ${isPlaying && !isPaused ? 'h-4 animate-pulse delay-150' : 'h-1'}`} />
              <span className={`w-1 rounded-full bg-[#f59e0b] ${isPlaying && !isPaused ? 'h-2 animate-pulse delay-100' : 'h-2.5'}`} />
            </div>

            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#18181b] border border-[#27272a] text-[#f59e0b]">
              CH {activeChapterIndex + 1}/6
            </span>

            <span className="text-xs font-semibold text-[#f4f4f5] hidden lg:inline">
              {activeChapter.title}
            </span>
          </div>

          {/* Synchronized Closed Caption Subtitle */}
          <div className="flex-1 px-2 text-center md:text-left">
            <p className="text-sm font-medium text-[#f4f4f5] leading-snug">
              &ldquo;{currentSentence}&rdquo;
            </p>
          </div>

          {/* Quick Jump to Live Console */}
          <div className="shrink-0 flex items-center gap-2">
            <button
              onClick={onSwitchToConsole}
              className="px-3 py-1.5 rounded-md text-xs font-semibold bg-[#27272a] hover:bg-[#3f3f46] text-[#f4f4f5] transition-all flex items-center gap-1.5"
            >
              <span>Switch to Console</span>
              <ArrowRight size={12} />
            </button>
          </div>
        </div>

        {/* Timeline progress line */}
        <div className="w-full bg-[#18181b] h-1 mt-2.5 rounded-full overflow-hidden">
          <div
            className="bg-[#f59e0b] h-full transition-all duration-300"
            style={{
              width: `${((activeChapterIndex * 100 + ((currentSentenceIndex + 1) / activeChapter.sentences.length) * 100) / 6).toFixed(1)}%`
            }}
          />
        </div>
      </div>
    </div>
  )
}
