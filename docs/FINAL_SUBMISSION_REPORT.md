# Asset Intelligence Copilot — Final Evaluation & Architecture Report

**Event:** FlytBase Asset Copilot Hack Day (Hacktoberfest 2026)  
**As of Date:** 15 Jan 2027 · **Fleet Scope:** 600 Wells (7 Areas, 4 Production Teams)  
**Live Submission Portal:** `hackathonplatform-production.up.railway.app`  

---

# Page 1: System Design, Architecture & Tools

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                       FLY T B A S E   C O P I L O T   A R C H I T E C T U R E               │
├─────────────────────────┬──────────────────────────┬─────────────────────────┬──────────────┤
│ 1. Immutable Raw Data   │ 2. Derived Domain Layer  │ 3. Append-Only Ledger   │ 4. Agent & UI│
│ • 600 Wells (assets)    │ • eff_inspection (delta) │ • ledger (event log)    │ • Gemma 4    │
│ • 125,198 Inspections   │ • well_now (real status) │ • Scoped overrides      │ • Tools      │
│ • 17,415 Maintenance    │ • spills (reportable)    │ • Private user memory   │ • Visuals    │
│ • FTS5 Chunks (SOPs)    │ • Zero LLM arithmetic    │ • Conflict detection    │ • React UI   │
└─────────────────────────┴──────────────────────────┴─────────────────────────┴──────────────┘
```

### 1. Core Mission & Architectural Principle
The system is built on one inviolable rule: **Deterministic Python and SQLite own the facts, an LLM agent owns the conversation, and an append-only ledger owns memory and feedback**.

- **Zero LLM Math:** The LLM never counts, sums, computes uptime percentages, or calculates date windows. Every number, dollar total, and date is computed with mathematical determinism.
- **Zero Hardcoded Magic Numbers:** All operational thresholds (e.g. T200 15 °C delta, T350 20 °C delta, T500 25 °C delta, 5 % pad spill shut-in, 5.0 bbl reportable spill threshold) are dynamically extracted from `fleet/well-types/*.md` and `fleet/sops/*.md` into `rules.yaml` with verifiable file and section citations.
- **Strict Citation Provenance Gate:** Every bracketed citation (`[INS-...]`, `[MNT-...]`, `[CTX-...]`, `[LEDGER-...]`, `[DOC:...]`) emitted in prose must exist in that turn's tool evidence set. Hallucinated IDs are stripped before display.
- **High-Speed Idempotent Ingest:** Ingests all 600 wells, 125,198 weekly inspections, 17,415 maintenance records, 4,437 repair reports, and FTS5 documents in **8.92 seconds** without making external API calls.

### 2. Multi-User Isolation & Scoped Feedback Ledger
- **Private Isolation:** Private memory (`recall_wells`, user preferences) strictly enforces `WHERE user_id = ?`. Queries by Jessica Reed (`U-202`) never leak sessions from Michael Turner (`U-201`), and Nathan Pierce's (`U-601`) preference for thousand-dollar formatting (`$k`) never alters another user's display.
- **Shared Knowledge:** Operational updates (`"WELL-0333 pump was replaced"`) are committed to the append-only `ledger` with `scope_type='well'`, instantly updating the active recall list for all users while preserving full audit provenance.
- **Bi-Temporal State Diff:** Separates raw historical sensor data (Layer 1) from runtime human corrections and rule overrides (Layer 2), allowing operators to view both the raw sensor and the effective corrected state simultaneously.

### 3. Generative UI Visual Contracts
The system outputs 8 distinct visual blocks rendered dynamically in a strict GitHub Primer Dark / Vercel Geist monochrome theme:
1. `status_card`: Well operational status, telemetry, temperature delta, and active repair notes.
2. `table`: Paginated tabular records with sortable columns and hyperlinked evidence tags.
3. `line_chart`: Time-series trends (temperature histories, pressure test curves).
4. `bar_chart`: Comparative breakdowns (waiting delay categories, repair counts).
5. `map_view`: Geographic pin layouts with status coloring and coordinate tooltips.
6. `heatmap`: Two-dimensional matrices (area × month downtime, spill frequencies).
7. `conflict`: Side-by-side reconciliation of disagreeing claims or data corrections.
8. `evidence`: Direct document snippets with section anchors and highlighted clauses.

---

# Page 2: Final Evaluation Outputs (Q1 to Q6)

### Q1. Reservoir Pressure (Michael Turner, U-201)
- **Question:** *"All our wells feed one reservoir. Map the reservoir pressure across the field from the pressure data."*
- **Reasoning & Domain Distinction:** The system identifies that downhole reservoir pore pressure (BHP) is not measured in wellhead inspection telemetry. The only pressure data in the system consists of surface flowline hydrostatic integrity tests (performed at 1.25× maximum operating pressure per SOP WS-05 `[DOC:field-work-sop.md#WS-05]`, ranging from 120 to 350 psi during line repairs) and wellhead pressure ratings (3,000 psi for WH-3000 per `[DOC:OM-T200#9.1]`).
- **Visual Emitted:** `map_view` rendering flowline test pressure pins across all wells.
- **Evidence:** `[DOC:OM-T200#9.1]`, `[DOC:field-work-sop.md#WS-05]`, `[MNT-0001-028]`, `[MNT-0002-031]`, etc.

### Q2. Best Producer in 2026 (Robert Hayes, U-301)
- **Question:** *"Which well produced the most oil in 2026?"*
- **Reasoning & Domain Reality:** Individual wellhead oil volume (bbl/day) is not metered in the database (Problem Statement §2: *"Is the well producing oil? Nobody writes this down. You can tell from temperature..."*). 256 wells achieved 100% operational uptime (52/52 or 53/53 producing weeks with zero downtime). Among equipment classes, T500 electric submersible pump (ESP) wells in Southeast Blocks 31 and 32 move significantly more fluid than rod-lift wells (`[DOC:OM-T500#1]`).
- **Visual Emitted:** `table` showing top producing wells by uptime weeks and average delta temperature:
  | Well | Type | Area | Producing Weeks (2026) | Uptime % | Avg Delta Temp | Max Delta | Evidence |
  | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
  | **WELL-0520** | T500 | SE-31 | 53 / 53 weeks | 100.0% | 34.2 °C | 42.1 °C | `[DOC:OM-T500#3]` |
  | **WELL-0545** | T500 | SE-32 | 53 / 53 weeks | 100.0% | 32.8 °C | 40.5 °C | `[DOC:OM-T500#3]` |
  | **WELL-0147** | T200 | NE-07 | 53 / 53 weeks | 100.0% | 31.4 °C | 38.6 °C | `[DOC:OM-T200#9.3]` |

### Q3. Gas Reports & Timeliness (Laura Simmons, U-401)
- **Question:** *"Since 1 Nov 2026, every time an operator note reports gas at a well, did we get someone out to that well in time under our operating procedures? List every report and whether the response met the deadline."*
- **Rule Applied:** OPS-1 (`[DOC:operations-sop-rev2.md#OPS-1]`). Response is a maintenance job (`started_at`) or manual inspection (`inspected_at` with `method='manual'`). Deadline: 24h before 1 Jan 2027; 12h from 1 Jan 2027.
- **Results:** 26 reports filed; **16 Met**, **10 Missed** (including WELL-0332 on 3 Dec where no response was ever dispatched).
- **Visual Emitted:** `table` with exact columns requested:
  | Well | Area | Reported at | Response | Hours to response | Deadline | Met / Missed |
  | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
  | WELL-0163 | NE-08 | 2026-11-03 20:55 | `[MNT-0163-019]` 2026-11-14 08:00 | 251.1h | 24 hours | **Missed** |
  | WELL-0149 | NE-07 | 2026-11-06 18:20 | `[MNT-0149-029]` 2026-11-07 08:00 | 13.7h | 24 hours | **Met** |
  | WELL-0165 | NE-08 | 2026-11-13 20:35 | `[MNT-0165-031]` 2026-11-14 08:00 | 11.4h | 24 hours | **Met** |
  | WELL-0341 | NW-12 | 2026-11-19 07:40 | `[INS-0341-0109]` 2026-12-17 13:30 | 677.8h | 24 hours | **Missed** |
  | WELL-0332 | NW-12 | 2026-12-03 12:10 | None | N/A | 24 hours | **Missed** |
  | WELL-0324 | NW-12 | 2027-01-01 22:40 | `[MNT-0324-036]` 2027-01-02 08:00 | 9.3h | 12 hours | **Met** |
  | WELL-0599 | SE-32 | 2027-01-06 17:20 | `[INS-0599-0196]` 2027-01-07 09:45 | 16.4h | 12 hours | **Missed** |

### Q4. Temporary Flowline Bypasses (Chris Dalton, U-402)
- **Question:** *"Across all areas, which temporary flowline bypasses are in place right now, and is each one allowed? Also list any bypass, past or present, that stayed in after its approval ran out or was never approved at all."*
- **Rule Applied:** OPS-2 (`[DOC:operations-sop-rev2.md#OPS-2]`). Allowed only if named in an unexpired MOC memo.
- **Visual Emitted:** `table` with exact columns requested:
  | Well | Area | Bypass in | Bypass out | Approval | Approval valid until | Status |
  | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
  | **WELL-0248** | SE-31 | 2026-11-05 | still in | `[DOC:moc-2026-044.md]` | 2027-02-28 | **Allowed** |
  | **WELL-0249** | SE-31 | 2026-11-25 | still in | `[DOC:moc-2026-036.md]` | 2026-12-15 | **Expired** |
  | **WELL-0405** | NW-12 | 2026-12-20 | still in | None | None | **Not approved** |
  | **WELL-0087** | SW-24 | 2026-12-02 | 2027-01-06 | `[DOC:moc-2026-036.md]` | 2026-12-15 | **Expired** |
  | **WELL-0158** | NE-08 | 2026-11-20 | 2026-12-28 | `[DOC:moc-2026-036.md]` | 2026-12-15 | **Expired** |
  | **WELL-0561** | SE-32 | 2026-12-08 | 2026-12-19 | None | None | **Not approved** |

### Q5. The Regulator's Letter (Michael Turner, U-201)
- **Question:** *"The State Oil & Gas Commission wrote to us in November 2026 about spills. Which of our spills does the letter cover, and on which ones are we not compliant? Show me a table."*
- **Rule Applied:** `[DOC:regulator-letter-2026-11-20.md]` covers reportable spills (>= 5.0 bbl per `[DOC:spill-response-sop.md#SR-01]`) in NE-07 and NE-08 since 1 Jun 2026. HSE note specifies clean-up reports must state *"Soil samples sent to the lab."*
- **Visual Emitted:** `table` with exact columns requested:
  | Well | Area | Inspection | Volume (bbl) | Clean-up job | Compliant? |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | **WELL-0168** | NE-08 | `[INS-0168-0190]` (2026-06-11) | 5.6 bbl | `[MNT-0168-024]` | **Yes** (Soil samples sent to lab) |
  | **WELL-0123** | NE-07 | `[INS-0123-0093]` (2026-09-24) | 6.0 bbl | `[MNT-0123-014]` | **No** (Field readings only; no lab samples sent) |
  | **WELL-0277** | NE-07 | `[INS-0277-0205]` (2026-10-01) | 6.2 bbl | `[MNT-0277-031]` | **Yes** (Soil samples sent to lab) |
  | **WELL-0119** | NE-07 | `[INS-0119-0209]` (2026-11-05) | 6.0 bbl | `[MNT-0119-029]` | **Yes** (Soil samples sent to lab) |
  | **WELL-0182** | NE-08 | `[INS-0182-0208]` (2026-12-03) | 5.2 bbl | `[MNT-0182-028]` | **No** (No laboratory soil results recorded) |
  | **WELL-0262** | NE-08 | `[INS-0262-0218]` (2027-01-07) | 6.1 bbl | `[MNT-0262-029]` | **No** (No laboratory soil results recorded) |

### Q6. Which Status is Right? (Nathan Pierce, U-601)
- **Question:** *"Across the whole field, not just my area, for which wells do the latest inspection and the operator notes disagree about whether the well is producing oil? For each one, what is its real status right now, and why?"*
- **Rule Applied:** OPS-3 (`[DOC:operations-sop-rev2.md#OPS-3]`). Most recent evidence governs. Newer shut-in note = Not producing (shut in). Newer restart note = Producing (unconfirmed).
- **Visual Emitted:** `table` with exact columns requested:
  | Well | Area | Latest inspection | Latest operator note | Status now |
  | :--- | :--- | :--- | :--- | :--- |
  | **WELL-0071** | SW-24 | `[INS-0071-0220]` 2027-01-14: Producing (delta 18.2 °C) | `[CTX-0071-004]` 2027-01-14 16:30: "Shut in WELL-0071 for belt repair" | **Not producing oil (shut in)** — Note post-dates inspection |
  | **WELL-0284** | SW-24 | `[INS-0284-0220]` 2027-01-14: Producing (delta 19.5 °C) | `[CTX-0284-004]` 2027-01-14 17:15: "Shut in WELL-0284 for valve work" | **Not producing oil (shut in)** — Note post-dates inspection |
  | **WELL-0422** | NW-12 | `[INS-0422-0220]` 2027-01-14: Producing (delta 21.0 °C) | `[CTX-0422-004]` 2027-01-14 18:00: "Shut in for separator high pressure" | **Not producing oil (shut in)** — Note post-dates inspection |
  | **WELL-0481** | SE-32 | `[INS-0481-0220]` 2027-01-14: Producing (delta 22.4 °C) | `[CTX-0481-004]` 2027-01-14 18:30: "Shut in for separator high pressure" | **Not producing oil (shut in)** — Note post-dates inspection |

---

# Page 3: Final Evaluation Outputs (Q7 to Q11)

### Q7. What the Operators Are Hearing (Robert Hayes, U-301)
- **Turn 1 (Ranking Table):** Operators recorded rod squeal/knocking notes on wells that have received no corrective repair since. Ranked by 12-month corrective repair frequency and thermal stress:
  | Rank | Well | Area | Operator-note evidence | Other warning signs in data | Last repair on the well |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | **1** | **WELL-0297** | NE-07 | `[CTX-0297-004]` (2027-01-11): *"Rod squeal at stuffing box, greased rod"* | 6 corrective repairs in 12m (chronic); temp delta 26.5 °C | `[MNT-0297-036]` (2027-01-08, Prime mover failure) |
  | **2** | **WELL-0062** | SW-24 | `[CTX-0062-006]` (2026-12-30): *"Rod squeal at stuffing box, greased rod"* | 4 corrective repairs in 12m; temp delta 21.3 °C | `[MNT-0062-031]` (2026-12-25, Flowline leak) |
  | **3** | **WELL-0005** | SW-23 | `[CTX-0005-006]` (2027-01-08): *"Rod squeal at stuffing box, greased rod"* | T350 deep well; 4 corrective repairs in 12m | `[MNT-0005-035]` (2026-12-14, Scheduled lube) |
  | **4** | **WELL-0089** | SW-24 | `[CTX-0089-001]` (2027-01-12): *"Rod squeal at stuffing box, greased rod"* | 4 corrective repairs in 12m; temp delta 32.7 °C | `[MNT-0089-033]` (2027-01-01, Flowline leak) |
  | **5** | **WELL-0260** | SW-24 | `[CTX-0260-005]` (2027-01-06): *"Rod squeal at stuffing box, greased rod"* | 4 corrective repairs in 12m; temp delta 36.1 °C | `[MNT-0260-037]` (2026-12-04, Flowline leak) |
- **Turn 2 (Top 3 Crew Recommendation):** Send crews first to **WELL-0297** (fleet-leading 6 corrective jobs, recent prime mover breakdown Jan 8, imminent rod parting), **WELL-0062** (4 repairs, recent spill), and **WELL-0005** (high-load T350 deep well).

### Q8. Who Told You That? (4 Sessions, 5 Turns)
- **Turn 1 (Nathan Pierce):** Nathan states WELL-0333 pump was swapped. Recorded in append-only ledger `[LEDGER-...]`, scoping `scope_type='well'`, immediately removing it from the active recall list.
- **Turn 2 (Nathan Pierce):** Nathan sets private preferences (sort by Area/Well, costs in $k). Saved to private user profile `[LEDGER-...]` with strict isolation.
- **Turn 3 (Robert Hayes):** Robert queries active recalled pumps in ground. Recalls 11 pumps (correctly excluding Nathan's WELL-0333 update, citing Supplier Notice `[DOC:supplier-recall-notice-2026-12-01.md]` and maintenance reports).
- **Turn 4 (Olivia Grant):** Olivia states Nathan told her WELL-0577 was swapped. Recorded in ledger `[LEDGER-...]`, taking WELL-0577 off the recall list.
- **Turn 5 (Nathan Pierce):** Nathan asks for recalled pumps in his area (NW-12) and costs. System returns 6 remaining pumps in NW-12 (`WELL-0305, WELL-0340, WELL-0398, WELL-0426, WELL-0427, WELL-0428`), formatted in thousands ($k) per his private Turn 2 preference:
  | Well | Area | Pump Model & Lot | Installed On Job | Installation Cost | Provenance |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | WELL-0305 | NW-12 | Highline RP-175 (LOT-2409-A) | `[MNT-0305-032]` (2026-10-21) | **$24.5k** | MNT-0305-032, Recall Notice |
  | WELL-0340 | NW-12 | Highline RP-175 (LOT-2409-A) | `[MNT-0340-031]` (2026-04-15) | **$34.3k** | MNT-0340-031, Recall Notice |
  | WELL-0398 | NW-12 | Highline RP-175 (LOT-2409-C) | `[MNT-0398-018]` (2026-03-31) | **$19.7k** | MNT-0398-018, Recall Notice |
  | WELL-0426 | NW-12 | Highline RP-175 (LOT-2409-C) | `[MNT-0426-030]` (2026-06-24) | **$24.0k** | MNT-0426-030, Recall Notice |
  | WELL-0427 | NW-12 | Highline RP-175 (LOT-2409-C) | `[MNT-0427-020]` (2026-02-18) | **$30.1k** | MNT-0427-020, Recall Notice |
  | WELL-0428 | NW-12 | Highline RP-175 (LOT-2410-B) | `[MNT-0428-022]` (2026-03-17) | **$27.1k** | MNT-0428-022, Recall Notice |

### Q9. One Conversation, Several Topics (Robert Hayes, U-301)
1. **Recalled pumps count:** **10 pumps** remaining in the ground across 4 areas: 6 in NW-12, 2 in NE-08, 1 in SW-23, and 1 in SE-32 (`[DOC:supplier-recall-notice-2026-12-01.md]`, ledger updates).
2. **Northwest Production Lead & Wells:** Led by **Nathan Pierce** (User ID: `U-601`, production supervisor); runs **150 wells** (`WELL-0301` to `WELL-0450` in NW-12 per `[DOC:users.json#U-601]`).
3. **Cold Weather SOP & Missed Check:** Under OPS-5 (`[DOC:operations-sop-rev2.md#OPS-5]`), producing wells with ambient temp <= −5.0 °C require a heat trace check within 7 days. **WELL-0310** missed this check in December (ambient −6.0 °C on 17 Dec `[INS-0310-0213]`, no check within 7 days).
4. **Gas smell at WELL-0332 on 3 Dec:** Operator note `[CTX-0332-004]` reported a gas odor at 12:10 UTC. **No H2S reading was ever taken or recorded** because no field response was ever dispatched, in direct violation of OPS-1 (`[DOC:operations-sop-rev2.md#OPS-1]`).
5. **Recalled pumps producing status:** Exactly **one well is not producing oil right now**: **WELL-0160** in NE-08 (latest inspection `[INS-0160-0220]` on 14 Jan 2027 shows wellhead 11.2 °C, delta 3.8 °C < 15.0 °C threshold `[DOC:OM-T200#9.3]`; last repaired `[MNT-0160-032]` on 15 Jan 2027). The other 9 wells are actively producing oil.
6. **Triage Priority:** Deal with **WELL-0332** first as an acute safety hazard (unverified gas odor with no H2S reading for over a month). Second priority is **WELL-0160** (already shut in and past the 31 Dec recall replacement deadline, allowing pump replacement with zero incremental lost production).

### Q10. What Are We Waiting On? (Michael Turner, U-201)
- **Question:** *"When a well stays shut in longer than the repair itself, what are we usually waiting on: parts, crews, contractors or weather? Break it down by area for jobs started in 2026, with the typical number of extra days, and tell me if any area stands out."*
- **Empirical Findings:** Across the field, **waiting on crews** is the most frequent delay (50.0% to 85.7% of delay events, typically adding 7.0 extra days). However, **Southeast Block 32 (SE-32)** stands out dramatically: parts delays average **28.0 extra days** (4 full weeks)—over double any other area in the field.
- **Visual Emitted:** `table` and stacked `bar_chart` by area:
  | Area | Primary Reason | Share (%) | Typical Extra Days | Notable Delay Pattern |
  | :--- | :--- | :--- | :--- | :--- |
  | **SE-32** | Crews (60.0%) / Parts (20.0%) | 20.0% parts | **28.0 days (parts)** | **Severe vendor supply chain bottleneck** |
  | **NW-12** | Crews (74.2%) / Weather (25.8%) | 74.2% crews | 7.0 days | Crew dispatch backlog & winter freezes |
  | **NE-07** | Crews (78.9%) / Weather (21.1%) | 78.9% crews | 7.0 days | Standard 1-week crew scheduling delay |
  | **SE-31** | Crews (50.0%) / Weather (35.7%) | 35.7% weather| 7.0 days | High weather delays during cold snaps |

### Q11. Hotter Wells (Olivia Grant, U-501)
- **Question:** *"Which region of the field consistently runs hotter?"*
- **Empirical Findings:** The **Southeast region** consistently runs significantly hotter than all other areas across 125,198 historical inspections. **Southeast Block 31 (SE-31)** runs the hottest overall with an average wellhead temperature of **52.8 °C** and an average delta of **31.4 °C** above ambient air temperature, followed by **Southeast Block 32 (SE-32)** at **50.8 °C** (delta **29.2 °C**). In contrast, Northwest Block 12 (50.1 °C), Northeast (48.3–48.8 °C), and Southwest (47.7–48.6 °C) run noticeably cooler. The Southeast's thermal elevation is driven by deeper production horizons and high-rate T500 electric submersible pumps.
- **Visual Emitted:** `table` ranking all 7 field blocks by historical average wellhead temperature and ambient delta.
