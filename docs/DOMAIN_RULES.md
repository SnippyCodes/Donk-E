# DOMAIN_RULES.md — Oil Field Domain Rules & Protocols

## 1. Well Production & Downtime
- **Production Determination:** A well is producing oil if and only if:
  `wellhead_temp_c - ambient_temp_c >= production_temp_delta`
  - For `T200`: `production_temp_delta = 15.0 °C` (OM-T200 §9.3)
  - For `T350`: `production_temp_delta = 20.0 °C` (OM-T350 §3)
- **Absolute Temperature Fallacy:** Never judge production status from absolute wellhead temperature. Solar heating on hot summer days can raise idle wellhead steel above 45°C.
- **Downtime Calculation:**
  - Inspections occur weekly.
  - Every weekly inspection where `is_producing = False` represents **7 days of downtime**.
  - Consecutive non-producing inspections accumulate multiples of 7 days (e.g. 3 inspections = 21 days).
  - Missed inspections add 0 days.
  - Do NOT use `maintenance.downtime_hours` for field downtime; that represents work duration on a single repair.

## 2. Spill Classification & Deadlines (SOP-SR)
- **Spill Classes:**
  - Minor: `< 1.0 bbl` (record and clean up; no external report).
  - Moderate: `1.0 <= vol < 5.0 bbl` (record, clean up, notify HSE within 72h).
  - Reportable: `5.0 <= vol < 25.0 bbl` (SR-01 applies).
  - Major: `>= 25.0 bbl` (SR-01 2-hour report, incident command).
- **SR-01 (Reporting):**
  - Written report filed with State Oil & Gas Commission within **24 hours** of discovery for reportable spills (or **2 hours** for major).
  - Late filing results in Notice of Violation (NOV) and fine ($2,500 - $7,500).
- **SR-02 (Containment):**
  - Source stopped and release contained within **4 hours** of discovery.
- **SR-03 (Remediation & Verification):**
  - Clean to `<= 1.0% TPH`.
  - Take at least 4 soil samples.
  - For reportable spills, agency verification site inspection required within **60 days** of discovery. Closed only by passing inspection.
- **SR-04 (Recording):**
  - Every spill recorded against asset with volume and pad area %.
- **False Positives:**
  - Detections corrected as water/mud via human context notes (`note_type == 'correction'`) do not count as spills for statistics or compliance.

## 3. Regulatory Compliance (SOP-RC)
- **RC-01:** Every well inspected at least once every 14 days.
- **RC-02:** Every flowline must pass an integrity test once per calendar year (`maintenance.issue == 'Annual flowline integrity test'`).
- **RC-03:** Downtime > 14 consecutive days reported to area supervisor.
- **RC-04:** Agency Notice of Violation answered within **30 days** (`nov_response_filed`).
- **RC-05:** Flowline maintenance program kept.

## 4. Maintenance Escalation & Safety (OM-T200 §10, SOP-WS)
- **RCA Requirement:** 3 or more corrective repairs on the same equipment kind on a well within the preceding 12 months requires a Root-Cause Analysis before the next repair is closed.
- **Spill Shut-in:** Spills covering `> 5%` of pad area require immediate well shut-in.
- **Planned Shut-in:** Planned shut-in must be recorded in the maintenance system before work begins (OM-T200 §4).
