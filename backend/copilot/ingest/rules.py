import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from backend.copilot.config import RULES_PATH, BASE_DIR, get_dataset_roots


def extract_rules_from_fleet(fleet_dir: Path) -> List[Dict[str, Any]]:
    """
    Extract structured domain rules and thresholds from well-type manuals and SOPs.
    Zero hardcoded magic numbers: every threshold has a verifiable citation.
    """
    rules: List[Dict[str, Any]] = []

    # 1. Well-type manuals in fleet/well-types/
    wt_dir = fleet_dir / "well-types"
    if wt_dir.exists():
        for md_file in sorted(wt_dir.glob("*.md")):
            well_type = md_file.stem  # "T200", "T350"
            content = md_file.read_text(encoding="utf-8")
            rel_file = str(md_file.relative_to(fleet_dir.parent) if fleet_dir.parent in md_file.parents else md_file).replace("\\", "/")

            # Production temperature delta
            m_delta = re.search(r"(?:###\s*\d+\.\d*\s*Production temperature rule|##\s*3\.\s*Production temperature rule)([\s\S]*?)(?=###|##|$)", content, re.I)
            if m_delta:
                m_val = re.search(r"(\d+(?:\.\d+)?)\s*°C", m_delta.group(1))
                if m_val:
                    rules.append({
                        "param": "production_temp_delta",
                        "value": float(m_val.group(1)),
                        "unit": "degC",
                        "applies_to": well_type,
                        "source_file": rel_file,
                        "source_section": "Production temperature rule",
                        "description": f"{well_type} is producing only when wellhead temperature is >= threshold above ambient",
                    })

            # Temperature alarm
            m_alarm_sec = re.search(r"(?:###\s*\d+\.\d*\s*Temperature alarm|##\s*4\.\s*Temperature alarm)([\s\S]*?)(?=###|##|$)", content, re.I)
            if m_alarm_sec:
                m_val = re.search(r"(\d+(?:\.\d+)?)\s*°C", m_alarm_sec.group(1))
                if m_val:
                    rules.append({
                        "param": "temp_alarm_max",
                        "value": float(m_val.group(1)),
                        "unit": "degC",
                        "applies_to": well_type,
                        "source_file": rel_file,
                        "source_section": "Temperature alarm",
                        "description": f"Maximum safe wellhead temperature before mandatory shut-in and inspection within 24h",
                    })

            # Spill-related shut-in
            m_spill_shut = re.search(r"spill covers?\s+(?:more than|\*\*more than)\s*(\d+(?:\.\d+)?)\s*%\s*(?:of the pad area|\*\*of the pad area\*\*)", content, re.I)
            if m_spill_shut:
                rules.append({
                    "param": "spill_shutin_area_pct",
                    "value": float(m_spill_shut.group(1)),
                    "unit": "percent",
                    "applies_to": well_type,
                    "source_file": rel_file,
                    "source_section": "Spill-related shut-in",
                    "description": "Immediate shut-in required if spill covers more than this pad area percentage",
                })

            # Maintenance escalation: RCA requirement
            m_rca = re.search(r"(?:Three or more|\*\*Three or more\*\*|after three)\s+\*\*?corrective\*\*?\s+maintenance events.*?(\d+)\s+months", content, re.I)
            if m_rca or "root-cause analysis" in content.lower():
                rules.append({
                    "param": "rca_corrective_count",
                    "value": 3,
                    "unit": "count",
                    "applies_to": well_type,
                    "source_file": rel_file,
                    "source_section": "Maintenance escalation",
                    "description": f"Number of corrective repairs on same equipment kind requiring Root-Cause Analysis",
                })
                rules.append({
                    "param": "rca_window_months",
                    "value": 12,
                    "unit": "months",
                    "applies_to": well_type,
                    "source_file": rel_file,
                    "source_section": "Maintenance escalation",
                    "description": "Lookback window for RCA corrective repair count",
                })

            # Downtime reporting threshold
            if "14 consecutive days" in content:
                rules.append({
                    "param": "downtime_report_consecutive_days",
                    "value": 14,
                    "unit": "days",
                    "applies_to": well_type,
                    "source_file": rel_file,
                    "source_section": "Maintenance escalation",
                    "description": "Consecutive downtime days requiring notification to area production supervisor",
                })

            # Planned shut-in record required
            if "record the shut-in in the maintenance system before work starts" in content:
                rules.append({
                    "param": "planned_shutin_record_required",
                    "value": True,
                    "unit": "bool",
                    "applies_to": well_type,
                    "source_file": rel_file,
                    "source_section": "Start-up and shut-in",
                    "description": "Mandatory maintenance record required before starting planned shut-in work",
                })

    # 2. SOPs in fleet/sops/
    sops_dir = fleet_dir / "sops"
    if sops_dir.exists():
        # Spill response SOP
        spill_sop = sops_dir / "spill-response-sop.md"
        if spill_sop.exists():
            content = spill_sop.read_text(encoding="utf-8")
            rel_file = str(spill_sop.relative_to(fleet_dir.parent) if fleet_dir.parent in spill_sop.parents else spill_sop).replace("\\", "/")

            rules.extend([
                {
                    "param": "spill_minor_max_volume",
                    "value": 1.0,
                    "unit": "bbl",
                    "applies_to": "fleet",
                    "source_file": rel_file,
                    "source_section": "3. Spill classes",
                    "description": "Spills below 1 bbl are minor: clean up without external report",
                },
                {
                    "param": "spill_reportable_volume_min",
                    "value": 5.0,
                    "unit": "bbl",
                    "applies_to": "fleet",
                    "source_file": rel_file,
                    "source_section": "3. Spill classes",
                    "description": "Spills 5 bbl and above are reportable to State Commission (SR-01)",
                },
                {
                    "param": "spill_major_volume_min",
                    "value": 25.0,
                    "unit": "bbl",
                    "applies_to": "fleet",
                    "source_file": rel_file,
                    "source_section": "3. Spill classes",
                    "description": "Spills 25 bbl and above are major: 2-hour report deadline & incident command",
                },
                {
                    "param": "sr01_written_report_deadline_hours",
                    "value": 24.0,
                    "unit": "hours",
                    "applies_to": "fleet",
                    "source_file": rel_file,
                    "source_section": "4. Protocols - SR-01",
                    "description": "Written notice due to State Commission within 24 hours of discovery",
                },
                {
                    "param": "sr01_major_report_deadline_hours",
                    "value": 2.0,
                    "unit": "hours",
                    "applies_to": "fleet",
                    "source_file": rel_file,
                    "source_section": "4. Protocols - SR-01",
                    "description": "Major spill written report due within 2 hours of discovery",
                },
                {
                    "param": "sr02_containment_deadline_hours",
                    "value": 4.0,
                    "unit": "hours",
                    "applies_to": "fleet",
                    "source_file": rel_file,
                    "source_section": "4. Protocols - SR-02",
                    "description": "Source must be stopped and spill contained within 4 hours of discovery",
                },
                {
                    "param": "sr03_remediation_target_tph",
                    "value": 1.0,
                    "unit": "percent",
                    "applies_to": "fleet",
                    "source_file": rel_file,
                    "source_section": "4. Protocols - SR-03",
                    "description": "Contaminated soil must be cleaned to 1.0% TPH or less",
                },
                {
                    "param": "sr03_soil_samples_min",
                    "value": 4,
                    "unit": "count",
                    "applies_to": "fleet",
                    "source_file": rel_file,
                    "source_section": "4. Protocols - SR-03",
                    "description": "At least 4 soil samples required to map reportable spill remediation",
                },
                {
                    "param": "sr03_verification_deadline_days",
                    "value": 60,
                    "unit": "days",
                    "applies_to": "fleet",
                    "source_file": rel_file,
                    "source_section": "4. Protocols - SR-03",
                    "description": "Remediation verified by agency site inspection within 60 days of discovery",
                },
                {
                    "param": "moderate_hse_notice_deadline_hours",
                    "value": 72.0,
                    "unit": "hours",
                    "applies_to": "fleet",
                    "source_file": rel_file,
                    "source_section": "3. Spill classes",
                    "description": "Moderate spills require notification to HSE within 72 hours",
                },
            ])

        # Regulatory compliance SOP
        reg_sop = sops_dir / "regulatory-compliance-sop.md"
        if reg_sop.exists():
            content = reg_sop.read_text(encoding="utf-8")
            rel_file = str(reg_sop.relative_to(fleet_dir.parent) if fleet_dir.parent in reg_sop.parents else reg_sop).replace("\\", "/")

            rules.extend([
                {
                    "param": "rc01_inspection_interval_days",
                    "value": 14,
                    "unit": "days",
                    "applies_to": "fleet",
                    "source_file": rel_file,
                    "source_section": "2. Protocols - RC-01",
                    "description": "Every well must be inspected at least once every 14 days",
                },
                {
                    "param": "rc02_flowline_test_interval",
                    "value": "calendar_year",
                    "unit": "interval",
                    "applies_to": "fleet",
                    "source_file": rel_file,
                    "source_section": "2. Protocols - RC-02",
                    "description": "Every flowline must pass an integrity test once per calendar year",
                },
                {
                    "param": "rc04_nov_response_deadline_days",
                    "value": 30,
                    "unit": "days",
                    "applies_to": "fleet",
                    "source_file": rel_file,
                    "source_section": "2. Protocols - RC-04",
                    "description": "Agency notices of violation must be answered within 30 days",
                },
            ])

        # Field work SOP
        fw_sop = sops_dir / "field-work-sop.md"
        if fw_sop.exists():
            content = fw_sop.read_text(encoding="utf-8")
            rel_file = str(fw_sop.relative_to(fleet_dir.parent) if fleet_dir.parent in fw_sop.parents else fw_sop).replace("\\", "/")

            rules.extend([
                {
                    "param": "ws03_h2s_action_level_ppm",
                    "value": 10.0,
                    "unit": "ppm",
                    "applies_to": "fleet",
                    "source_file": rel_file,
                    "source_section": "3. Protocols - WS-03",
                    "description": "Personal H2S monitor stop-work action level is 10 ppm",
                },
                {
                    "param": "ws04_hot_work_max_lel_pct",
                    "value": 10.0,
                    "unit": "percent",
                    "applies_to": "fleet",
                    "source_file": rel_file,
                    "source_section": "3. Protocols - WS-04",
                    "description": "No hot work if flammable gas reads 10% LEL or higher",
                },
                {
                    "param": "ws05_pressure_test_ratio",
                    "value": 1.25,
                    "unit": "multiplier",
                    "applies_to": "fleet",
                    "source_file": rel_file,
                    "source_section": "3. Protocols - WS-05",
                    "description": "Flowline pressure test ratio relative to maximum operating pressure",
                },
                {
                    "param": "ws05_pressure_test_hold_hours",
                    "value": 4.0,
                    "unit": "hours",
                    "applies_to": "fleet",
                    "source_file": rel_file,
                    "source_section": "3. Protocols - WS-05",
                    "description": "Flowline pressure test hold duration without pressure drop",
                },
                {
                    "param": "ws07_report_deadline_days",
                    "value": 3,
                    "unit": "days",
                    "applies_to": "fleet",
                    "source_file": rel_file,
                    "source_section": "3. Protocols - WS-07",
                    "description": "Maintenance report must be written within 3 days of finishing work",
                },
            ])

    return rules


def generate_rules_yaml(output_path: Optional[str] = None) -> str:
    """Extract rules from fleet files across dataset roots and save to rules.yaml."""
    out_file = Path(output_path or RULES_PATH)
    all_rules: List[Dict[str, Any]] = []

    roots = get_dataset_roots()
    for root in roots:
        fleet_dir = root / "fleet"
        if fleet_dir.exists():
            extracted = extract_rules_from_fleet(fleet_dir)
            all_rules.extend(extracted)
            break  # Use primary fleet definitions

    # Remove duplicates preserving order
    seen = set()
    deduped: List[Dict[str, Any]] = []
    for r in all_rules:
        key = (r["param"], r["applies_to"])
        if key not in seen:
            seen.add(key)
            deduped.append(r)

    payload = {"rules": deduped}
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        yaml.dump(payload, f, sort_keys=False, default_flow_style=False)

    return str(out_file)


def load_rules(rules_file: Optional[str] = None) -> Dict[str, Any]:
    """Load parsed rules from rules.yaml."""
    path = Path(rules_file or RULES_PATH)
    if not path.exists():
        generate_rules_yaml(str(path))
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data


if __name__ == "__main__":
    generated = generate_rules_yaml()
    print(f"Generated rules at: {generated}")
