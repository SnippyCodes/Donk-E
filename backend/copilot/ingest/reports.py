import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


class ReportParser:
    """Fast, regex-based parser extracting structured facts from free-text maintenance reports."""

    RE_MNT_ID = re.compile(r"#\s*Maintenance Report\s*[\u2014\u2013\-]\s*(MNT-[\w\-]+)", re.I)
    RE_ASSET_ID = re.compile(r"\*\*Asset:\*\*\s*(WELL-\d+)", re.I)
    RE_EQUIPMENT = re.compile(r"\*\*Equipment:\*\*\s*([^\n\*]+)", re.I)
    RE_WORK_STARTED = re.compile(r"\*\*Work started:\*\*\s*([^·\n]+)", re.I)
    RE_WORK_FINISHED = re.compile(r"\*\*Finished:\*\*\s*([^·\n]+)", re.I)
    RE_STOPPED_HOURS = re.compile(r"\*\*Well stopped for this job:\*\*\s*(\d+(?:\.\d+)?)\s*hours", re.I)
    RE_CREW_LEAD = re.compile(r"\*\*Crew lead:\*\*\s*([^(·\n]+)(?:\(([^)]+)\))?", re.I)
    RE_CONTRACTOR = re.compile(r"\*\*Contractor:\*\*\s*([^\n\*]+)", re.I)
    RE_TRIGGERED_BY = re.compile(r"\*\*Triggered by:\*\*\s*(?:inspection\s*)?(INS-[\w\-]+)", re.I)
    RE_REPORT_WRITTEN = re.compile(r"\*\*Report written:\*\*\s*([^\n\*]+)", re.I)

    RE_CONTAINED = re.compile(r"contained\s+(?:about\s+|after\s+about\s+|after\s+)?([\d\.]+)\s*hours", re.I)
    RE_SPILL_VOL = re.compile(r"estimated\s+([\d\.]+)\s*bbl", re.I)
    RE_SPILL_PAD_PCT = re.compile(r"([\d\.]+)%\s*of the pad", re.I)

    RE_PRESSURE_TEST = re.compile(r"Pressure-tested.*?at\s*(\d+)\s*psi", re.I)
    RE_PRESSURE_MOP = re.compile(r"maximum operating pressure of\s*(\d+)\s*psi", re.I)
    RE_PRESSURE_HOURS = re.compile(r"held (?:it )?for\s*(\d+(?:\.\d+)?)\s*hours", re.I)

    RE_H2S = re.compile(r"highest reading\s*(\d+(?:\.\d+)?)\s*ppm", re.I)
    RE_WASTE_VOL = re.compile(r"About\s*([\d\.]+)\s*m³.*?excavated", re.I)
    RE_WASTE_MANIFEST = re.compile(r"waste manifest\s*(WM-[\w\-]+)", re.I)
    RE_SOIL_SAMPLES = re.compile(r"(\d+)\s*soil samples taken", re.I)
    RE_SOIL_TPH = re.compile(r"highest result after clean-up was\s*([\d\.]+)%\s*TPH", re.I)

    RE_COMPLIANCE_TABLE = re.compile(
        r"##\s*Compliance check\s*\n\s*\|[^\n]+\|\s*\n\s*\|[-|\s]+\|\s*\n((?:\|[^\n]+\|\s*\n)+)",
        re.I
    )

    @classmethod
    def parse_report_text(cls, text: str, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Parse raw markdown report into structured facts dict."""
        m_id_match = cls.RE_MNT_ID.search(text)
        if m_id_match:
            mnt_id = m_id_match.group(1).strip()
        elif file_path:
            # Fallback to filename pattern MNT-XXXX-YYY
            p_match = re.search(r"(MNT-\d+-\d+)", Path(file_path).stem, re.I)
            mnt_id = p_match.group(1).upper() if p_match else Path(file_path).stem
        else:
            mnt_id = "UNKNOWN"

        asset_match = cls.RE_ASSET_ID.search(text)
        asset_id = asset_match.group(1).strip() if asset_match else None

        equip_match = cls.RE_EQUIPMENT.search(text)
        equipment = equip_match.group(1).strip() if equip_match else None

        started_match = cls.RE_WORK_STARTED.search(text)
        work_started = started_match.group(1).strip() if started_match else None

        finished_match = cls.RE_WORK_FINISHED.search(text)
        work_finished = finished_match.group(1).strip() if finished_match else None

        stopped_match = cls.RE_STOPPED_HOURS.search(text)
        well_stopped_hours = float(stopped_match.group(1)) if stopped_match else None

        crew_match = cls.RE_CREW_LEAD.search(text)
        crew_lead_name = crew_match.group(1).strip() if crew_match else None
        crew_lead_user_id = crew_match.group(2).strip() if crew_match and crew_match.group(2) else None

        contractor_match = cls.RE_CONTRACTOR.search(text)
        contractor = contractor_match.group(1).strip() if contractor_match else None

        triggered_match = cls.RE_TRIGGERED_BY.search(text)
        triggered_by = triggered_match.group(1).strip() if triggered_match else None

        written_match = cls.RE_REPORT_WRITTEN.search(text)
        report_written = written_match.group(1).strip() if written_match else None

        # Containment hours
        contained_hours: Optional[float] = None
        cont_match = cls.RE_CONTAINED.search(text)
        if cont_match:
            try:
                contained_hours = float(cont_match.group(1))
            except ValueError:
                pass

        # Spill facts
        spill_vol_match = cls.RE_SPILL_VOL.search(text)
        spill_volume_bbl = float(spill_vol_match.group(1)) if spill_vol_match else None

        spill_pad_match = cls.RE_SPILL_PAD_PCT.search(text)
        spill_pad_pct = float(spill_pad_match.group(1)) if spill_pad_match else None

        # Engineering and safety facts
        pt_match = cls.RE_PRESSURE_TEST.search(text)
        pressure_test_psi = int(pt_match.group(1)) if pt_match else None

        pt_mop_match = cls.RE_PRESSURE_MOP.search(text)
        pressure_test_mop_psi = int(pt_mop_match.group(1)) if pt_mop_match else None

        pt_hrs_match = cls.RE_PRESSURE_HOURS.search(text)
        pressure_test_hours = float(pt_hrs_match.group(1)) if pt_hrs_match else None

        h2s_match = cls.RE_H2S.search(text)
        h2s_ppm = float(h2s_match.group(1)) if h2s_match else None

        waste_vol_match = cls.RE_WASTE_VOL.search(text)
        waste_volume_m3 = float(waste_vol_match.group(1)) if waste_vol_match else None

        wm_match = cls.RE_WASTE_MANIFEST.search(text)
        waste_manifest_id = wm_match.group(1).strip() if wm_match else None

        ss_match = cls.RE_SOIL_SAMPLES.search(text)
        soil_samples = int(ss_match.group(1)) if ss_match else None

        tph_match = cls.RE_SOIL_TPH.search(text)
        soil_tph_pct = float(tph_match.group(1)) if tph_match else None

        # Compliance table parsing
        protocols_checked: List[Dict[str, str]] = []
        action_required_items: List[str] = []
        table_match = cls.RE_COMPLIANCE_TABLE.search(text)
        if table_match:
            table_lines = table_match.group(1).strip().split("\n")
            for line in table_lines:
                parts = [p.strip() for p in line.strip("|").split("|")]
                if len(parts) >= 3:
                    proto, result, detail = parts[0], parts[1], parts[2]
                    # Clean markdown bolding
                    clean_res = result.replace("*", "").strip()
                    protocols_checked.append({
                        "protocol": proto,
                        "result": clean_res,
                        "detail": detail,
                    })
                    if "action required" in clean_res.lower() or "not met" in clean_res.lower():
                        action_required_items.append(f"{proto}: {detail}")
                    # If containment hours wasn't matched from text, try from SR-02 row
                    if proto == "SR-02" and contained_hours is None:
                        m_c = re.search(r"([\d\.]+)\s*hours", detail, re.I)
                        if m_c:
                            contained_hours = float(m_c.group(1))

        return {
            "maintenance_id": mnt_id,
            "asset_id": asset_id,
            "report_file": file_path,
            "equipment": equipment,
            "work_started": work_started,
            "work_finished": work_finished,
            "well_stopped_hours": well_stopped_hours,
            "crew_lead_name": crew_lead_name,
            "crew_lead_user_id": crew_lead_user_id,
            "contractor": contractor,
            "triggered_by_inspection_id": triggered_by,
            "report_written": report_written,
            "contained_hours": contained_hours,
            "spill_volume_bbl": spill_volume_bbl,
            "spill_area_pct": spill_pad_pct,
            "pressure_test_psi": pressure_test_psi,
            "pressure_test_mop_psi": pressure_test_mop_psi,
            "pressure_test_hours": pressure_test_hours,
            "h2s_ppm": h2s_ppm,
            "waste_volume_m3": waste_volume_m3,
            "waste_manifest_id": waste_manifest_id,
            "soil_samples": soil_samples,
            "soil_tph_pct": soil_tph_pct,
            "compliance_protocols": protocols_checked,
            "action_required_items": action_required_items,
            "compliance_json": json.dumps(protocols_checked),
            "raw_text": text,
        }

    @classmethod
    def parse_report_file(cls, path: Path) -> Dict[str, Any]:
        """Parse file from path."""
        text = path.read_text(encoding="utf-8")
        return cls.parse_report_text(text, str(path).replace("\\", "/"))
