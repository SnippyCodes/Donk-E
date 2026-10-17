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
  Video,
  Square,
} from 'lucide-react'

export interface BragTourProps {
  onJumpToChat: (prompt: string, userId?: string) => void
  onSwitchToConsole: () => void
  onStartLiveDemo5Min?: () => void
  externalSubtitle?: string
  externalChapterBadge?: string
  isExternalRunning?: boolean
  hideLocalBars?: boolean
}

export interface TourChapter {
  id: number
  title: string
  subtitle: string
  timeRange: string
  timerSeconds: number
  sentences: string[]
  narrationText: string
}

export const TOUR_CHAPTERS: TourChapter[] = [
  {
    id: 1,
    title: 'Architecture & Zero-LLM-Math Invariant',
    subtitle: 'Deterministic Python/SQLite core with 100% regex report facts & FTS5 indexing',
    timeRange: '0:00 – 0:25',
    timerSeconds: 25,
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
    timerSeconds: 55,
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
    timerSeconds: 85,
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
    timerSeconds: 110,
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
    timeRange: '1:50 – 2:00',
    timerSeconds: 120,
    sentences: [
      'Quality assurance is mathematically validated across four pillars: invariant gates, strict citation set membership, generative UI typing, and stateful memory carry-forward.',
      'All eighteen golden scenarios pass sequentially in 2.44 seconds.',
      'During real testing, our QA suite caught four critical failures: Gemma 4 native tool call token leakage, keyword argument drift, duplicate markdown tables, and rate-limit latency.',
      'We resolved each with an AST regex parser, universal parameter normalization, markdown table stripping, and inline visual consolidation.',
      'At this two minute mark, we now transition directly into our live operational console to witness real-time multi-user carry-forward in action!'
    ],
    narrationText:
      'Quality assurance is mathematically validated across four pillars: invariant gates, strict citation set membership, generative UI typing, and stateful memory carry-forward. All eighteen golden scenarios pass sequentially in 2.44 seconds. During real testing, our QA suite caught four critical failures: Gemma 4 native tool call token leakage, keyword argument drift, duplicate markdown tables, and rate-limit latency. We resolved each with an AST regex parser, universal parameter normalization, markdown table stripping, and inline visual consolidation. At this two minute mark, we now transition directly into our live operational console to witness real-time multi-user carry-forward in action!'
  }
]

export const BragTour: React.FC<BragTourProps> = ({
  onJumpToChat,
  onSwitchToConsole,
  onStartLiveDemo5Min,
  externalSubtitle,
  externalChapterBadge,
  hideLocalBars = false
}) => {
  const [isPlaying, setIsPlaying] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [activeChapterIndex, setActiveChapterIndex] = useState(0)
  const [currentSentenceIndex, setCurrentSentenceIndex] = useState(0)
  const [speechRate, setSpeechRate] = useState<number>(1.05)
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([])
  const [selectedVoiceIndex, setSelectedVoiceIndex] = useState<number>(0)
  const [isMuted, setIsMuted] = useState(false)
  const [elapsedSeconds, setElapsedSeconds] = useState(0)

  // Screen recording state
  const [isRecording, setIsRecording] = useState(false)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const recordedChunksRef = useRef<Blob[]>([])

  const isTourActiveRef = useRef(false)
  const synthRef = useRef<SpeechSynthesis | null>(null)
  const timerRef = useRef<any>(null)
  const clockIntervalRef = useRef<any>(null)

  useEffect(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      synthRef.current = window.speechSynthesis
      const loadVoices = () => {
        const available = window.speechSynthesis.getVoices()
        if (available.length > 0) {
          const english = available.filter(v => v.lang.startsWith('en'))
          const list = english.length > 0 ? english : available
          setVoices(list)

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
      if (clockIntervalRef.current) clearInterval(clockIntervalRef.current)
    }
  }, [])

  // Elapsed clock timer for 5-minute counter
  useEffect(() => {
    if (isPlaying && !isPaused) {
      clockIntervalRef.current = setInterval(() => {
        setElapsedSeconds(prev => prev + 1)
      }, 1000)
    } else {
      if (clockIntervalRef.current) clearInterval(clockIntervalRef.current)
    }
    return () => {
      if (clockIntervalRef.current) clearInterval(clockIntervalRef.current)
    }
  }, [isPlaying, isPaused])

  const scrollToChapter = (chapterId: number) => {
    const el = document.getElementById(`chapter-${chapterId}`)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }

  // Voice playback loop
  const speakSentence = (chapterIdx: number, sentenceIdx: number) => {
    if (!isTourActiveRef.current) return

    // Check if we reached the 2:00 mark (end of Chapter 5)
    if (chapterIdx >= TOUR_CHAPTERS.length) {
      // Transition to Live Console Demo!
      handleStopTour()
      if (onStartLiveDemo5Min) {
        onStartLiveDemo5Min()
      } else {
        onSwitchToConsole()
      }
      return
    }

    const chapter = TOUR_CHAPTERS[chapterIdx]
    if (!chapter) {
      handleStopTour()
      return
    }

    if (sentenceIdx === 0) {
      scrollToChapter(chapter.id)
    }

    const sentences = chapter.sentences
    if (sentenceIdx >= sentences.length) {
      // Advance to next chapter
      if (chapterIdx + 1 < TOUR_CHAPTERS.length) {
        setActiveChapterIndex(chapterIdx + 1)
        setCurrentSentenceIndex(0)
        speakSentence(chapterIdx + 1, 0)
      } else {
        // Completed Chapter 5 (2:00) -> Switch to Live Workbench!
        handleStopTour()
        if (onStartLiveDemo5Min) {
          onStartLiveDemo5Min()
        } else {
          onSwitchToConsole()
        }
      }
      return
    }

    setActiveChapterIndex(chapterIdx)
    setCurrentSentenceIndex(sentenceIdx)

    if (isMuted || !synthRef.current) {
      const durationMs = Math.max(2200, (sentences[sentenceIdx].length / 14) * 1000 / speechRate)
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
        timerRef.current = setTimeout(() => {
          speakSentence(chapterIdx, sentenceIdx + 1)
        }, 110)
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
    setElapsedSeconds(startFromChapter === 0 ? 0 : TOUR_CHAPTERS[startFromChapter - 1]?.timerSeconds || 0)
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
    const nextIdx = Math.min(TOUR_CHAPTERS.length - 1, activeChapterIndex + 1)
    if (isPlaying) {
      handleStartTour(nextIdx)
    } else {
      setActiveChapterIndex(nextIdx)
      setCurrentSentenceIndex(0)
      scrollToChapter(TOUR_CHAPTERS[nextIdx].id)
    }
  }

  const handlePrevChapter = () => {
    const prevIdx = Math.max(0, activeChapterIndex - 1)
    if (isPlaying) {
      handleStartTour(prevIdx)
    } else {
      setActiveChapterIndex(prevIdx)
      setCurrentSentenceIndex(0)
      scrollToChapter(TOUR_CHAPTERS[prevIdx].id)
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

  // Native Screen Recording Handler
  const handleToggleRecording = async () => {
    if (isRecording) {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop()
        mediaRecorderRef.current.stream?.getTracks().forEach(t => t.stop())
      }
      setIsRecording(false)
    } else {
      try {
        const stream = await navigator.mediaDevices.getDisplayMedia({
          video: { frameRate: 30 },
          audio: true
        })
        let mixedStream = stream
        try {
          const AudioCtxClass = window.AudioContext || (window as any).webkitAudioContext
          if (AudioCtxClass) {
            const ctx = new AudioCtxClass()
            const dest = ctx.createMediaStreamDestination()
            if (stream.getAudioTracks().length > 0) {
              try {
                ctx.createMediaStreamSource(stream).connect(dest)
              } catch (_) {}
            }
            try {
              const mic = await navigator.mediaDevices.getUserMedia({ audio: true })
              if (mic) {
                ctx.createMediaStreamSource(mic).connect(dest)
              }
            } catch (_) {}
            const audioTracks = dest.stream.getAudioTracks()
            if (audioTracks.length > 0) {
              mixedStream = new MediaStream([...stream.getVideoTracks(), ...audioTracks])
            }
          }
        } catch (e) {
          console.warn('Audio mix error:', e)
        }

        recordedChunksRef.current = []
        const mimeType = MediaRecorder.isTypeSupported('video/webm;codecs=vp9,opus')
          ? 'video/webm;codecs=vp9,opus'
          : MediaRecorder.isTypeSupported('video/webm')
          ? 'video/webm'
          : 'video/mp4'

        const recorder = new MediaRecorder(mixedStream, { mimeType })
        recorder.ondataavailable = e => {
          if (e.data && e.data.size > 0) {
            recordedChunksRef.current.push(e.data)
          }
        }
        recorder.onstop = () => {
          const blob = new Blob(recordedChunksRef.current, { type: 'video/webm' })
          const url = URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = `DonkE_Copilot_Demo_5Min_${Date.now()}.webm`
          a.click()
          URL.revokeObjectURL(url)
          setIsRecording(false)
        }
        stream.getVideoTracks()[0].onended = () => {
          if (recorder.state !== 'inactive') recorder.stop()
        }
        recorder.start(1000)
        mediaRecorderRef.current = recorder
        setIsRecording(true)
      } catch (err: any) {
        console.warn('Screen recording cancelled or failed:', err)
      }
    }
  }

  const activeChapter = TOUR_CHAPTERS[activeChapterIndex]
  const currentSentence =
    externalSubtitle ||
    activeChapter?.sentences[currentSentenceIndex] ||
    activeChapter?.sentences[0] ||
    'Ready to begin auto-narrated walkthrough.'

  const formatTime = (totalSec: number) => {
    const m = Math.floor(totalSec / 60)
    const s = totalSec % 60
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  }

  return (
    <div
      style={{
        position: 'relative',
        minHeight: '100vh',
        width: '100%',
        backgroundColor: '#0d1117',
        color: '#f0f6fc',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
        paddingBottom: '140px'
      }}
    >
      {/* Scoped CSS block for animations & scrollbar */}
      <style>{`
        @keyframes pulse-dot {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.4; transform: scale(0.9); }
        }
        @keyframes eq-bounce {
          0%, 100% { height: 4px; }
          50% { height: 16px; }
        }
        .live-eq-bar {
          display: inline-block;
          width: 3px;
          border-radius: 2px;
          background-color: #f0883e;
          animation: eq-bounce 0.8s ease-in-out infinite;
        }
        .live-eq-bar:nth-child(2) { animation-delay: 0.15s; }
        .live-eq-bar:nth-child(3) { animation-delay: 0.3s; }
        .live-eq-bar:nth-child(4) { animation-delay: 0.45s; }
      `}</style>

      {/* 1. STICKY TOP DIRECTOR CONTROL BAR */}
      {!hideLocalBars && (
        <div
          style={{
          position: 'sticky',
          top: 0,
          zIndex: 50,
          width: '100%',
          backgroundColor: '#161b22',
          borderBottom: '1px solid #30363d',
          padding: '12px 24px',
          boxShadow: '0 2px 10px rgba(0, 0, 0, 0.5)'
        }}
      >
        <div
          style={{
            maxWidth: '1200px',
            margin: '0 auto',
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '12px'
          }}
        >
          {/* Left: Branding & Timer */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '14px', fontWeight: 700, color: '#f0f6fc', letterSpacing: '-0.2px' }}>
                DEMO DIRECTOR
              </span>
              <span
                style={{
                  fontSize: '10px',
                  fontFamily: 'monospace',
                  fontWeight: 700,
                  padding: '2px 6px',
                  borderRadius: '4px',
                  backgroundColor: '#21262d',
                  border: '1px solid #30363d',
                  color: '#f0883e'
                }}
              >
                5-MIN TOUR
              </span>
            </div>

            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '12px',
                fontFamily: 'monospace',
                color: '#8b949e',
                borderLeft: '1px solid #30363d',
                paddingLeft: '12px'
              }}
            >
              <span style={{ color: '#58a6ff' }}>
                {isPlaying ? `Chapter ${activeChapterIndex + 1} of 5` : 'Overview Mode'}
              </span>
              <span>·</span>
              <span style={{ color: '#3fb950', fontWeight: 600 }}>
                {formatTime(elapsedSeconds)} / 05:00
              </span>
            </div>
          </div>

          {/* Center: Playback & Tour Controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {!isPlaying ? (
              <button
                onClick={() => handleStartTour(0)}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 18px',
                  borderRadius: '6px',
                  fontSize: '12.5px',
                  fontWeight: 600,
                  backgroundColor: '#f0883e',
                  color: '#ffffff',
                  border: 'none',
                  cursor: 'pointer',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.4)',
                  transition: 'opacity 0.15s ease'
                }}
              >
                <Play size={14} fill="#ffffff" />
                <span>Start 5-Min Auto-Narrated Demo</span>
              </button>
            ) : (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  backgroundColor: '#090d13',
                  border: '1px solid #30363d',
                  borderRadius: '6px',
                  padding: '4px'
                }}
              >
                <button
                  onClick={handlePrevChapter}
                  style={{
                    padding: '6px 8px',
                    backgroundColor: 'transparent',
                    border: 'none',
                    color: '#8b949e',
                    cursor: 'pointer',
                    borderRadius: '4px'
                  }}
                  title="Previous Chapter"
                >
                  <SkipBack size={13} />
                </button>
                <button
                  onClick={handlePauseResume}
                  style={{
                    padding: '6px 12px',
                    fontSize: '12px',
                    fontWeight: 600,
                    backgroundColor: '#21262d',
                    border: '1px solid #30363d',
                    color: '#f0f6fc',
                    cursor: 'pointer',
                    borderRadius: '4px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px'
                  }}
                >
                  {isPaused ? <Play size={12} fill="#ffffff" /> : <Pause size={12} />}
                  <span>{isPaused ? 'Resume' : 'Pause'}</span>
                </button>
                <button
                  onClick={handleNextChapter}
                  style={{
                    padding: '6px 8px',
                    backgroundColor: 'transparent',
                    border: 'none',
                    color: '#8b949e',
                    cursor: 'pointer',
                    borderRadius: '4px'
                  }}
                  title="Next Chapter"
                >
                  <SkipForward size={13} />
                </button>
                <button
                  onClick={handleStopTour}
                  style={{
                    padding: '6px 8px',
                    backgroundColor: 'transparent',
                    border: 'none',
                    color: '#f85149',
                    cursor: 'pointer',
                    borderRadius: '4px'
                  }}
                  title="Stop Tour"
                >
                  <RotateCcw size={13} />
                </button>
              </div>
            )}

            {/* Speed Toggle */}
            <button
              onClick={() => {
                const nextRate =
                  speechRate === 1.0 ? 1.05 : speechRate === 1.05 ? 1.15 : speechRate === 1.15 ? 1.25 : 1.0
                setSpeechRate(nextRate)
              }}
              style={{
                padding: '7px 12px',
                borderRadius: '6px',
                fontSize: '12px',
                fontFamily: 'monospace',
                fontWeight: 600,
                backgroundColor: '#21262d',
                border: '1px solid #30363d',
                color: '#c9d1d9',
                cursor: 'pointer'
              }}
              title="Voice playback rate"
            >
              {speechRate}x
            </button>

            {/* Mute Toggle */}
            <button
              onClick={() => setIsMuted(!isMuted)}
              style={{
                padding: '7px 10px',
                borderRadius: '6px',
                backgroundColor: '#21262d',
                border: '1px solid #30363d',
                color: isMuted ? '#f85149' : '#8b949e',
                cursor: 'pointer'
              }}
              title={isMuted ? 'Unmute Audio Voice' : 'Mute Voice (Subtitles Only)'}
            >
              {isMuted ? <VolumeX size={14} /> : <Volume2 size={14} />}
            </button>

            {/* Screen Recording Button */}
            <button
              onClick={handleToggleRecording}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '7px 14px',
                borderRadius: '6px',
                fontSize: '12px',
                fontWeight: 600,
                backgroundColor: isRecording ? '#f85149' : '#21262d',
                border: isRecording ? '1px solid #da3633' : '1px solid #30363d',
                color: isRecording ? '#ffffff' : '#f85149',
                cursor: 'pointer'
              }}
              title="Record full demo video + audio to .webm file"
            >
              {isRecording ? <Square size={13} fill="#ffffff" /> : <Video size={13} />}
              <span>{isRecording ? 'Recording (Click to Save)' : 'Record Video (.webm)'}</span>
            </button>
          </div>

          {/* Right: Voice selector & Switch to Console */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {voices.length > 0 && !isMuted && (
              <select
                value={selectedVoiceIndex}
                onChange={e => setSelectedVoiceIndex(Number(e.target.value))}
                style={{
                  maxWidth: '140px',
                  fontSize: '11.5px',
                  backgroundColor: '#21262d',
                  border: '1px solid #30363d',
                  color: '#c9d1d9',
                  borderRadius: '6px',
                  padding: '6px 8px',
                  cursor: 'pointer'
                }}
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
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '7px 14px',
                borderRadius: '6px',
                fontSize: '12px',
                fontWeight: 600,
                backgroundColor: '#238636',
                border: '1px solid #2ea043',
                color: '#ffffff',
                cursor: 'pointer'
              }}
            >
              <span>Live Console</span>
              <ArrowRight size={13} />
            </button>
          </div>
        </div>
      </div>
    )}

      {/* 2. MAIN DOCUMENT CANVAS (0:00–2:00 ARCHITECTURE & RULES) */}
      <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '32px 24px' }}>
        {/* CHAPTER 1 */}
        <section
          id="chapter-1"
          style={{
            backgroundColor: '#161b22',
            border: activeChapterIndex === 0 && isPlaying ? '2px solid #f0883e' : '1px solid #30363d',
            boxShadow:
              activeChapterIndex === 0 && isPlaying
                ? '0 0 0 3px rgba(240, 136, 62, 0.15)'
                : 'none',
            borderRadius: '8px',
            padding: '24px',
            marginBottom: '20px',
            transition: 'border 0.2s ease, box-shadow 0.2s ease'
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '1px solid #30363d',
              paddingBottom: '12px',
              marginBottom: '16px'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span
                style={{
                  fontSize: '11px',
                  fontFamily: 'monospace',
                  fontWeight: 700,
                  backgroundColor: '#21262d',
                  color: '#f0883e',
                  border: '1px solid #30363d',
                  padding: '2px 8px',
                  borderRadius: '4px'
                }}
              >
                CHAPTER 1 (0:00 – 0:25)
              </span>
              <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#f0f6fc', margin: 0 }}>
                Architecture &amp; Zero-LLM-Math Invariant
              </h2>
            </div>
            {activeChapterIndex === 0 && isPlaying && (
              <span
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontSize: '12px',
                  color: '#3fb950',
                  fontFamily: 'monospace',
                  fontWeight: 600
                }}
              >
                <span
                  style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    backgroundColor: '#3fb950',
                    animation: 'pulse-dot 1s infinite'
                  }}
                />
                ON AIR
              </span>
            )}
          </div>

          <p style={{ fontSize: '13px', color: '#8b949e', lineHeight: 1.6, marginBottom: '18px' }}>
            Core engineering philosophy: <b>Deterministic code owns facts and compliance math, Gemma 4 owns conversational synthesis, and an append-only ledger owns memory.</b>
          </p>

          {/* 4-Column KPI Stat Grid */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))',
              gap: '12px',
              margin: '16px 0'
            }}
          >
            <div
              style={{
                backgroundColor: '#0d1117',
                border: '1px solid #30363d',
                borderRadius: '6px',
                padding: '14px'
              }}
            >
              <div
                style={{
                  fontSize: '11px',
                  fontFamily: 'monospace',
                  color: '#8b949e',
                  textTransform: 'uppercase',
                  marginBottom: '4px'
                }}
              >
                Multi-Root Ingest
              </div>
              <div
                style={{
                  fontSize: '22px',
                  fontWeight: 700,
                  fontFamily: 'monospace',
                  color: '#f0f6fc',
                  marginBottom: '2px'
                }}
              >
                2.54s
              </div>
              <div style={{ fontSize: '11px', color: '#3fb950', fontFamily: 'monospace' }}>
                0 LLM Calls
              </div>
            </div>

            <div
              style={{
                backgroundColor: '#0d1117',
                border: '1px solid #30363d',
                borderRadius: '6px',
                padding: '14px'
              }}
            >
              <div
                style={{
                  fontSize: '11px',
                  fontFamily: 'monospace',
                  color: '#8b949e',
                  textTransform: 'uppercase',
                  marginBottom: '4px'
                }}
              >
                Raw Inspections
              </div>
              <div
                style={{
                  fontSize: '22px',
                  fontWeight: 700,
                  fontFamily: 'monospace',
                  color: '#f0f6fc',
                  marginBottom: '2px'
                }}
              >
                39,567
              </div>
              <div style={{ fontSize: '11px', color: '#8b949e', fontFamily: 'monospace' }}>
                Immutable SQLite
              </div>
            </div>

            <div
              style={{
                backgroundColor: '#0d1117',
                border: '1px solid #30363d',
                borderRadius: '6px',
                padding: '14px'
              }}
            >
              <div
                style={{
                  fontSize: '11px',
                  fontFamily: 'monospace',
                  color: '#8b949e',
                  textTransform: 'uppercase',
                  marginBottom: '4px'
                }}
              >
                Repair Reports
              </div>
              <div
                style={{
                  fontSize: '22px',
                  fontWeight: 700,
                  fontFamily: 'monospace',
                  color: '#f0f6fc',
                  marginBottom: '2px'
                }}
              >
                1,509 / 1,509
              </div>
              <div style={{ fontSize: '11px', color: '#3fb950', fontFamily: 'monospace' }}>
                100% Regex Coverage
              </div>
            </div>

            <div
              style={{
                backgroundColor: '#0d1117',
                border: '1px solid #30363d',
                borderRadius: '6px',
                padding: '14px'
              }}
            >
              <div
                style={{
                  fontSize: '11px',
                  fontFamily: 'monospace',
                  color: '#8b949e',
                  textTransform: 'uppercase',
                  marginBottom: '4px'
                }}
              >
                Derived Rebuild
              </div>
              <div
                style={{
                  fontSize: '22px',
                  fontWeight: 700,
                  fontFamily: 'monospace',
                  color: '#f0f6fc',
                  marginBottom: '2px'
                }}
              >
                &lt; 20 ms
              </div>
              <div style={{ fontSize: '11px', color: '#8b949e', fontFamily: 'monospace' }}>
                eff_inspection / spills
              </div>
            </div>
          </div>

          {/* ASCII Architecture Diagram */}
          <pre
            style={{
              backgroundColor: '#090d13',
              border: '1px solid #30363d',
              borderRadius: '6px',
              padding: '14px',
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '12px',
              color: '#79c0ff',
              lineHeight: 1.5,
              overflowX: 'auto',
              margin: '12px 0 0 0'
            }}
          >{`DATASET_ROOTS (sample-data, test-data)
  └──▶ [Idempotent Loader: 2.54s] ──▶ RAW SQLITE (39,567 ins, 5,665 mnt, 90 reg, 140 notes)
        ├── rules.yaml (Extracted thresholds with manual section citations)
        ├── report_facts (1,509 free-text repair MD reports, 100% regex coverage)
        └── docs_fts (SQLite FTS5 BM25 search index across SOPs & manuals)
APPEND-ONLY LEDGER (corrections, overrides, claims w/ author & timestamp)
  └──▶ MATERIALIZED DERIVED VIEWS (<20ms rebuild: eff_inspection, well_now, spills)
        └──▶ GEMMA 4 AGENT LOOP ──▶ CITATION GUARDRAIL ──▶ GENERATIVE UI (8 Visual Types)`}</pre>
        </section>

        {/* CHAPTER 2 */}
        <section
          id="chapter-2"
          style={{
            backgroundColor: '#161b22',
            border: activeChapterIndex === 1 && isPlaying ? '2px solid #f0883e' : '1px solid #30363d',
            boxShadow:
              activeChapterIndex === 1 && isPlaying
                ? '0 0 0 3px rgba(240, 136, 62, 0.15)'
                : 'none',
            borderRadius: '8px',
            padding: '24px',
            marginBottom: '20px',
            transition: 'border 0.2s ease, box-shadow 0.2s ease'
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '1px solid #30363d',
              paddingBottom: '12px',
              marginBottom: '16px'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span
                style={{
                  fontSize: '11px',
                  fontFamily: 'monospace',
                  fontWeight: 700,
                  backgroundColor: '#21262d',
                  color: '#f0883e',
                  border: '1px solid #30363d',
                  padding: '2px 8px',
                  borderRadius: '4px'
                }}
              >
                CHAPTER 2 (0:25 – 0:55)
              </span>
              <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#f0f6fc', margin: 0 }}>
                Truth Hierarchy &amp; Cross-Source Synthesis
              </h2>
            </div>
            {activeChapterIndex === 1 && isPlaying && (
              <span
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontSize: '12px',
                  color: '#3fb950',
                  fontFamily: 'monospace',
                  fontWeight: 600
                }}
              >
                <span
                  style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    backgroundColor: '#3fb950',
                    animation: 'pulse-dot 1s infinite'
                  }}
                />
                ON AIR
              </span>
            )}
          </div>

          {/* 3-Column Sub-Cards */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: '12px'
            }}
          >
            <div
              style={{
                backgroundColor: '#0d1117',
                border: '1px solid #30363d',
                borderRadius: '6px',
                padding: '16px'
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  marginBottom: '10px'
                }}
              >
                <span style={{ fontSize: '13px', fontWeight: 600, color: '#f0f6fc' }}>
                  Q1: Stale Status Flag
                </span>
                <span
                  style={{
                    fontSize: '11px',
                    fontFamily: 'monospace',
                    backgroundColor: '#21262d',
                    border: '1px solid #30363d',
                    color: '#58a6ff',
                    padding: '2px 8px',
                    borderRadius: '4px'
                  }}
                >
                  WELL-0001
                </span>
              </div>
              <p style={{ fontSize: '12.5px', color: '#8b949e', lineHeight: 1.5, margin: 0 }}>
                Recorded status claims <span style={{ color: '#f85149', fontFamily: 'monospace' }}>active</span>, but empirical ΔT is <span style={{ color: '#f0f6fc', fontFamily: 'monospace' }}>3.2°C &lt; 15.0°C</span>. Copilot flags metadata as stale and surfaces Jake Morales's <span style={{ color: '#58a6ff', fontFamily: 'monospace' }}>[CTX-0001-003]</span> rod string shut-in note.
              </p>
            </div>

            <div
              style={{
                backgroundColor: '#0d1117',
                border: '1px solid #30363d',
                borderRadius: '6px',
                padding: '16px'
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  marginBottom: '10px'
                }}
              >
                <span style={{ fontSize: '13px', fontWeight: 600, color: '#f0f6fc' }}>
                  Q5: Downtime Rule
                </span>
                <span
                  style={{
                    fontSize: '11px',
                    fontFamily: 'monospace',
                    backgroundColor: '#21262d',
                    border: '1px solid #30363d',
                    color: '#3fb950',
                    padding: '2px 8px',
                    borderRadius: '4px'
                  }}
                >
                  21 Days
                </span>
              </div>
              <p style={{ fontSize: '12.5px', color: '#8b949e', lineHeight: 1.5, margin: 0 }}>
                Evaluated strictly as <b>7 days × 3 non-producing inspections</b> (24 Jul motor trip MNT-0001-021; 16 &amp; 23 Oct packing leak MNT-0001-023), completely ignoring erroneous self-reported maintenance hours.
              </p>
            </div>

            <div
              style={{
                backgroundColor: '#0d1117',
                border: '1px solid #30363d',
                borderRadius: '6px',
                padding: '16px'
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  marginBottom: '10px'
                }}
              >
                <span style={{ fontSize: '13px', fontWeight: 600, color: '#f0f6fc' }}>
                  Q9 &amp; Q10: SR-02 4h Breach
                </span>
                <span
                  style={{
                    fontSize: '11px',
                    fontFamily: 'monospace',
                    backgroundColor: '#21262d',
                    border: '1px solid #30363d',
                    color: '#f0883e',
                    padding: '2px 8px',
                    borderRadius: '4px'
                  }}
                >
                  Free-Text Joining
                </span>
              </div>
              <p style={{ fontSize: '12.5px', color: '#8b949e', lineHeight: 1.5, margin: 0 }}>
                SOP SR-02 requires spill containment within 4 hours. By deterministically parsing free-text repair markdown files, copilot catches <span style={{ color: '#f0f6fc', fontFamily: 'monospace' }}>WELL-0082 (7.1h)</span> and <span style={{ color: '#f0f6fc', fontFamily: 'monospace' }}>WELL-0100 (8.1h)</span> breaches.
              </p>
            </div>
          </div>
        </section>

        {/* CHAPTER 3 */}
        <section
          id="chapter-3"
          style={{
            backgroundColor: '#161b22',
            border: activeChapterIndex === 2 && isPlaying ? '2px solid #f0883e' : '1px solid #30363d',
            boxShadow:
              activeChapterIndex === 2 && isPlaying
                ? '0 0 0 3px rgba(240, 136, 62, 0.15)'
                : 'none',
            borderRadius: '8px',
            padding: '24px',
            marginBottom: '20px',
            transition: 'border 0.2s ease, box-shadow 0.2s ease'
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '1px solid #30363d',
              paddingBottom: '12px',
              marginBottom: '16px'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span
                style={{
                  fontSize: '11px',
                  fontFamily: 'monospace',
                  fontWeight: 700,
                  backgroundColor: '#21262d',
                  color: '#f0883e',
                  border: '1px solid #30363d',
                  padding: '2px 8px',
                  borderRadius: '4px'
                }}
              >
                CHAPTER 3 (0:55 – 1:25)
              </span>
              <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#f0f6fc', margin: 0 }}>
                Two-Level Memory &amp; Scoped Overrides
              </h2>
            </div>
            {activeChapterIndex === 2 && isPlaying && (
              <span
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontSize: '12px',
                  color: '#3fb950',
                  fontFamily: 'monospace',
                  fontWeight: 600
                }}
              >
                <span
                  style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    backgroundColor: '#3fb950',
                    animation: 'pulse-dot 1s infinite'
                  }}
                />
                ON AIR
              </span>
            )}
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
              gap: '12px'
            }}
          >
            <div
              style={{
                backgroundColor: '#0d1117',
                border: '1px solid #30363d',
                borderRadius: '6px',
                padding: '16px'
              }}
            >
              <div
                style={{
                  fontSize: '12px',
                  fontFamily: 'monospace',
                  fontWeight: 700,
                  color: '#3fb950',
                  marginBottom: '8px'
                }}
              >
                SHARED APPEND-ONLY LEDGER (Q12–Q14)
              </div>
              <div style={{ fontSize: '12.5px', color: '#8b949e', lineHeight: 1.6 }}>
                • <b>Q12 (WELL-0164 Temp):</b> Michael corrects temp 24.0°C ➔ 41.0°C. Derived table flips producing status and re-evaluating Q2 removes WELL-0164 in &lt;20ms.<br />
                • <b>Q13 (WELL-0151 Volume):</b> Michael corrects spill 4.5 ➔ 5.4 bbl. Crossing 5.0 bbl threshold triggers SR-01 breach.<br />
                • <b>Q14 (Scope Containment):</b> Michael overrides T350 pump jack RCA threshold to 2 repairs. Rule applies strictly to <span style={{ color: '#f0f6fc', fontFamily: 'monospace' }}>WELL-0120 (T350)</span>, strictly excluding <span style={{ color: '#8b949e', fontFamily: 'monospace' }}>WELL-0102 (T200)</span>.
              </div>
            </div>

            <div
              style={{
                backgroundColor: '#0d1117',
                border: '1px solid #30363d',
                borderRadius: '6px',
                padding: '16px'
              }}
            >
              <div
                style={{
                  fontSize: '12px',
                  fontFamily: 'monospace',
                  fontWeight: 700,
                  color: '#58a6ff',
                  marginBottom: '8px'
                }}
              >
                PRIVATE PER-USER ISOLATION (Q11 vs Q16)
              </div>
              <div style={{ fontSize: '12.5px', color: '#8b949e', lineHeight: 1.6 }}>
                • <b>Code-Enforced Privacy:</b> User identity is injected by backend session header, never by the LLM. All private queries enforce <span style={{ color: '#f0f6fc', fontFamily: 'monospace' }}>WHERE user_id = ?</span>.<br />
                • <b>Q11 (Michael Turner Recall):</b> Recalls NE-07 top wells (WELL-0121, WELL-0138, WELL-0107) and sums 2026 repair costs ($77,912).<br />
                • <b>Q16 (Jessica Reed Isolation):</b> When Jessica asks identical question, copilot strictly returns <span style={{ color: '#3fb950', fontFamily: 'monospace' }}>"no earlier conversation"</span> with zero cross-user leakage.
              </div>
            </div>
          </div>
        </section>

        {/* CHAPTER 4 */}
        <section
          id="chapter-4"
          style={{
            backgroundColor: '#161b22',
            border: activeChapterIndex === 3 && isPlaying ? '2px solid #f0883e' : '1px solid #30363d',
            boxShadow:
              activeChapterIndex === 3 && isPlaying
                ? '0 0 0 3px rgba(240, 136, 62, 0.15)'
                : 'none',
            borderRadius: '8px',
            padding: '24px',
            marginBottom: '20px',
            transition: 'border 0.2s ease, box-shadow 0.2s ease'
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '1px solid #30363d',
              paddingBottom: '12px',
              marginBottom: '16px'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span
                style={{
                  fontSize: '11px',
                  fontFamily: 'monospace',
                  fontWeight: 700,
                  backgroundColor: '#21262d',
                  color: '#f0883e',
                  border: '1px solid #30363d',
                  padding: '2px 8px',
                  borderRadius: '4px'
                }}
              >
                CHAPTER 4 (1:25 – 1:50)
              </span>
              <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#f0f6fc', margin: 0 }}>
                Conflict Honesty &amp; Disputed Claims
              </h2>
            </div>
            {activeChapterIndex === 3 && isPlaying && (
              <span
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontSize: '12px',
                  color: '#3fb950',
                  fontFamily: 'monospace',
                  fontWeight: 600
                }}
              >
                <span
                  style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    backgroundColor: '#3fb950',
                    animation: 'pulse-dot 1s infinite'
                  }}
                />
                ON AIR
              </span>
            )}
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
              gap: '12px'
            }}
          >
            <div
              style={{
                backgroundColor: '#0d1117',
                border: '1px solid #30363d',
                borderRadius: '6px',
                padding: '16px'
              }}
            >
              <div
                style={{
                  fontSize: '12px',
                  fontFamily: 'monospace',
                  fontWeight: 700,
                  color: '#f85149',
                  marginBottom: '8px'
                }}
              >
                Q17: TELEMETRY VS HUMAN CLAIM
              </div>
              <p style={{ fontSize: '12.5px', color: '#8b949e', lineHeight: 1.5, marginBottom: '10px' }}>
                Tyler Hughes claims <i>"WELL-0175 is running fine"</i>. The claims verification engine checks the latest inspection: ΔT is 0.4°C (&lt; 15°C) and Michael Turner logged a shut-in.
              </p>
              <div
                style={{
                  backgroundColor: '#161b22',
                  border: '1px solid #30363d',
                  borderRadius: '4px',
                  padding: '10px',
                  fontFamily: 'monospace',
                  fontSize: '11px',
                  color: '#f0f6fc'
                }}
              >
                <span style={{ color: '#f85149', fontWeight: 700 }}>STATUS: UNCONFIRMED</span>
                <br />
                Surface both sides: Tyler's assertion vs Jessica Reed's drone inspection [INS-0175-0193].
              </div>
            </div>

            <div
              style={{
                backgroundColor: '#0d1117',
                border: '1px solid #30363d',
                borderRadius: '6px',
                padding: '16px'
              }}
            >
              <div
                style={{
                  fontSize: '12px',
                  fontFamily: 'monospace',
                  fontWeight: 700,
                  color: '#f0883e',
                  marginBottom: '8px'
                }}
              >
                Q18: DISPUTED AI SPILL ANALYSIS (WELL-0101)
              </div>
              <p style={{ fontSize: '12.5px', color: '#8b949e', lineHeight: 1.5, marginBottom: '10px' }}>
                Ryan Brooks <span style={{ color: '#58a6ff', fontFamily: 'monospace' }}>[CTX-0101-002]</span> claims the 20 Aug spill was produced water; HSE officer Chris Dalton <span style={{ color: '#58a6ff', fontFamily: 'monospace' }}>[CTX-0101-003]</span> recorded crude oil.
              </p>
              <div
                style={{
                  backgroundColor: '#161b22',
                  border: '1px solid #30363d',
                  borderRadius: '4px',
                  padding: '10px',
                  fontFamily: 'monospace',
                  fontSize: '11px',
                  color: '#f0f6fc'
                }}
              >
                <span style={{ color: '#3fb950', fontWeight: 700 }}>OUTCOME: REAL CRUDE CONFIRMED</span>
                <br />
                Verified via repair report [MNT-0101-029] flowline patch while transparently citing the water dispute.
              </div>
            </div>
          </div>
        </section>

        {/* CHAPTER 5 */}
        <section
          id="chapter-5"
          style={{
            backgroundColor: '#161b22',
            border: activeChapterIndex === 4 && isPlaying ? '2px solid #f0883e' : '1px solid #30363d',
            boxShadow:
              activeChapterIndex === 4 && isPlaying
                ? '0 0 0 3px rgba(240, 136, 62, 0.15)'
                : 'none',
            borderRadius: '8px',
            padding: '24px',
            marginBottom: '20px',
            transition: 'border 0.2s ease, box-shadow 0.2s ease'
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '1px solid #30363d',
              paddingBottom: '12px',
              marginBottom: '16px'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span
                style={{
                  fontSize: '11px',
                  fontFamily: 'monospace',
                  fontWeight: 700,
                  backgroundColor: '#21262d',
                  color: '#f0883e',
                  border: '1px solid #30363d',
                  padding: '2px 8px',
                  borderRadius: '4px'
                }}
              >
                CHAPTER 5 (1:50 – 2:00)
              </span>
              <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#f0f6fc', margin: 0 }}>
                4-Layer QA Pipeline &amp; Failure Post-Mortem
              </h2>
            </div>
            {activeChapterIndex === 4 && isPlaying && (
              <span
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontSize: '12px',
                  color: '#3fb950',
                  fontFamily: 'monospace',
                  fontWeight: 600
                }}
              >
                <span
                  style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    backgroundColor: '#3fb950',
                    animation: 'pulse-dot 1s infinite'
                  }}
                />
                ON AIR
              </span>
            )}
          </div>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              backgroundColor: '#0d1117',
              border: '1px solid #30363d',
              borderRadius: '6px',
              padding: '14px 18px',
              marginBottom: '16px'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <ShieldCheck size={22} color="#3fb950" />
              <div>
                <div style={{ fontSize: '13.5px', fontWeight: 700, color: '#f0f6fc' }}>
                  18 / 18 Golden Scenarios Verified Green
                </div>
                <div style={{ fontSize: '11.5px', fontFamily: 'monospace', color: '#8b949e' }}>
                  Full AgentLoop sequential pass in 2.44s across Part A &amp; Part B
                </div>
              </div>
            </div>
            <span
              style={{
                padding: '4px 10px',
                borderRadius: '4px',
                fontSize: '11px',
                fontFamily: 'monospace',
                fontWeight: 700,
                backgroundColor: 'rgba(63, 185, 80, 0.15)',
                color: '#3fb950',
                border: '1px solid rgba(63, 185, 80, 0.3)'
              }}
            >
              100% PASS
            </span>
          </div>

          {/* 4 Real Bugs Caught & Fixed */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
              gap: '12px',
              fontSize: '12px'
            }}
          >
            <div
              style={{
                backgroundColor: '#0d1117',
                border: '1px solid #30363d',
                borderRadius: '6px',
                padding: '14px'
              }}
            >
              <div style={{ fontWeight: 700, color: '#f85149', marginBottom: '4px' }}>
                1. &lt;|tool_call&gt; Token Leakage:
              </div>
              <p style={{ color: '#8b949e', lineHeight: 1.5, margin: 0 }}>
                Gemma 4 emitted raw AST tokens in prose. <b>Fixed:</b> AST regex parser in <span style={{ color: '#f0f6fc', fontFamily: 'monospace' }}>llm.py</span> intercepting tokens and forcing structured synthesis.
              </p>
            </div>

            <div
              style={{
                backgroundColor: '#0d1117',
                border: '1px solid #30363d',
                borderRadius: '6px',
                padding: '14px'
              }}
            >
              <div style={{ fontWeight: 700, color: '#f85149', marginBottom: '4px' }}>
                2. Keyword Argument Drift:
              </div>
              <p style={{ color: '#8b949e', lineHeight: 1.5, margin: 0 }}>
                Interchanging <span style={{ color: '#f0f6fc', fontFamily: 'monospace' }}>window</span> with <span style={{ color: '#f0f6fc', fontFamily: 'monospace' }}>from_date/to_date</span>. <b>Fixed:</b> Universal <span style={{ color: '#f0f6fc', fontFamily: 'monospace' }}>**kwargs</span> in <span style={{ color: '#f0f6fc', fontFamily: 'monospace' }}>registry.py</span> and fuzzy date resolver.
              </p>
            </div>

            <div
              style={{
                backgroundColor: '#0d1117',
                border: '1px solid #30363d',
                borderRadius: '6px',
                padding: '14px'
              }}
            >
              <div style={{ fontWeight: 700, color: '#f85149', marginBottom: '4px' }}>
                3. Duplicate Markdown Tables:
              </div>
              <p style={{ color: '#8b949e', lineHeight: 1.5, margin: 0 }}>
                Redundant ASCII tables above React visuals. <b>Fixed:</b> Table stripper in <span style={{ color: '#f0f6fc', fontFamily: 'monospace' }}>guardrails.py</span> that strips raw pipe tables when visual blocks exist.
              </p>
            </div>

            <div
              style={{
                backgroundColor: '#0d1117',
                border: '1px solid #30363d',
                borderRadius: '6px',
                padding: '14px'
              }}
            >
              <div style={{ fontWeight: 700, color: '#f85149', marginBottom: '4px' }}>
                4. Cross-Scope Rule Contamination:
              </div>
              <p style={{ color: '#8b949e', lineHeight: 1.5, margin: 0 }}>
                T350 2-repair override risked leaking to T200 wells. <b>Fixed:</b> Hierarchical scope containment in <span style={{ color: '#f0f6fc', fontFamily: 'monospace' }}>params.py</span> (<span style={{ color: '#f0f6fc', fontFamily: 'monospace' }}>well &gt; well_type &gt; fleet</span>).
              </p>
            </div>
          </div>
        </section>

        {/* 2:00 TRANSITION BANNER */}
        <div
          style={{
            backgroundColor: '#0d1117',
            border: '2px dashed #f0883e',
            borderRadius: '8px',
            padding: '20px',
            textAlign: 'center',
            marginBottom: '24px'
          }}
        >
          <div style={{ fontSize: '14px', fontWeight: 700, color: '#f0883e', marginBottom: '6px' }}>
            AT 2:00: AUTOMATIC TRANSITION TO LIVE OPERATIONAL CONSOLE (2:00–5:00)
          </div>
          <p style={{ fontSize: '13px', color: '#8b949e', maxWidth: '720px', margin: '0 auto 14px auto', lineHeight: 1.5 }}>
            The auto-narrated tour transitions smoothly into the Live Console, demonstrating multi-user carry-forward across Nathan Pierce, Robert Hayes, Laura Simmons, and interactive visuals.
          </p>
          <button
            onClick={() => {
              if (onStartLiveDemo5Min) onStartLiveDemo5Min()
              else onSwitchToConsole()
            }}
            style={{
              padding: '9px 20px',
              backgroundColor: '#f0883e',
              border: 'none',
              borderRadius: '6px',
              color: '#ffffff',
              fontSize: '13px',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            Launch Live Console Walkthrough Now ➔
          </button>
        </div>

        {/* QUICK INTERACTIVE LAUNCH PADS */}
        <div style={{ marginTop: '24px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: 700, color: '#f0f6fc', marginBottom: '12px' }}>
            Direct Visual Block Launchpads:
          </h3>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
              gap: '12px'
            }}
          >
            <button
              onClick={() =>
                onJumpToChat(
                  'Is WELL-0001 producing oil right now? When was it last inspected, and by whom?',
                  'U-201'
                )
              }
              style={{
                textAlign: 'left',
                backgroundColor: '#161b22',
                border: '1px solid #30363d',
                borderRadius: '6px',
                padding: '14px',
                cursor: 'pointer',
                transition: 'border 0.15s ease'
              }}
            >
              <div
                style={{
                  fontSize: '12px',
                  fontFamily: 'monospace',
                  fontWeight: 700,
                  color: '#f0883e',
                  marginBottom: '4px'
                }}
              >
                Q1: StatusCard Visual
              </div>
              <div style={{ fontSize: '12px', color: '#8b949e' }}>
                ΔT=3.2°C &lt; 15°C stale status check
              </div>
            </button>

            <button
              onClick={() =>
                onJumpToChat(
                  "Show a line chart of WELL-0001's wellhead temperature against air temperature for the last 13 weeks, and mark when it was not producing oil.",
                  'U-201'
                )
              }
              style={{
                textAlign: 'left',
                backgroundColor: '#161b22',
                border: '1px solid #30363d',
                borderRadius: '6px',
                padding: '14px',
                cursor: 'pointer',
                transition: 'border 0.15s ease'
              }}
            >
              <div
                style={{
                  fontSize: '12px',
                  fontFamily: 'monospace',
                  fontWeight: 700,
                  color: '#58a6ff',
                  marginBottom: '4px'
                }}
              >
                Q3: LineChart Visual
              </div>
              <div style={{ fontSize: '12px', color: '#8b949e' }}>
                13-week interactive hover guidelines
              </div>
            </button>

            <button
              onClick={() =>
                onJumpToChat(
                  'Which 3 wells in Northeast Block 7 had the most downtime in the last 4 months? Show a bar chart.',
                  'U-201'
                )
              }
              style={{
                textAlign: 'left',
                backgroundColor: '#161b22',
                border: '1px solid #30363d',
                borderRadius: '6px',
                padding: '14px',
                cursor: 'pointer',
                transition: 'border 0.15s ease'
              }}
            >
              <div
                style={{
                  fontSize: '12px',
                  fontFamily: 'monospace',
                  fontWeight: 700,
                  color: '#3fb950',
                  marginBottom: '4px'
                }}
              >
                Q6: BarChart Visual
              </div>
              <div style={{ fontSize: '12px', color: '#8b949e' }}>
                WELL-0121 (49d), WELL-0138 (42d), WELL-0107 (42d)
              </div>
            </button>

            <button
              onClick={() =>
                onJumpToChat('Show a heatmap of 2026 spills by geographic area and month.', 'U-201')
              }
              style={{
                textAlign: 'left',
                backgroundColor: '#161b22',
                border: '1px solid #30363d',
                borderRadius: '6px',
                padding: '14px',
                cursor: 'pointer',
                transition: 'border 0.15s ease'
              }}
            >
              <div
                style={{
                  fontSize: '12px',
                  fontFamily: 'monospace',
                  fontWeight: 700,
                  color: '#f0883e',
                  marginBottom: '4px'
                }}
              >
                Q8: Heatmap Visual
              </div>
              <div style={{ fontSize: '12px', color: '#8b949e' }}>
                141 confirmed spills by area and month
              </div>
            </button>
          </div>
        </div>
      </div>

      {/* 3. FIXED BOTTOM TELEPROMPTER / SUBTITLE BANNER */}
      {!hideLocalBars && (
        <div
          style={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          zIndex: 9999,
          backgroundColor: 'rgba(13, 17, 23, 0.96)',
          backdropFilter: 'blur(10px)',
          borderTop: '2px solid #f0883e',
          padding: '14px 28px',
          boxShadow: '0 -4px 20px rgba(0, 0, 0, 0.7)'
        }}
      >
        <div
          style={{
            maxWidth: '1200px',
            margin: '0 auto',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '16px'
          }}
        >
          {/* Audio Equalizer & Badge */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexShrink: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '2px', height: '16px' }}>
              <span className="live-eq-bar" />
              <span className="live-eq-bar" />
              <span className="live-eq-bar" />
              <span className="live-eq-bar" />
            </div>

            <span
              style={{
                fontSize: '11px',
                fontFamily: 'monospace',
                fontWeight: 700,
                backgroundColor: '#21262d',
                border: '1px solid #30363d',
                color: '#f0883e',
                padding: '2px 8px',
                borderRadius: '4px'
              }}
            >
              {externalChapterBadge || `CH ${activeChapterIndex + 1}/5`}
            </span>

            <span
              style={{
                fontSize: '12px',
                fontFamily: 'monospace',
                color: '#8b949e'
              }}
            >
              [{formatTime(elapsedSeconds)} / 05:00]
            </span>
          </div>

          {/* Real-time Subtitle Text */}
          <div style={{ flex: 1, textAlign: 'center', padding: '0 12px' }}>
            <p
              style={{
                fontSize: '15.5px',
                fontWeight: 500,
                color: '#ffffff',
                lineHeight: 1.4,
                margin: 0
              }}
            >
              &ldquo;{currentSentence}&rdquo;
            </p>
          </div>

          {/* Quick Jump to Console */}
          <div style={{ flexShrink: 0 }}>
            <button
              onClick={onSwitchToConsole}
              style={{
                padding: '6px 14px',
                borderRadius: '6px',
                fontSize: '12px',
                fontWeight: 600,
                backgroundColor: '#21262d',
                border: '1px solid #30363d',
                color: '#f0f6fc',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <span>Console</span>
              <ArrowRight size={12} />
            </button>
          </div>
        </div>

        {/* Timeline progress line */}
        <div
          style={{
            width: '100%',
            backgroundColor: '#21262d',
            height: '3px',
            marginTop: '10px',
            borderRadius: '2px',
            overflow: 'hidden'
          }}
        >
          <div
            style={{
              backgroundColor: '#f0883e',
              height: '100%',
              width: `${Math.min(100, (elapsedSeconds / 300) * 100).toFixed(1)}%`,
              transition: 'width 0.3s ease'
            }}
          />
        </div>
      </div>
    )}
  </div>
)
}
