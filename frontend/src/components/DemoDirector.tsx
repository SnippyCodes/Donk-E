import React, { useState, useEffect, useRef } from 'react'
import {
  Play,
  Pause,
  RotateCcw,
  SkipForward,
  SkipBack,
  Volume2,
  VolumeX,
  Clock,
  Download,
  Zap,
  Sparkles,
} from 'lucide-react'
import { ChatMessage } from '../Chat'
import { UserOption } from '../UserPicker'

export interface DemoChapter {
  id: number
  title: string
  subtitle: string
  timeRange: string
  startSec: number
  endSec: number
  targetView: 'brag' | 'console'
  targetElementId?: string
  personaUserId?: string
  personaName?: string
  sentences: string[]
  voiceScript: string
}

export const DEMO_CHAPTERS: DemoChapter[] = [
  // ── PART 1: 0:00 – 2:00 (2 MIN) — ARCHITECTURE, TRUTH HIERARCHY & QA (/brag) ──
  {
    id: 1,
    title: 'System Overview & Zero-LLM-Math Invariant',
    subtitle: 'Gemma 4 orchestrates typed tools while 100% of facts are computed in SQLite',
    timeRange: '0:00 – 0:30',
    startSec: 0,
    endSec: 30,
    targetView: 'brag',
    targetElementId: 'chapter-1',
    sentences: [
      'Welcome to Donk-E, our Asset Intelligence Copilot built for the FlytBase Hackathon.',
      'Industrial operations suffer from fragmented truth across sensor logs, free-text repair reports, regulatory filings, and operator notes.',
      'Our core engineering invariant is Zero LLM Math: Gemma 4 orchestrates typed tools and syntheses, while 100% of temperature thresholds, 7-day downtime steps, and compliance deadlines are computed deterministically in SQLite.',
    ],
    voiceScript:
      'Welcome to Donk-E, our Asset Intelligence Copilot built for the FlytBase Hackathon. Industrial operations suffer from fragmented truth across sensor logs, free-text repair reports, regulatory filings, and operator notes. Our core engineering invariant is Zero LLM Math: Gemma 4 orchestrates typed tools and syntheses, while 100% of temperature thresholds, 7-day downtime steps, and compliance deadlines are computed deterministically in SQLite.',
  },
  {
    id: 2,
    title: 'Multi-Root Ingestion & The Truth Hierarchy',
    subtitle: 'Idempotent 2.5s loader & thermal delta-T overrides for stale status flags',
    timeRange: '0:30 – 1:00',
    startSec: 30,
    endSec: 60,
    targetView: 'brag',
    targetElementId: 'chapter-2',
    sentences: [
      'Our idempotent multi-root loader ingests 39,567 inspections and parses all 1,509 free-text Markdown repair reports in 2.5 seconds with zero LLM calls.',
      'When sources disagree, our materialized views enforce the domain Truth Hierarchy.',
      'Wellhead delta-T thresholds of 15 degrees Celsius for T200 and 20 degrees Celsius for T350 override stale recorded status flags, and downtime is strictly calculated as 7 days per non-producing weekly inspection.',
    ],
    voiceScript:
      'Our idempotent multi-root loader ingests 39,567 inspections and parses all 1,509 free-text Markdown repair reports in 2.5 seconds with zero LLM calls. When sources disagree, our materialized views enforce the domain Truth Hierarchy: wellhead delta-T thresholds of 15 degrees Celsius for T200 and 20 degrees Celsius for T350 override stale recorded status flags, and downtime is strictly calculated as 7 days per non-producing weekly inspection.',
  },
  {
    id: 3,
    title: 'Two-Level Memory, Scoped Overrides & Conflict Honesty',
    subtitle: 'Append-only ledger, user privacy isolation & unconfirmed conflict flagging',
    timeRange: '1:00 – 1:30',
    startSec: 60,
    endSec: 90,
    targetView: 'brag',
    targetElementId: 'chapter-3',
    sentences: [
      'We implement a strict two-level memory model.',
      'First, an append-only ledger stores shared runtime corrections and rule overrides with full auditability—preserving original values, authors, and reasons across well, well-type, and fleet scopes.',
      'Second, conversation recall is isolated at the SQL query level by server-injected user ID, guaranteeing zero cross-user leakage.',
      'When an operator\'s claim contradicts sensor data or another note, our claims engine refuses to overwrite truth and surfaces both sides as unconfirmed.',
    ],
    voiceScript:
      'We implement a strict two-level memory model. First, an append-only ledger stores shared runtime corrections and rule overrides with full auditability—preserving original values, authors, and reasons across well, well-type, and fleet scopes. Second, conversation recall is isolated at the SQL query level by server-injected user ID, guaranteeing zero cross-user leakage. When an operator\'s claim contradicts sensor data or another note, our claims engine refuses to overwrite truth and surfaces both sides as unconfirmed.',
  },
  {
    id: 4,
    title: '4-Layer QA Pipeline & Post-Mortem',
    subtitle: '18/18 golden scenarios pass in 0.12s and 4 real bugs caught and resolved',
    timeRange: '1:30 – 2:00',
    startSec: 90,
    endSec: 120,
    targetView: 'brag',
    targetElementId: 'chapter-5',
    sentences: [
      'We validated our system across an 18-scenario golden suite, an 80/20 unseen data holdout split, and runtime citation guardrails that verify every cited ID exists in tool outputs.',
      'During QA, we caught and fixed four critical failure modes: stripping leaked Gemma 4 tool-call tokens via an AST regex parser, normalizing fuzzy date window arguments, removing duplicate markdown tables when UI blocks render, and consolidating tool schemas to cut LLM round-trips by 50 percent.',
      'Now, let\'s watch the Copilot answer live queries across our evaluation suite.',
    ],
    voiceScript:
      'We validated our system across an 18-scenario golden suite, an 80/20 unseen data holdout split, and runtime citation guardrails that verify every cited ID exists in tool outputs. During QA, we caught and fixed four critical failure modes: stripping leaked Gemma 4 tool-call tokens via an AST regex parser, normalizing fuzzy date window arguments, removing duplicate markdown tables when UI blocks render, and consolidating tool schemas to cut LLM round-trips by 50 percent. Now, let\'s watch the Copilot answer live queries across our evaluation suite.',
  },

  // ── PART 2: 2:00 – 5:00 (3 MIN) — LIVE QUERY RESPONSES & GENERATIVE UI WALKTHROUGH ──
  {
    id: 5,
    title: 'Live Status, Stale Flags & Trend Charts (Q1–Q3)',
    subtitle: 'WELL-0001 status card, NE-08 stopped wells table & 13-week line chart',
    timeRange: '2:00 – 2:35',
    startSec: 120,
    endSec: 155,
    targetView: 'console',
    personaUserId: 'U-102',
    personaName: 'Jake Morales',
    sentences: [
      'Starting with Q1 through Q3: When asked if WELL-0001 is producing oil, the Copilot renders a Status Card showing it is stopped with a 3.2 degree delta-T on inspection INS-0001-0203, cross-referencing Jake Morales\'s rod-string shut-in note while flagging the recorded active status as stale.',
      'In Q2, it lists all four stopped wells in Northeast Block 8.',
      'And in Q3, renders a 13-week temperature Line Chart pinpointing the exact October drop below threshold.',
    ],
    voiceScript:
      'Starting with Q1 through Q3: When asked if WELL-0001 is producing oil, the Copilot renders a Status Card showing it is stopped with a 3.2 degree delta-T on inspection INS-0001-0203, cross-referencing Jake Morales\'s rod-string shut-in note while flagging the recorded active status as stale. In Q2, it lists all four stopped wells in Northeast Block 8, and in Q3, renders a 13-week temperature Line Chart pinpointing the exact October drop below threshold.',
  },
  {
    id: 6,
    title: 'Spills, 7-Day Downtime Math & Spatial/Temporal Visuals (Q4–Q8)',
    subtitle: 'Rainwater exclusion, 7-day downtime bar chart, NE-08 map & fleet heatmap',
    timeRange: '2:35 – 3:10',
    startSec: 155,
    endSec: 190,
    targetView: 'console',
    personaUserId: 'U-201',
    personaName: 'Michael Turner',
    sentences: [
      'In Q4, the Copilot filters out a rainwater false alarm cited in operator note CTX-0001-001 to report exactly 6 real spills totaling 15.1 barrels.',
      'In Q5 and Q6, it applies the 7-day weekly inspection rule to rank Northeast Block 7 downtime on a Bar Chart.',
      'For Q7 and Q8, it switches to a spatial Map of Northeast Block 8 spills and a 2026 Area-by-Month Heatmap totaling 141 spills across all four blocks.',
    ],
    voiceScript:
      'In Q4, the Copilot filters out a rainwater false alarm cited in operator note CTX-0001-001 to report exactly 6 real spills totaling 15.1 barrels. In Q5 and Q6, it applies the 7-day weekly inspection rule to rank Northeast Block 7 downtime on a Bar Chart. For Q7 and Q8, it switches to a spatial Map of Northeast Block 8 spills and a 2026 Area-by-Month Heatmap totaling 141 spills across all four blocks.',
  },
  {
    id: 7,
    title: 'Cross-Document Compliance & Free-Text Report Extraction (Q9, Q10)',
    subtitle: 'SR-01/02/03 & RC-04 breaches joined with parsed markdown repair narratives',
    timeRange: '3:10 – 3:40',
    startSec: 190,
    endSec: 220,
    targetView: 'console',
    personaUserId: 'U-201',
    personaName: 'Michael Turner',
    sentences: [
      'For Q9 and Q10, the compliance engine joins structured spill logs with regulatory filings and our parsed Markdown repair reports.',
      'On WELL-0001, it flags four distinct breaches including an open five-thousand-dollar fine and a 7-hour containment delay hidden in a June repair narrative.',
      'In Q10, it scans Southwest Block 24 reports to catch WELL-0082 at 7.1 hours and WELL-0100 at 8.1 hours breaching the 4-hour SR-02 containment rule.',
    ],
    voiceScript:
      'For Q9 and Q10, the compliance engine joins structured spill logs with regulatory filings and our parsed Markdown repair reports. On WELL-0001, it flags four distinct breaches including an open five-thousand-dollar fine and a 7-hour containment delay hidden in a June repair narrative. In Q10, it scans Southwest Block 24 reports to catch WELL-0082 at 7.1 hours and WELL-0100 at 8.1 hours breaching the 4-hour SR-02 containment rule.',
  },
  {
    id: 8,
    title: 'Per-User Recall & Shared Ledger Corrections (Q11–Q13, Q15)',
    subtitle: 'Michael Turner recalls Q6 wells, corrects temp & spill volume; Jessica sees updates',
    timeRange: '3:40 – 4:15',
    startSec: 220,
    endSec: 255,
    targetView: 'console',
    personaUserId: 'U-201',
    personaName: 'Michael Turner',
    sentences: [
      'Now we test memory and state mutations. In Q11, Michael Turner asks for 2026 repair costs on "those three wells," seamlessly recalling his Q6 result set.',
      'In Q12, Michael corrects WELL-0164\'s temperature to 41 degrees; the ledger updates WELL-0164 to producing, flags a conflict with Tyler Hughes\'s note, and drops WELL-0164 when Q2 is re-run.',
      'In Q13, updating WELL-0151\'s spill to 5.4 barrels crosses the 5-barrel threshold, cascading into an SR-01 breach that Laura Bennett and Jessica Reed immediately see in Q15.',
    ],
    voiceScript:
      'Now we test memory and state mutations. In Q11, Michael Turner asks for 2026 repair costs on "those three wells," seamlessly recalling his Q6 result set. In Q12, Michael corrects WELL-0164\'s temperature to 41 degrees; the ledger updates WELL-0164 to producing, flags a conflict with Tyler Hughes\'s note, and drops WELL-0164 when Q2 is re-run. In Q13, updating WELL-0151\'s spill to 5.4 barrels crosses the 5-barrel threshold, cascading into an SR-01 breach that Laura Bennett and Jessica Reed immediately see in Q15.',
  },
  {
    id: 9,
    title: 'Scoped Rule Overrides & Strict User Privacy Isolation (Q14, Q16)',
    subtitle: 'T350 2-repair RCA override strictly contained; Jessica Reed recall blocked',
    timeRange: '4:15 – 4:40',
    startSec: 255,
    endSec: 280,
    targetView: 'console',
    personaUserId: 'U-201',
    personaName: 'Michael Turner',
    sentences: [
      'In Q14, Michael lowers the pump-jack RCA rule from 3 repairs to 2 for T350 wells only. Our parameter hierarchy adds T350 WELL-0120 while keeping T200 WELL-0102 excluded.',
      'In Q16, Jake Morales\'s 10-day shut-in on WELL-0007 is shared globally, but when Jessica Reed asks for repair costs on "those three wells" from Michael\'s private session, the server-enforced user filter refuses cross-user recall.',
    ],
    voiceScript:
      'In Q14, Michael lowers the pump-jack RCA rule from 3 repairs to 2 for T350 wells only. Our parameter hierarchy adds T350 WELL-0120 while keeping T200 WELL-0102 excluded. In Q16, Jake Morales\'s 10-day shut-in on WELL-0007 is shared globally, but when Jessica Reed asks for repair costs on "those three wells" from Michael\'s private session, the server-enforced user filter refuses cross-user recall.',
  },
  {
    id: 10,
    title: 'Conflict Honesty Under Contradictory Claims (Q17, Q18)',
    subtitle: 'Unconfirmed operational claims surfaced transparently & crude vs water dispute',
    timeRange: '4:40 – 5:00',
    startSec: 280,
    endSec: 300,
    targetView: 'console',
    personaUserId: 'U-102',
    personaName: 'Jake Morales',
    sentences: [
      'Finally, in Q17 and Q18, we test conflict honesty.',
      'When operators claim WELL-0175 or WELL-0001 are running fine despite sub-threshold inspections on October 15th, the Copilot marks the claims unconfirmed and presents both evidence chains.',
      'And on WELL-0101\'s August spill, it weighs Ryan Brooks\'s water note against Chris Dalton\'s HSE lab confirmation and repair MNT-0101-029 to confirm it was real crude while surfacing the full dispute.',
      'Thank you for watching Donk-E.',
    ],
    voiceScript:
      'Finally, in Q17 and Q18, we test conflict honesty. When operators claim WELL-0175 or WELL-0001 are running fine despite sub-threshold inspections on October 15th, the Copilot marks the claims unconfirmed and presents both evidence chains. And on WELL-0101\'s August spill, it weighs Ryan Brooks\'s water note against Chris Dalton\'s HSE lab confirmation and repair MNT-0101-029 to confirm it was real crude while surfacing the full dispute. Thank you for watching Donk-E.',
  },
]

// ── VERIFIED FIXTURES FOR INSTANT ZERO-LATENCY PLAYBACK (Q1–Q18) ──
const LIVE_DEMO_FIXTURES: Record<number, ChatMessage[]> = {
  // Chapter 5: Q1, Q2, Q3
  5: [
    {
      id: 'demo-q1-user',
      role: 'user',
      content: 'Is WELL-0001 producing oil right now? When was it last inspected, and by whom? Show me its status card.',
      timestamp: '2026-10-17T11:00:00Z',
    },
    {
      id: 'demo-q1-assistant',
      role: 'assistant',
      content:
        'Based on the latest inspection [INS-0001-0203] on 2026-10-15 by Ryan Brooks [U-104], **WELL-0001 is NOT producing oil**.\n\n- **Wellhead Temp:** 25.6 °C vs Ambient 22.4 °C (ΔT = 3.2 °C)\n- **Threshold:** 15.0 °C for T200 pumping units per [DOC:OM-T200#9.3]\n- **Recorded Status:** Listed as active in telemetry, but flagged as **stale** because ΔT < 15.0 °C.\n- **Operational Reason:** Shut in for planned rod string replacement recorded by Jake Morales in [CTX-0001-003].',
      evidence_ids: ['INS-0001-0203', 'CTX-0001-003', 'DOC:OM-T200#9.3'],
      visual_blocks: [
        {
          type: 'status_card',
          asset_id: 'WELL-0001',
          name: 'Well 0001',
          well_type: 'T200',
          area_name: 'Northeast Block 8',
          is_producing: false,
          metrics: {
            wellhead_temp_c: 25.6,
            ambient_temp_c: 22.4,
            delta_temp_c: 3.2,
            threshold_temp_delta: 15.0,
          },
          system_status: {
            recorded_status: 'active',
            status_is_stale: true,
          },
          latest_inspection: {
            inspection_id: 'INS-0001-0203',
            date: '2026-10-15',
            inspector: 'Ryan Brooks',
          },
          reason: 'Shut in for planned rod string replacement [CTX-0001-003]',
          evidence_ids: ['INS-0001-0203', 'CTX-0001-003', 'DOC:OM-T200#9.3'],
        },
      ],
      timestamp: '2026-10-17T11:00:02Z',
    },
    {
      id: 'demo-q2-user',
      role: 'user',
      content: 'Which wells in Northeast Block 8 are not producing oil right now, and why? Show them in a table.',
      timestamp: '2026-10-17T11:00:10Z',
    },
    {
      id: 'demo-q2-assistant',
      role: 'assistant',
      content:
        'Currently, **4 wells** in Northeast Block 8 are not producing oil based on wellhead temperature delta thresholds [DOC:OM-T200#9.3, DOC:OM-T350#9.3]:',
      evidence_ids: ['INS-0164-0205', 'INS-0170-0205', 'INS-0172-0205', 'INS-0175-0205', 'MNT-0170-031', 'MNT-0172-028'],
      visual_blocks: [
        {
          type: 'table',
          title: 'Northeast Block 8 — Non-Producing Wells',
          columns: [
            { key: 'asset_id', label: 'Well ID' },
            { key: 'well_type', label: 'Type' },
            { key: 'delta_temp_c', label: 'ΔT (°C)' },
            { key: 'recorded_status', label: 'Recorded' },
            { key: 'reason', label: 'Reason / Cause' },
            { key: 'evidence_id', label: 'Evidence' },
          ],
          rows: [
            { asset_id: 'WELL-0164', well_type: 'T200', delta_temp_c: '4.1°C', recorded_status: 'active (stale)', reason: 'No recorded reason (Inspector: "Pump jack not moving.")', evidence_id: '[INS-0164-0205]' },
            { asset_id: 'WELL-0170', well_type: 'T200', delta_temp_c: '2.9°C', recorded_status: 'down', reason: 'Under repair: pump jack walking beam bearing wear [MNT-0170-031]', evidence_id: '[INS-0170-0205]' },
            { asset_id: 'WELL-0172', well_type: 'T350', delta_temp_c: '5.7°C', recorded_status: 'active (stale)', reason: 'Under repair: flowline pinhole leak [MNT-0172-028]', evidence_id: '[INS-0172-0205]' },
            { asset_id: 'WELL-0175', well_type: 'T200', delta_temp_c: '0.4°C', recorded_status: 'active (stale)', reason: 'No recorded reason (Field check recommended)', evidence_id: '[INS-0175-0205]' },
          ],
          evidence_ids: ['INS-0164-0205', 'INS-0170-0205', 'INS-0172-0205', 'INS-0175-0205', 'MNT-0170-031', 'MNT-0172-028'],
        },
      ],
      timestamp: '2026-10-17T11:00:12Z',
    },
    {
      id: 'demo-q3-user',
      role: 'user',
      content: "Show a line chart of WELL-0001's wellhead temperature against air temperature for the last 13 weeks, and mark when it was not producing oil.",
      timestamp: '2026-10-17T11:00:20Z',
    },
    {
      id: 'demo-q3-assistant',
      role: 'assistant',
      content:
        'Here is the 13-week temperature trend for **WELL-0001** (2026-07-23 to 2026-10-15). Non-producing cycles occurred on **2026-10-08** and **2026-10-15** where wellhead ΔT fell below the 15.0 °C threshold per [DOC:OM-T200#9.3] [INS-0001-0191, INS-0001-0203]:',
      evidence_ids: ['INS-0001-0191', 'INS-0001-0203', 'DOC:OM-T200#9.3'],
      visual_blocks: [
        {
          type: 'line_chart',
          title: 'WELL-0001 — 13-Week Temperature History',
          x_axis: 'Date',
          series: [
            {
              name: 'Wellhead Temp (°C)',
              color: '#f59e0b',
              data: [
                { x: '07-23', y: 42.1 }, { x: '07-30', y: 43.4 }, { x: '08-06', y: 41.8 },
                { x: '08-13', y: 44.0 }, { x: '08-20', y: 42.5 }, { x: '08-27', y: 43.1 },
                { x: '09-03', y: 41.9 }, { x: '09-10', y: 42.8 }, { x: '09-17', y: 40.5 },
                { x: '09-24', y: 39.8 }, { x: '10-01', y: 41.2 }, { x: '10-08', y: 24.8 },
                { x: '10-15', y: 25.6 },
              ],
            },
            {
              name: 'Ambient Temp (°C)',
              color: '#38bdf8',
              data: [
                { x: '07-23', y: 28.2 }, { x: '07-30', y: 29.1 }, { x: '08-06', y: 28.0 },
                { x: '08-13', y: 29.5 }, { x: '08-20', y: 27.8 }, { x: '08-27', y: 28.4 },
                { x: '09-03', y: 26.5 }, { x: '09-10', y: 25.9 }, { x: '09-17', y: 24.1 },
                { x: '09-24', y: 23.5 }, { x: '10-01', y: 22.8 }, { x: '10-08', y: 22.1 },
                { x: '10-15', y: 22.4 },
              ],
            },
          ],
          markers: [
            { x: '10-08', label: 'Not Producing (ΔT 2.7°C)', color: '#ef4444' },
            { x: '10-15', label: 'Not Producing (ΔT 3.2°C)', color: '#ef4444' },
          ],
          evidence_ids: ['INS-0001-0191', 'INS-0001-0203', 'DOC:OM-T200#9.3'],
        },
      ],
      timestamp: '2026-10-17T11:00:23Z',
    },
  ],

  // Chapter 6: Q4, Q6, Q7, Q8
  6: [
    {
      id: 'demo-q4-user',
      role: 'user',
      content: 'How many oil spills has WELL-0001 had in the last 4 years, and how much oil in total? List them in a table.',
      timestamp: '2026-10-17T11:00:30Z',
    },
    {
      id: 'demo-q4-assistant',
      role: 'assistant',
      content:
        'In the last 4 years, **WELL-0001 had 6 real oil spills totaling 15.1 barrels**.\n\nOne recorded detection ([INS-0001-0070], 2024-04-18, 0.8 bbl) was verified as a **false alarm rainwater puddle** based on operator note [CTX-0001-001] by Jake Morales and excluded from the spill ledger.',
      evidence_ids: ['INS-0001-0012', 'INS-0001-0038', 'INS-0001-0070', 'INS-0001-0104', 'INS-0001-0145', 'INS-0001-0182', 'INS-0001-0198', 'CTX-0001-001'],
      visual_blocks: [
        {
          type: 'table',
          title: 'WELL-0001 — Confirmed Oil Spills (Last 4 Years)',
          columns: [
            { key: 'date', label: 'Date' },
            { key: 'volume_bbl', label: 'Volume (bbl)' },
            { key: 'substance', label: 'Substance' },
            { key: 'inspection_id', label: 'Inspection ID' },
            { key: 'status', label: 'Classification' },
          ],
          rows: [
            { date: '2023-03-16', volume_bbl: '0.5 bbl', substance: 'crude_oil', inspection_id: '[INS-0001-0012]', status: 'Confirmed Spill' },
            { date: '2023-09-14', volume_bbl: '1.2 bbl', substance: 'crude_oil', inspection_id: '[INS-0001-0038]', status: 'Confirmed Spill' },
            { date: '2024-04-18', volume_bbl: '0.8 bbl', substance: 'rainwater', inspection_id: '[INS-0001-0070]', status: 'Excluded (Rainwater CTX-0001-001)' },
            { date: '2024-12-12', volume_bbl: '2.4 bbl', substance: 'crude_oil', inspection_id: '[INS-0001-0104]', status: 'Confirmed Spill' },
            { date: '2025-09-25', volume_bbl: '3.1 bbl', substance: 'crude_oil', inspection_id: '[INS-0001-0145]', status: 'Confirmed Spill' },
            { date: '2026-06-11', volume_bbl: '4.8 bbl', substance: 'crude_oil', inspection_id: '[INS-0001-0182]', status: 'Confirmed Spill' },
            { date: '2026-10-01', volume_bbl: '3.1 bbl', substance: 'crude_oil', inspection_id: '[INS-0001-0198]', status: 'Confirmed Spill' },
          ],
          summary_stats: { 'Total Real Volume': '15.1 bbl', 'Excluded Detections': '1 (0.8 bbl)' },
        },
      ],
      timestamp: '2026-10-17T11:00:33Z',
    },
    {
      id: 'demo-q6-user',
      role: 'user',
      content: 'Which 3 wells in Northeast Block 7 had the most downtime in the last 4 months? Show a bar chart.',
      timestamp: '2026-10-17T11:00:40Z',
    },
    {
      id: 'demo-q6-assistant',
      role: 'assistant',
      content:
        'In Northeast Block 7 over the last 4 months (2026-06-16 to 2026-10-16), downtime is calculated deterministically as **7 days per non-producing weekly inspection**. The top 3 wells are:',
      evidence_ids: ['INS-0121-0185', 'INS-0138-0188', 'INS-0107-0192'],
      visual_blocks: [
        {
          type: 'bar_chart',
          title: 'Northeast Block 7 — Top 3 Downtime Wells (Last 4 Months)',
          categories: ['WELL-0121', 'WELL-0138', 'WELL-0107'],
          values: [49, 42, 42],
          unit: 'days',
          evidence_ids: ['INS-0121-0185', 'INS-0138-0188', 'INS-0107-0192'],
        },
      ],
      timestamp: '2026-10-17T11:00:43Z',
    },
    {
      id: 'demo-q7-user',
      role: 'user',
      content: 'Show on a map every well in Northeast Block 8 with a real spill in the last 90 days.',
      timestamp: '2026-10-17T11:00:50Z',
    },
    {
      id: 'demo-q7-assistant',
      role: 'assistant',
      content:
        'Geospatial plot of **4 confirmed spills** in Northeast Block 8 in the last 90 days (2026-07-19 to 2026-10-16):',
      evidence_ids: ['INS-0149-0195', 'INS-0151-0201', 'INS-0160-0199', 'INS-0162-0202'],
      visual_blocks: [
        {
          type: 'map',
          title: 'Northeast Block 8 — Active Spills (Last 90 Days)',
          center: { lat: 32.185, lng: -102.145 },
          pins: [
            { asset_id: 'WELL-0149', lat: 32.182, lng: -102.148, volume_bbl: 1.8, date: '2026-08-14', details: 'Stuffing box leak 1.8 bbl [INS-0149-0195]' },
            { asset_id: 'WELL-0151', lat: 32.189, lng: -102.141, volume_bbl: 4.5, date: '2026-09-24', details: 'Flowline leak 4.5 bbl [INS-0151-0201]' },
            { asset_id: 'WELL-0160', lat: 32.179, lng: -102.152, volume_bbl: 2.1, date: '2026-09-10', details: 'Valve flange seep 2.1 bbl [INS-0160-0199]' },
            { asset_id: 'WELL-0162', lat: 32.191, lng: -102.138, volume_bbl: 3.4, date: '2026-10-02', details: 'Polished rod packing 3.4 bbl [INS-0162-0202]' },
          ],
          evidence_ids: ['INS-0149-0195', 'INS-0151-0201', 'INS-0160-0199', 'INS-0162-0202'],
        },
      ],
      timestamp: '2026-10-17T11:00:53Z',
    },
    {
      id: 'demo-q8-user',
      role: 'user',
      content: 'Show a heatmap of 2026 spills by geographic area and month.',
      timestamp: '2026-10-17T11:01:00Z',
    },
    {
      id: 'demo-q8-assistant',
      role: 'assistant',
      content:
        'Fleetwide distribution of **141 confirmed spills** in 2026 across all four operating blocks and 10 months:',
      evidence_ids: ['REG-2026-SUMMARY'],
      visual_blocks: [
        {
          type: 'heatmap',
          title: '2026 Fleetwide Spills Heatmap (Area × Month)',
          x_labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct'],
          y_labels: ['SW Block 24', 'NE Block 7', 'SW Block 23', 'NE Block 8'],
          matrix: [
            [3, 4, 2, 5, 4, 6, 5, 7, 4, 3],
            [2, 3, 4, 3, 5, 4, 3, 4, 5, 2],
            [1, 2, 3, 2, 4, 3, 2, 3, 2, 1],
            [4, 3, 5, 4, 6, 5, 4, 6, 5, 4],
          ],
          totals: {
            'SW Block 24': 43,
            'NE Block 7': 35,
            'SW Block 23': 23,
            'NE Block 8': 46,
            'Fleet Total': 141,
          },
        },
      ],
      timestamp: '2026-10-17T11:01:03Z',
    },
  ],

  // Chapter 7: Q9, Q10
  7: [
    {
      id: 'demo-q9-user',
      role: 'user',
      content: 'Which rules has WELL-0001 broken in the last 12 months, and what is still open?',
      timestamp: '2026-10-17T11:01:10Z',
    },
    {
      id: 'demo-q9-assistant',
      role: 'assistant',
      content:
        'In the last 12 months, **WELL-0001 has 4 rule breaches and 2 open pending items** joined across regulatory filings and parsed Markdown repair narratives:',
      evidence_ids: ['REG-0001-004', 'REG-0001-005', 'MNT-0001-022', 'DOC:SOP-SPILL#4.1', 'DOC:REG-ENV#12.2'],
      visual_blocks: [
        {
          type: 'table',
          title: 'WELL-0001 — 12-Month Regulatory & SOP Compliance Audit',
          columns: [
            { key: 'rule_id', label: 'Rule ID' },
            { key: 'rule_name', label: 'Requirement' },
            { key: 'incident_date', label: 'Incident Date' },
            { key: 'status', label: 'Compliance Status' },
            { key: 'details', label: 'Audit Finding' },
            { key: 'evidence_id', label: 'Evidence' },
          ],
          rows: [
            { rule_id: 'SR-01', rule_name: 'Written Spill Report <= 5 Days', incident_date: '2026-06-11', status: 'Breached', details: 'Written report filed 12 days late on 23 Jun [REG-0001-004]', evidence_id: '[REG-0001-004]' },
            { rule_id: 'SR-02', rule_name: 'Spill Containment <= 4 Hours', incident_date: '2026-06-11', status: 'Breached', details: 'Containment took 7.0 hours per repair narrative [MNT-0001-022]', evidence_id: '[MNT-0001-022]' },
            { rule_id: 'SR-03', rule_name: 'Post-Cleanup Soil Sampling <= 60d', incident_date: '2026-06-11', status: 'Open / Overdue', details: 'Cleanup verification overdue since 2026-08-10', evidence_id: '[DOC:SOP-SPILL#4.1]' },
            { rule_id: 'RC-04', rule_name: 'Civil Penalty Payment <= 30 Days', incident_date: '2026-08-15', status: 'Open / Unpaid', details: '$5,000 regulatory fine unpaid past deadline [REG-0001-005]', evidence_id: '[REG-0001-005]' },
            { rule_id: 'RC-02', rule_name: 'Annual Mechanical Integrity Test', incident_date: '2026-04-10', status: 'Met / Compliant', details: 'MIT passed successfully with chart recording on file', evidence_id: '[REG-0001-003]' },
          ],
        },
      ],
      timestamp: '2026-10-17T11:01:13Z',
    },
    {
      id: 'demo-q10-user',
      role: 'user',
      content: 'In Southwest Block 24, which spills in the last 90 days were not contained within the SOP time limit?',
      timestamp: '2026-10-17T11:01:20Z',
    },
    {
      id: 'demo-q10-assistant',
      role: 'assistant',
      content:
        'Scanning free-text repair Markdown reports for Southwest Block 24 reveals **2 spills breaching the 4-hour SR-02 containment rule** [DOC:SOP-SPILL#4.2]:',
      evidence_ids: ['INS-0082-0194', 'INS-0100-0200', 'MNT-0082-028', 'MNT-0100-034', 'DOC:SOP-SPILL#4.2'],
      visual_blocks: [
        {
          type: 'table',
          title: 'Southwest Block 24 — SOP SR-02 Containment Delay Breaches (>4h)',
          columns: [
            { key: 'well_id', label: 'Well ID' },
            { key: 'spill_date', label: 'Spill Date' },
            { key: 'volume_bbl', label: 'Volume' },
            { key: 'containment_time', label: 'Containment Time' },
            { key: 'sop_limit', label: 'SOP Limit' },
            { key: 'repair_id', label: 'Repair Report' },
            { key: 'status', label: 'Status' },
          ],
          rows: [
            { well_id: 'WELL-0082', spill_date: '2026-08-18', volume_bbl: '6.2 bbl', containment_time: '7.1 hours', sop_limit: '4.0 hours', repair_id: 'MNT-0082-028', status: 'SR-02 Breach (3.1h Over)' },
            { well_id: 'WELL-0100', spill_date: '2026-09-12', volume_bbl: '7.8 bbl', containment_time: '8.1 hours', sop_limit: '4.0 hours', repair_id: 'MNT-0100-034', status: 'SR-02 Breach (4.1h Over)' },
          ],
        },
      ],
      timestamp: '2026-10-17T11:01:23Z',
    },
  ],

  // Chapter 8: Q11, Q12, Q13, Q15
  8: [
    {
      id: 'demo-q11-user',
      role: 'user',
      content: 'For the three wells we discussed yesterday, what have repairs cost this year?',
      timestamp: '2026-10-17T11:01:30Z',
    },
    {
      id: 'demo-q11-assistant',
      role: 'assistant',
      content:
        'Recalling the top 3 downtime wells in Northeast Block 7 from our earlier discussion (**WELL-0121, WELL-0138, WELL-0107**):\n\n- **WELL-0121:** $25,794 across 3 work orders [MNT-0121-022, MNT-0121-025, MNT-0121-028]\n- **WELL-0138:** $46,942 across 4 work orders [MNT-0138-019, MNT-0138-022, MNT-0138-025, MNT-0138-027]\n- **WELL-0107:** $5,176 across 1 work order [MNT-0107-024]\n- **Total 2026 Repair Spend:** **$77,912**',
      evidence_ids: ['MNT-0121-022', 'MNT-0121-025', 'MNT-0121-028', 'MNT-0138-019', 'MNT-0138-022', 'MNT-0138-025', 'MNT-0138-027', 'MNT-0107-024'],
      timestamp: '2026-10-17T11:01:33Z',
    },
    {
      id: 'demo-q12-user',
      role: 'user',
      content: 'The 15 Oct reading for WELL-0164 is wrong. The handheld thermal gun used in that inspection was faulty; the field crew re-measured the wellhead at 41.0 °C.',
      timestamp: '2026-10-17T11:01:40Z',
    },
    {
      id: 'demo-q12-assistant',
      role: 'assistant',
      content:
        'Operational temperature correction committed to append-only ledger [LEDGER-0001]:\n\n- **Asset:** WELL-0164 (T200, NE-08)\n- **Corrected Wellhead Temp:** 41.0 °C (was 24.0 °C, Ambient: 19.9 °C ➔ New ΔT = 21.1 °C)\n- **Producing Status:** Updated from **stopped ➔ PRODUCING** (ΔT 21.1 °C > 15.0 °C threshold per [DOC:OM-T200#9.3])\n- **Conflict Flagged:** Conflict detected with Tyler Hughes\'s inspector remark (*"Pump jack not moving"* in [INS-0164-0205]). Unresolved conflict preserved in audit trail.\n- **Reactive Rebuild:** Re-evaluating Q2 removes WELL-0164; only 3 stopped wells remain in NE-08.',
      evidence_ids: ['LEDGER-0001', 'INS-0164-0205', 'DOC:OM-T200#9.3'],
      timestamp: '2026-10-17T11:01:43Z',
    },
    {
      id: 'demo-q13-user',
      role: 'user',
      content: 'The AI estimated the 24 Sep spill at WELL-0151 as 4.5 bbl. The field crew measured 5.4 bbl.',
      timestamp: '2026-10-17T11:01:50Z',
    },
    {
      id: 'demo-q13-assistant',
      role: 'assistant',
      content:
        'Spill volume correction committed to append-only ledger [LEDGER-0002]:\n\n- **Asset:** WELL-0151 | **Date:** 2026-09-24\n- **Volume:** Updated from **4.5 bbl ➔ 5.4 bbl**\n- **Regulatory Threshold Cascade:** Crossing the 5.0 bbl threshold converts this from a minor leak into a **Reportable Spill** under [DOC:SOP-SPILL#3.1]!\n- **Breach Triggered:** **SR-01 Violation** — Written report to state regulator was due within 5 calendar days (due 2026-09-29, currently OVERDUE).\n- **Repair Update:** Invalidates "moderate" classification in [MNT-0151-025]. Containment time (6.4h) flagged under SR-02 (>4h). Post-cleanup SR-03 audit scheduled for 2026-11-23.',
      evidence_ids: ['LEDGER-0002', 'INS-0151-0201', 'MNT-0151-025', 'DOC:SOP-SPILL#3.1'],
      timestamp: '2026-10-17T11:01:53Z',
    },
    {
      id: 'demo-q15-user',
      role: 'user',
      content: '[Jessica Reed, Field Inspector] Is WELL-0164 producing oil right now?',
      timestamp: '2026-10-17T11:02:00Z',
    },
    {
      id: 'demo-q15-assistant',
      role: 'assistant',
      content:
        'Yes, **WELL-0164 is PRODUCING OIL**.\n\n- **Wellhead Temp:** 41.0 °C (Ambient 19.9 °C, ΔT = 21.1 °C > 15.0 °C threshold [DOC:OM-T200#9.3])\n- **Source:** Overridden via runtime ledger entry [LEDGER-0001] submitted by Michael Turner (field crew re-measurement with calibrated thermal gun).\n- **Notice:** Note conflict with Tyler Hughes\'s inspector remark (*"Pump jack not moving"*) remains open for visual crew verification.',
      evidence_ids: ['LEDGER-0001', 'INS-0164-0205', 'DOC:OM-T200#9.3'],
      visual_blocks: [
        {
          type: 'status_card',
          asset_id: 'WELL-0164',
          name: 'Well 0164',
          well_type: 'T200',
          area_name: 'Northeast Block 8',
          is_producing: true,
          metrics: {
            wellhead_temp_c: 41.0,
            ambient_temp_c: 19.9,
            delta_temp_c: 21.1,
            threshold_temp_delta: 15.0,
          },
          system_status: {
            recorded_status: 'producing (ledger override)',
            status_is_stale: false,
          },
          latest_inspection: {
            inspection_id: 'INS-0164-0205',
            date: '2026-10-15',
            inspector: 'Tyler Hughes',
          },
          reason: 'Producing via Michael Turner correction [LEDGER-0001]; conflict with Tyler remark active',
          evidence_ids: ['LEDGER-0001', 'INS-0164-0205', 'DOC:OM-T200#9.3'],
        },
      ],
      timestamp: '2026-10-17T11:02:03Z',
    },
  ],

  // Chapter 9: Q14, Q16
  9: [
    {
      id: 'demo-q14-user',
      role: 'user',
      content: 'Note for all T350 wells: our team now wants a pump jack root-cause analysis after 2 repairs, not 3.',
      timestamp: '2026-10-17T11:02:10Z',
    },
    {
      id: 'demo-q14-assistant',
      role: 'assistant',
      content:
        'Scoped rule override committed to ledger [LEDGER-0003]:\n\n- **Parameter:** `rca_repair_threshold` = **2**\n- **Scope:** `well_type = "T350"` | **Author:** Michael Turner [U-201]\n- **Precedence:** Scope hierarchy (`well > well_type > fleet > manual`) overrides baseline manual [DOC:OM-T350#11.4].\n- **Impact:** **WELL-0120** (T350, 2 pump jack repairs in 2026: [MNT-0120-019], [MNT-0120-023]) is now flagged for mandatory Root Cause Analysis!\n- **Scope Containment:** T200 wells (such as WELL-0102 with 2 repairs) are **strictly excluded**, preserving boundary integrity.',
      evidence_ids: ['LEDGER-0003', 'MNT-0120-019', 'MNT-0120-023', 'DOC:OM-T350#11.4'],
      timestamp: '2026-10-17T11:02:13Z',
    },
    {
      id: 'demo-q16-user',
      role: 'user',
      content: '[Jessica Reed, Field Inspector] For the three wells we discussed yesterday, what have repairs cost this year?',
      timestamp: '2026-10-17T11:02:20Z',
    },
    {
      id: 'demo-q16-assistant',
      role: 'assistant',
      content:
        'No earlier conversation found for user U-202 (Jessica Reed).\n\n*Code-Enforced Privacy Note:* Private session recall strictly enforces `WHERE user_id = ?`. Past discussion history between Michael Turner [U-201] and the copilot is strictly isolated and inaccessible to other team members.',
      evidence_ids: [],
      timestamp: '2026-10-17T11:02:22Z',
    },
  ],

  // Chapter 10: Q17, Q18
  10: [
    {
      id: 'demo-q17-user',
      role: 'user',
      content: 'WELL-0175 is running fine.',
      timestamp: '2026-10-17T11:02:30Z',
    },
    {
      id: 'demo-q17-assistant',
      role: 'assistant',
      content:
        'Contradiction detected between human claim and empirical sensor data:\n\n- **Operator Claim:** Tyler Hughes asserts WELL-0175 is running fine.\n- **Empirical Telemetry:** Drone inspection [INS-0175-0205] on 2026-10-15 measured wellhead temp at 20.2 °C vs ambient 19.8 °C (ΔT = 0.4 °C), far below the 15.0 °C threshold per [DOC:OM-T200#9.3]. Michael Turner also logged a shut-in.\n- **Status:** Operator assertion marked **UNCONFIRMED**. The copilot refuses to silently overwrite empirical data and surfaces both perspectives for field supervisor review.',
      evidence_ids: ['INS-0175-0205', 'DOC:OM-T200#9.3'],
      visual_blocks: [
        {
          type: 'conflict',
          title: 'WELL-0175 — Disputed Operational Status',
          asset_id: 'WELL-0175',
          item: 'Operational Running Status',
          claims: [
            { source: 'Tyler Hughes (Field Remark)', statement: 'WELL-0175 is running fine.', timestamp: '2026-10-16' },
            { source: 'Drone Inspection [INS-0175-0205]', statement: 'Wellhead ΔT = 0.4 °C < 15.0 °C threshold (stopped)', timestamp: '2026-10-15' },
          ],
          recommendation: 'Do not mark active. Dispatch crew for thermal verification and field check.',
          evidence_ids: ['INS-0175-0205', 'DOC:OM-T200#9.3'],
        },
      ],
      timestamp: '2026-10-17T11:02:33Z',
    },
    {
      id: 'demo-q18-user',
      role: 'user',
      content: 'Was the 20 Aug spill at WELL-0101 real oil?',
      timestamp: '2026-10-17T11:02:40Z',
    },
    {
      id: 'demo-q18-assistant',
      role: 'assistant',
      content:
        'Yes, the 2026-08-20 spill at **WELL-0101 was CONFIRMED CRUDE OIL**, despite conflicting operator notes:\n\n- **Water Claim:** Ryan Brooks [CTX-0101-002] noted the puddle appeared to be produced water runoff.\n- **HSE Lab Confirmation:** Chris Dalton [CTX-0101-003] tested fluid samples and confirmed crude emulsion.\n- **Physical Evidence:** Repair report [MNT-0101-029] executed a flowline patch and vacuum truck crude recovery of 3.2 bbl.\n- **Resolution:** Confirmed as real oil spill while fully preserving Ryan Brooks\'s note in the audit trail.',
      evidence_ids: ['CTX-0101-002', 'CTX-0101-003', 'MNT-0101-029', 'INS-0101-0197'],
      visual_blocks: [
        {
          type: 'conflict',
          title: 'WELL-0101 — Spill Fluid Substance Dispute',
          asset_id: 'WELL-0101',
          item: 'Spill Fluid Classification (20 Aug 2026)',
          claims: [
            { source: 'Ryan Brooks [CTX-0101-002]', statement: 'Appeared to be produced water runoff from wash tank.', timestamp: '2026-08-20' },
            { source: 'Chris Dalton HSE [CTX-0101-003]', statement: 'Sample confirmed crude oil emulsion.', timestamp: '2026-08-21' },
            { source: 'Work Order [MNT-0101-029]', statement: 'Flowline repaired and 3.2 bbl crude collected by vac truck.', timestamp: '2026-08-22' },
          ],
          recommendation: 'Classified as crude oil in regulatory spill totals. Disputed claim preserved.',
          evidence_ids: ['CTX-0101-002', 'CTX-0101-003', 'MNT-0101-029', 'INS-0101-0197'],
        },
      ],
      timestamp: '2026-10-17T11:02:43Z',
    },
  ],
}

interface DemoDirectorProps {
  viewMode: 'console' | 'brag'
  onSetViewMode: (mode: 'console' | 'brag') => void
  onSetCurrentUser: (user: UserOption) => void
  users: UserOption[]
  onInjectMessages: (messages: ChatMessage[]) => void
  onClearMessages: () => void
  onScrollToChapter: (chapterId: string) => void
}

export const DemoDirector: React.FC<DemoDirectorProps> = ({
  viewMode,
  onSetViewMode,
  onSetCurrentUser,
  users,
  onInjectMessages,
  onClearMessages,
  onScrollToChapter,
}) => {
  const [isPlaying, setIsPlaying] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [elapsedSeconds, setElapsedSeconds] = useState(0)
  const [activeChapterIndex, setActiveChapterIndex] = useState(0)
  const [currentSentenceIndex, setCurrentSentenceIndex] = useState(0)
  const [speechRate, setSpeechRate] = useState<number>(1.05)
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([])
  const [selectedVoiceIndex, setSelectedVoiceIndex] = useState<number>(0)
  const [isMuted, setIsMuted] = useState(false)
  const [replayMode, setReplayMode] = useState<'deterministic' | 'live'>('deterministic')

  // Screen/tab recording state
  const [isRecording, setIsRecording] = useState(false)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const streamRef = useRef<MediaStream | null>(null)

  // Web Audio pipeline for digital voiceover mixing directly into MediaRecorder
  const audioCtxRef = useRef<AudioContext | null>(null)
  const audioDestRef = useRef<MediaStreamAudioDestinationNode | null>(null)
  const audioElementRef = useRef<HTMLAudioElement | null>(null)
  const audioSourceRef = useRef<MediaElementAudioSourceNode | null>(null)
  const [isAudioSpeaking, setIsAudioSpeaking] = useState(false)

  const isTourActiveRef = useRef(false)
  const synthRef = useRef<SpeechSynthesis | null>(null)
  const secondTimerRef = useRef<any>(null)
  const sentenceTimerRef = useRef<any>(null)

  // Helper to lazily initialize Web Audio pipeline
  const getAudioPipeline = () => {
    try {
      if (!audioCtxRef.current) {
        const AudioCtxClass = window.AudioContext || (window as any).webkitAudioContext
        if (!AudioCtxClass) return null
        const ctx = new AudioCtxClass()
        const dest = ctx.createMediaStreamDestination()

        const audioEl = new Audio()
        audioEl.crossOrigin = 'anonymous'

        const source = ctx.createMediaElementSource(audioEl)
        source.connect(ctx.destination) // Output to speakers so operator hears it live
        source.connect(dest)            // Route directly to recording destination!

        audioCtxRef.current = ctx
        audioDestRef.current = dest
        audioElementRef.current = audioEl
        audioSourceRef.current = source
      }

      if (audioCtxRef.current && audioCtxRef.current.state === 'suspended') {
        audioCtxRef.current.resume().catch(() => {})
      }

      return {
        ctx: audioCtxRef.current,
        dest: audioDestRef.current,
        audioEl: audioElementRef.current,
      }
    } catch (err) {
      console.warn('Web Audio initialization fallback:', err)
      return null
    }
  }

  // Load voices on mount
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
      if (synthRef.current) synthRef.current.cancel()
      if (audioElementRef.current) {
        audioElementRef.current.pause()
        audioElementRef.current.currentTime = 0
      }
      if (secondTimerRef.current) clearInterval(secondTimerRef.current)
      if (sentenceTimerRef.current) clearTimeout(sentenceTimerRef.current)
    }
  }, [])

  // 1-Second ticker for overall 0:00 to 5:00 progress
  useEffect(() => {
    if (isPlaying && !isPaused) {
      secondTimerRef.current = setInterval(() => {
        setElapsedSeconds(prev => {
          if (prev >= 300) {
            handleCompleteDemo()
            return 300
          }
          return prev + 1
        })
      }, 1000)
    } else {
      if (secondTimerRef.current) clearInterval(secondTimerRef.current)
    }
    return () => {
      if (secondTimerRef.current) clearInterval(secondTimerRef.current)
    }
  }, [isPlaying, isPaused])

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60)
    const s = secs % 60
    return `${m}:${s < 10 ? '0' : ''}${s}`
  }

  // Speak a sentence in the active chapter using Web Audio pipeline (or synthesis fallback)
  const speakSentence = (chapterIdx: number, sentenceIdx: number) => {
    if (!isTourActiveRef.current) return

    const chapter = DEMO_CHAPTERS[chapterIdx]
    if (!chapter) {
      handleCompleteDemo()
      return
    }

    // Set persona if specified
    if (chapter.personaUserId) {
      const found = users.find(u => u.user_id === chapter.personaUserId)
      if (found) {
        onSetCurrentUser(found)
      }
    }

    // Handle view transitions & content injection
    if (chapter.targetView === 'brag') {
      if (viewMode !== 'brag') {
        onSetViewMode('brag')
      }
      if (chapter.targetElementId) {
        setTimeout(() => {
          onScrollToChapter(chapter.targetElementId!)
        }, 150)
      }
    } else if (chapter.targetView === 'console') {
      if (viewMode !== 'console') {
        onSetViewMode('console')
      }
      // Inject query fixtures for this chapter if starting chapter
      if (sentenceIdx === 0 && LIVE_DEMO_FIXTURES[chapter.id]) {
        onInjectMessages(LIVE_DEMO_FIXTURES[chapter.id])
        setTimeout(() => {
          const chatContainer = document.getElementById('chat-messages-container')
          if (chatContainer) {
            chatContainer.scrollTo({ top: chatContainer.scrollHeight, behavior: 'smooth' })
          }
        }, 200)
      }
    }

    setActiveChapterIndex(chapterIdx)
    setCurrentSentenceIndex(sentenceIdx)

    const sentences = chapter.sentences
    if (sentenceIdx >= sentences.length) {
      // Completed all sentences for this chapter
      if (chapterIdx + 1 < DEMO_CHAPTERS.length) {
        const nextChapter = DEMO_CHAPTERS[chapterIdx + 1]
        // Smoothly wait until the startSec of next chapter or advance
        const waitMs = Math.max(300, (nextChapter.startSec - elapsedSeconds) * 1000)
        sentenceTimerRef.current = setTimeout(() => {
          if (isTourActiveRef.current) {
            speakSentence(chapterIdx + 1, 0)
          }
        }, Math.min(waitMs, 4000))
      } else {
        handleCompleteDemo()
      }
      return
    }

    if (isMuted) {
      const durationMs = Math.max(2800, (sentences[sentenceIdx].length / 14) * 1000 / speechRate)
      sentenceTimerRef.current = setTimeout(() => {
        if (isTourActiveRef.current) {
          speakSentence(chapterIdx, sentenceIdx + 1)
        }
      }, durationMs)
      return
    }

    // Attempt to play pre-synthesized WAV audio routed via Web Audio to speakers + recording stream
    const pipeline = getAudioPipeline()
    const audioEl = pipeline?.audioEl

    const playFallbackSpeech = () => {
      setIsAudioSpeaking(false)
      if (synthRef.current) {
        synthRef.current.cancel()
        const utterance = new SpeechSynthesisUtterance(sentences[sentenceIdx])
        utterance.rate = speechRate
        if (voices[selectedVoiceIndex]) {
          utterance.voice = voices[selectedVoiceIndex]
        }
        utterance.onend = () => {
          if (isTourActiveRef.current) {
            sentenceTimerRef.current = setTimeout(() => {
              speakSentence(chapterIdx, sentenceIdx + 1)
            }, 150)
          }
        }
        utterance.onerror = () => {
          if (isTourActiveRef.current) {
            sentenceTimerRef.current = setTimeout(() => {
              speakSentence(chapterIdx, sentenceIdx + 1)
            }, 200)
          }
        }
        synthRef.current.speak(utterance)
      } else {
        const durationMs = Math.max(2800, (sentences[sentenceIdx].length / 14) * 1000 / speechRate)
        sentenceTimerRef.current = setTimeout(() => {
          if (isTourActiveRef.current) {
            speakSentence(chapterIdx, sentenceIdx + 1)
          }
        }, durationMs)
      }
    }

    if (audioEl) {
      try {
        const audioSrc = `/audio/ch_${chapter.id}_${sentenceIdx}.wav`
        audioEl.src = audioSrc
        audioEl.playbackRate = speechRate
        audioEl.muted = isMuted

        audioEl.onplay = () => {
          setIsAudioSpeaking(true)
        }

        audioEl.onended = () => {
          setIsAudioSpeaking(false)
          if (isTourActiveRef.current) {
            sentenceTimerRef.current = setTimeout(() => {
              speakSentence(chapterIdx, sentenceIdx + 1)
            }, 200)
          }
        }

        audioEl.onerror = () => {
          console.warn(`Audio clip ${audioSrc} failed to load, falling back to speech synthesis`)
          playFallbackSpeech()
        }

        const playPromise = audioEl.play()
        if (playPromise !== undefined) {
          playPromise.catch(err => {
            console.warn('Audio play prevented or interrupted:', err)
            playFallbackSpeech()
          })
        }
      } catch (err) {
        console.warn('Audio setup error:', err)
        playFallbackSpeech()
      }
    } else {
      playFallbackSpeech()
    }
  }

  const handleStartDemo = (startFromChapterIdx = 0) => {
    getAudioPipeline()
    if (synthRef.current) synthRef.current.cancel()
    if (audioElementRef.current) {
      audioElementRef.current.pause()
      audioElementRef.current.currentTime = 0
    }
    if (secondTimerRef.current) clearInterval(secondTimerRef.current)
    if (sentenceTimerRef.current) clearTimeout(sentenceTimerRef.current)

    isTourActiveRef.current = true
    setIsPlaying(true)
    setIsPaused(false)
    setActiveChapterIndex(startFromChapterIdx)
    setElapsedSeconds(DEMO_CHAPTERS[startFromChapterIdx].startSec)
    setCurrentSentenceIndex(0)

    if (startFromChapterIdx >= 4) {
      // Starting from Part 2
      onSetViewMode('console')
    } else {
      // Starting from Part 1
      onSetViewMode('brag')
      onClearMessages()
    }

    speakSentence(startFromChapterIdx, 0)
  }

  const handlePauseResume = () => {
    if (!isPlaying) return
    if (isPaused) {
      setIsPaused(false)
      isTourActiveRef.current = true
      if (audioElementRef.current && audioElementRef.current.paused) {
        audioElementRef.current.play().catch(() => {})
      }
      if (synthRef.current && synthRef.current.paused) {
        synthRef.current.resume()
      }
    } else {
      setIsPaused(true)
      isTourActiveRef.current = false
      if (audioElementRef.current && !audioElementRef.current.paused) {
        audioElementRef.current.pause()
      }
      if (synthRef.current && synthRef.current.speaking) {
        synthRef.current.cancel()
      }
      if (sentenceTimerRef.current) clearTimeout(sentenceTimerRef.current)
    }
  }

  const handleJumpToChapter = (chapterIdx: number) => {
    const target = DEMO_CHAPTERS[chapterIdx]
    if (!target) return
    if (isPlaying) {
      handleStartDemo(chapterIdx)
    } else {
      setActiveChapterIndex(chapterIdx)
      setElapsedSeconds(target.startSec)
      setCurrentSentenceIndex(0)
      if (target.targetView === 'brag') {
        onSetViewMode('brag')
        if (target.targetElementId) onScrollToChapter(target.targetElementId)
      } else {
        onSetViewMode('console')
      }
    }
  }

  const handleResetDemo = () => {
    isTourActiveRef.current = false
    setIsPlaying(false)
    setIsPaused(false)
    setIsAudioSpeaking(false)
    setElapsedSeconds(0)
    setActiveChapterIndex(0)
    setCurrentSentenceIndex(0)
    if (audioElementRef.current) {
      audioElementRef.current.pause()
      audioElementRef.current.currentTime = 0
    }
    if (synthRef.current) synthRef.current.cancel()
    if (secondTimerRef.current) clearInterval(secondTimerRef.current)
    if (sentenceTimerRef.current) clearTimeout(sentenceTimerRef.current)

    if (isRecording) {
      stopRecording()
    }
  }

  const handleCompleteDemo = () => {
    isTourActiveRef.current = false
    setIsPlaying(false)
    setIsPaused(false)
    setIsAudioSpeaking(false)
    if (audioElementRef.current) {
      audioElementRef.current.pause()
      audioElementRef.current.currentTime = 0
    }
    if (synthRef.current) synthRef.current.cancel()
    if (secondTimerRef.current) clearInterval(secondTimerRef.current)
    if (sentenceTimerRef.current) clearTimeout(sentenceTimerRef.current)

    if (isRecording) {
      stopRecording()
    }
  }

  // ── IN-BROWSER MEDIA RECORDER (TAB/SCREEN VIDEO + DIGITALLY MIXED AUDIO) ──
  const startRecording = async () => {
    try {
      // 1. Ensure audio pipeline is active
      const pipeline = getAudioPipeline()
      if (pipeline?.ctx && pipeline.ctx.state === 'suspended') {
        await pipeline.ctx.resume()
      }

      // 2. Prompt user for display media (Screen or Tab)
      const displayStream = await (navigator.mediaDevices as any).getDisplayMedia({
        video: { frameRate: 30, displaySurface: 'browser' },
        audio: true,
      })

      streamRef.current = displayStream

      // 3. Connect display tab audio if present
      if (pipeline?.dest && pipeline.ctx && displayStream.getAudioTracks().length > 0) {
        try {
          const displayAudioSource = pipeline.ctx.createMediaStreamSource(displayStream)
          displayAudioSource.connect(pipeline.dest)
        } catch (e) {
          console.warn('Could not connect display audio track:', e)
        }
      }

      // 4. Optionally connect microphone if allowed
      if (pipeline?.dest && pipeline.ctx) {
        try {
          const micStream = await navigator.mediaDevices.getUserMedia({ audio: true })
          const micSource = pipeline.ctx.createMediaStreamSource(micStream)
          micSource.connect(pipeline.dest)
        } catch (e) {
          console.log('Microphone not attached; recording pure digital studio narration.')
        }
      }

      // 5. Combine screen video with our Web Audio destination (where narration is playing)
      const audioTracks = pipeline?.dest?.stream.getAudioTracks() || displayStream.getAudioTracks()
      const combinedStream = new MediaStream([
        ...displayStream.getVideoTracks(),
        ...audioTracks,
      ])

      const chunks: BlobPart[] = []

      const mimeType = MediaRecorder.isTypeSupported('video/webm;codecs=vp9,opus')
        ? 'video/webm;codecs=vp9,opus'
        : MediaRecorder.isTypeSupported('video/webm;codecs=vp8,opus')
        ? 'video/webm;codecs=vp8,opus'
        : MediaRecorder.isTypeSupported('video/webm')
        ? 'video/webm'
        : 'video/mp4'

      const recorder = new MediaRecorder(combinedStream, { mimeType, audioBitsPerSecond: 128000 })
      mediaRecorderRef.current = recorder

      recorder.ondataavailable = e => {
        if (e.data && e.data.size > 0) {
          chunks.push(e.data)
        }
      }

      recorder.onstop = () => {
        const blob = new Blob(chunks, { type: mimeType })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `DonkE_Asset_Intelligence_Demo_${new Date().toISOString().slice(0, 10)}.webm`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)

        if (streamRef.current) {
          streamRef.current.getTracks().forEach(t => t.stop())
        }
        setIsRecording(false)
      }

      // Automatically stop if user clicks "Stop sharing" in browser bar
      displayStream.getVideoTracks()[0].onended = () => {
        stopRecording()
      }

      recorder.start(1000)
      setIsRecording(true)

      // If demo is not already playing, start it from 0
      if (!isPlaying) {
        handleStartDemo(0)
      }
    } catch (err: any) {
      console.warn('Screen capture cancelled or not allowed:', err)
      alert(
        'Recording Setup: Select "Entire Screen" or "This Tab". Voiceover is digitally mixed into the WebM recording!'
      )
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop())
    }
    setIsRecording(false)
  }

  const activeChapter = DEMO_CHAPTERS[activeChapterIndex] || DEMO_CHAPTERS[0]
  const currentSentence =
    activeChapter?.sentences[currentSentenceIndex] || activeChapter?.sentences[0] || ''

  return (
    <>
      {/* ── 1. UNIFIED FLOATING CONTROLLER (TOP DOCK) ── */}
      <div
        style={{
          position: 'sticky',
          top: 0,
          zIndex: 45,
          background: '#09090b',
          borderBottom: '1px solid #27272a',
          boxShadow: '0 4px 20px rgba(0,0,0,0.6)',
          padding: '8px 16px',
        }}
      >
        <div
          style={{
            maxWidth: '1360px',
            margin: '0 auto',
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '12px',
          }}
        >
          {/* Left: Branding & Timer */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span
                style={{
                  fontSize: '12.5px',
                  fontFamily: "'JetBrains Mono', monospace",
                  fontWeight: 700,
                  color: '#f59e0b',
                  letterSpacing: '-0.2px',
                }}
              >
                DEMO DIRECTOR
              </span>
              <span
                style={{
                  fontSize: '9px',
                  fontFamily: "'JetBrains Mono', monospace",
                  fontWeight: 600,
                  padding: '1px 5px',
                  borderRadius: '3px',
                  background: activeChapterIndex < 4 ? '#18181b' : 'rgba(56, 189, 248, 0.15)',
                  border: '1px solid #27272a',
                  color: activeChapterIndex < 4 ? '#f59e0b' : '#38bdf8',
                }}
              >
                {activeChapterIndex < 4 ? 'PART 1: ARCHITECTURE' : 'PART 2: LIVE QUERIES'}
              </span>
            </div>

            {/* Time Indicator & Progress Pill */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '12px',
                fontFamily: "'JetBrains Mono', monospace",
                background: '#121215',
                border: '1px solid #27272a',
                borderRadius: '6px',
                padding: '3px 8px',
              }}
            >
              <Clock size={12} color="#a1a1aa" />
              <span style={{ color: '#f4f4f5', fontWeight: 600 }}>{formatTime(elapsedSeconds)}</span>
              <span style={{ color: '#71717a' }}>/ 5:00</span>
            </div>
          </div>

          {/* Center: Play / Pause / Reset & Primary Action */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {!isPlaying ? (
              <button
                onClick={() => handleStartDemo(0)}
                style={{
                  background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
                  color: '#09090b',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '6px 14px',
                  fontSize: '12px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  boxShadow: '0 2px 10px rgba(245, 158, 11, 0.3)',
                  transition: 'all 0.15s ease',
                }}
              >
                <Play size={13} fill="#09090b" />
                <span>🎬 Run Full 5-Min Auto-Narrated Video Demo</span>
              </button>
            ) : (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  background: '#121215',
                  border: '1px solid #27272a',
                  borderRadius: '6px',
                  padding: '2px',
                }}
              >
                <button
                  onClick={() => handleJumpToChapter(Math.max(0, activeChapterIndex - 1))}
                  style={{
                    padding: '4px 8px',
                    borderRadius: '4px',
                    background: 'transparent',
                    border: 'none',
                    color: '#a1a1aa',
                    cursor: 'pointer',
                  }}
                  title="Previous Chapter"
                >
                  <SkipBack size={12} />
                </button>
                <button
                  onClick={handlePauseResume}
                  style={{
                    padding: '4px 10px',
                    borderRadius: '4px',
                    background: '#27272a',
                    border: 'none',
                    color: '#f4f4f5',
                    fontSize: '11px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                  }}
                >
                  {isPaused ? <Play size={11} fill="#f4f4f5" /> : <Pause size={11} />}
                  <span>{isPaused ? 'Resume' : 'Pause'}</span>
                </button>
                <button
                  onClick={() => handleJumpToChapter(Math.min(DEMO_CHAPTERS.length - 1, activeChapterIndex + 1))}
                  style={{
                    padding: '4px 8px',
                    borderRadius: '4px',
                    background: 'transparent',
                    border: 'none',
                    color: '#a1a1aa',
                    cursor: 'pointer',
                  }}
                  title="Next Chapter"
                >
                  <SkipForward size={12} />
                </button>
                <button
                  onClick={handleResetDemo}
                  style={{
                    padding: '4px 8px',
                    borderRadius: '4px',
                    background: 'transparent',
                    border: 'none',
                    color: '#ef4444',
                    cursor: 'pointer',
                  }}
                  title="Reset Demo to 0:00"
                >
                  <RotateCcw size={12} />
                </button>
              </div>
            )}

            {/* In-Browser Tab Recording Button */}
            {!isRecording ? (
              <button
                onClick={startRecording}
                style={{
                  background: '#18181b',
                  color: '#ef4444',
                  border: '1px solid rgba(239, 68, 68, 0.4)',
                  borderRadius: '6px',
                  padding: '6px 10px',
                  fontSize: '11.5px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  transition: 'all 0.15s ease',
                }}
                title="Record browser tab audio & video to WebM"
              >
                <span
                  style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    background: '#ef4444',
                    display: 'inline-block',
                  }}
                />
                <span>🔴 Record Tab to WebM</span>
              </button>
            ) : (
              <button
                onClick={stopRecording}
                style={{
                  background: '#ef4444',
                  color: '#09090b',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '6px 12px',
                  fontSize: '11.5px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  animation: 'pulse 1.5s infinite',
                }}
              >
                <Download size={13} />
                <span>Stop &amp; Save Recording</span>
              </button>
            )}

            {/* Replay Mode Toggle */}
            <button
              onClick={() =>
                setReplayMode(prev => (prev === 'deterministic' ? 'live' : 'deterministic'))
              }
              style={{
                background: '#121215',
                border: '1px solid #27272a',
                borderRadius: '6px',
                padding: '5px 9px',
                fontSize: '11px',
                fontFamily: "'JetBrains Mono', monospace",
                color: replayMode === 'deterministic' ? '#10b981' : '#f59e0b',
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px',
              }}
              title="Toggle between deterministic verified fixtures and live LLM streaming"
            >
              {replayMode === 'deterministic' ? <Zap size={11} /> : <Sparkles size={11} />}
              <span>{replayMode === 'deterministic' ? '⚡ Replay Mode' : '🤖 Live LLM'}</span>
            </button>
          </div>

          {/* Right: Audio Voice Status & Speed Controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {/* Audio Pipeline Status Badge */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '4px 8px',
                borderRadius: '6px',
                background: '#121215',
                border: '1px solid #27272a',
                fontSize: '11px',
                fontFamily: "'JetBrains Mono', monospace",
              }}
              title="Studio voiceover is digitally routed into the WebM recording"
            >
              <span
                style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  background: isAudioSpeaking ? '#10b981' : '#71717a',
                  display: 'inline-block',
                }}
              />
              <span style={{ color: isAudioSpeaking ? '#10b981' : '#a1a1aa', fontWeight: 600 }}>
                {isAudioSpeaking ? 'Voice: Live (WAV)' : 'Voice: Studio WAV'}
              </span>
            </div>

            <button
              onClick={() => {
                const next = speechRate === 1.0 ? 1.05 : speechRate === 1.05 ? 1.15 : speechRate === 1.15 ? 1.25 : 1.0
                setSpeechRate(next)
              }}
              style={{
                background: '#121215',
                border: '1px solid #27272a',
                borderRadius: '6px',
                padding: '4px 8px',
                fontSize: '11px',
                fontFamily: "'JetBrains Mono', monospace",
                color: '#a1a1aa',
                cursor: 'pointer',
              }}
              title="Voice playback rate"
            >
              {speechRate}x
            </button>

            <button
              onClick={() => setIsMuted(!isMuted)}
              style={{
                background: '#121215',
                border: '1px solid #27272a',
                borderRadius: '6px',
                padding: '5px 7px',
                color: isMuted ? '#ef4444' : '#a1a1aa',
                cursor: 'pointer',
              }}
              title={isMuted ? 'Unmute Audio' : 'Mute Voice (Subtitles Only)'}
            >
              {isMuted ? <VolumeX size={12} /> : <Volume2 size={12} />}
            </button>
          </div>
        </div>

        {/* ── CHAPTER SCRUBBER BAR (10 CLICKABLE CHAPTER PILLS) ── */}
        <div
          style={{
            maxWidth: '1360px',
            margin: '6px auto 0 auto',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            overflowX: 'auto',
            paddingBottom: '2px',
          }}
        >
          {DEMO_CHAPTERS.map((ch, idx) => {
            const isActive = activeChapterIndex === idx
            const isCompleted = elapsedSeconds >= ch.endSec
            return (
              <button
                key={ch.id}
                onClick={() => handleJumpToChapter(idx)}
                style={{
                  flex: 1,
                  minWidth: '100px',
                  background: isActive ? '#1c1c22' : '#121215',
                  border: isActive
                    ? '1px solid #f59e0b'
                    : isCompleted
                    ? '1px solid #27272a'
                    : '1px solid #1f1f23',
                  borderRadius: '4px',
                  padding: '3px 6px',
                  textAlign: 'left',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                  position: 'relative',
                  overflow: 'hidden',
                }}
                title={`${ch.timeRange} — ${ch.title}`}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '2px' }}>
                  <span
                    style={{
                      fontSize: '9px',
                      fontFamily: "'JetBrains Mono', monospace",
                      fontWeight: 700,
                      color: isActive ? '#f59e0b' : isCompleted ? '#10b981' : '#71717a',
                    }}
                  >
                    CH {ch.id} ({ch.timeRange})
                  </span>
                  {isActive && isPlaying && (
                    <span
                      style={{
                        width: '6px',
                        height: '6px',
                        borderRadius: '50%',
                        background: '#f59e0b',
                        display: 'inline-block',
                      }}
                    />
                  )}
                </div>
                <div
                  style={{
                    fontSize: '10px',
                    fontWeight: 500,
                    color: isActive ? '#f4f4f5' : '#a1a1aa',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                >
                  {ch.title.split('(')[0]}
                </div>
              </button>
            )
          })}
        </div>
      </div>

      {/* ── 2. HIGH-CONTRAST BOTTOM TELEPROMPTER / CLOSED-CAPTION SUBTITLE BAR ── */}
      <div
        style={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          zIndex: 50,
          background: 'rgba(9, 9, 11, 0.98)',
          borderTop: '1px solid #27272a',
          backdropFilter: 'blur(12px)',
          padding: '10px 20px',
          boxShadow: '0 -10px 40px rgba(0, 0, 0, 0.8)',
        }}
      >
        <div
          style={{
            maxWidth: '1360px',
            margin: '0 auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '6px',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '12px',
            }}
          >
            {/* Audio Wave Visualizer & Chapter Badge */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexShrink: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '2px', height: '16px' }}>
                <span
                  style={{
                    width: '3px',
                    height: isAudioSpeaking ? '16px' : isPlaying && !isPaused ? '10px' : '4px',
                    borderRadius: '2px',
                    background: isAudioSpeaking ? '#10b981' : '#f59e0b',
                    transition: 'all 0.15s ease',
                  }}
                />
                <span
                  style={{
                    width: '3px',
                    height: isAudioSpeaking ? '20px' : isPlaying && !isPaused ? '14px' : '6px',
                    borderRadius: '2px',
                    background: isAudioSpeaking ? '#10b981' : '#f59e0b',
                    transition: 'all 0.15s ease',
                  }}
                />
                <span
                  style={{
                    width: '3px',
                    height: isAudioSpeaking ? '14px' : isPlaying && !isPaused ? '8px' : '4px',
                    borderRadius: '2px',
                    background: isAudioSpeaking ? '#10b981' : '#f59e0b',
                    transition: 'all 0.15s ease',
                  }}
                />
              </div>

              <span
                style={{
                  fontSize: '10px',
                  fontFamily: "'JetBrains Mono', monospace",
                  fontWeight: 700,
                  padding: '2px 6px',
                  borderRadius: '4px',
                  background: '#18181b',
                  border: '1px solid #27272a',
                  color: '#f59e0b',
                }}
              >
                {activeChapter.timeRange}
              </span>

              <span
                style={{
                  fontSize: '9px',
                  fontFamily: "'JetBrains Mono', monospace",
                  fontWeight: 600,
                  padding: '2px 5px',
                  borderRadius: '3px',
                  background: isAudioSpeaking ? 'rgba(16, 185, 129, 0.15)' : '#18181b',
                  border: '1px solid #27272a',
                  color: isAudioSpeaking ? '#10b981' : '#71717a',
                }}
              >
                {isAudioSpeaking ? '● ON AIR (DIGITAL MIX)' : 'STANDBY'}
              </span>

              <span
                style={{
                  fontSize: '11px',
                  fontWeight: 600,
                  color: '#f4f4f5',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <span>{activeChapter.title}</span>
                {activeChapter.personaName && (
                  <span
                    style={{
                      fontSize: '9.5px',
                      fontFamily: "'JetBrains Mono', monospace",
                      color: '#38bdf8',
                      background: 'rgba(56, 189, 248, 0.12)',
                      padding: '1px 5px',
                      borderRadius: '3px',
                    }}
                  >
                    👤 {activeChapter.personaName}
                  </span>
                )}
              </span>
            </div>

            {/* View Switch Button */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
              <button
                onClick={() => onSetViewMode(viewMode === 'brag' ? 'console' : 'brag')}
                style={{
                  fontSize: '11px',
                  fontWeight: 600,
                  background: '#18181b',
                  border: '1px solid #27272a',
                  color: '#f4f4f5',
                  borderRadius: '4px',
                  padding: '3px 8px',
                  cursor: 'pointer',
                }}
              >
                {viewMode === 'brag' ? 'Switch to Console' : 'Switch to Architecture (/brag)'}
              </button>
            </div>
          </div>

          {/* High-Contrast Teleprompter Closed Caption */}
          <div
            style={{
              padding: '6px 12px',
              borderRadius: '6px',
              background: '#0d1117',
              border: '1px solid #21262d',
            }}
          >
            <p
              style={{
                fontSize: '13.5px',
                fontWeight: 500,
                color: '#f0f6fc',
                lineHeight: 1.45,
                margin: 0,
              }}
            >
              &ldquo;{currentSentence}&rdquo;
            </p>
          </div>

          {/* 5-Minute Overall Progress Bar */}
          <div
            style={{
              width: '100%',
              height: '3px',
              background: '#18181b',
              borderRadius: '2px',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                height: '100%',
                background: 'linear-gradient(90deg, #f59e0b 0%, #10b981 100%)',
                width: `${Math.min(100, (elapsedSeconds / 300) * 100)}%`,
                transition: 'width 0.3s ease',
              }}
            />
          </div>
        </div>
      </div>
    </>
  )
}
