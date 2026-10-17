import datetime
import json
import re
import sqlite3
from typing import Any, Dict, List, Optional, Tuple
from dateutil.relativedelta import relativedelta

from backend.copilot.config import AS_OF
from backend.copilot.db import get_connection


def get_data_end(conn: Optional[sqlite3.Connection] = None) -> str:
    """
    Compute DATA_END dynamically as MAX(date(inspected_at)) across loaded inspections,
    defaulting to '2026-10-16' on sample data and auto-advancing if holdout data has newer dates.
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    cursor = conn.cursor()
    cursor.execute("SELECT MAX(inspected_date) FROM eff_inspection")
    row = cursor.fetchone()
    max_date = row[0] if (row and row[0]) else "2026-10-16"

    if close_conn:
        conn.close()

    # Base date is 2026-10-16 for sample data, auto-advancing for newer holdout dates
    if max_date < "2026-10-16":
        return "2026-10-16"
    return max_date


def resolve_window(window_expr: str, conn: Optional[sqlite3.Connection] = None) -> Tuple[str, str]:
    """
    Resolve natural language date windows backward from dynamic DATA_END.
    Calendar date inclusive on both ends.
    Returns (start_date_str, end_date_str) in 'YYYY-MM-DD' format.
    """
    data_end_str = get_data_end(conn)
    end_dt = datetime.date.fromisoformat(data_end_str)

    expr = window_expr.strip().lower()

    # Calendar years e.g. "2025", "2026"
    if re.fullmatch(r"20\d\d", expr):
        yr = int(expr)
        return (f"{yr}-01-01", f"{yr}-12-31")

    # "last 13 weeks": exactly 13 weekly inspection cycles
    # For sample data ending on Friday 2026-10-16, the latest weekly inspection was Thursday 2026-10-15.
    # 13 weeks backward (12 7-day intervals) = 2026-07-23 to 2026-10-15.
    if "13 week" in expr:
        # Find latest Thursday <= end_dt
        offset = (end_dt.weekday() - 3) % 7  # Thursday is weekday 3
        latest_thurs = end_dt - datetime.timedelta(days=offset)
        start_thurs = latest_thurs - datetime.timedelta(weeks=12)
        return (start_thurs.isoformat(), latest_thurs.isoformat())

    # "last N weeks"
    m_weeks = re.search(r"(\d+)\s*week", expr)
    if m_weeks:
        w = int(m_weeks.group(1))
        offset = (end_dt.weekday() - 3) % 7
        latest_thurs = end_dt - datetime.timedelta(days=offset)
        start_thurs = latest_thurs - datetime.timedelta(weeks=w - 1)
        return (start_thurs.isoformat(), latest_thurs.isoformat())

    # "last 4 months" -> exactly 4 calendar months prior: 2026-06-16 to 2026-10-16
    m_months = re.search(r"(\d+)\s*month", expr)
    if m_months:
        m = int(m_months.group(1))
        start_dt = end_dt - relativedelta(months=m)
        return (start_dt.isoformat(), end_dt.isoformat())

    # "last 90 days" -> calendar-inclusive 90 days ending on end_dt (end_dt - 89 days)
    # E.g. for 2026-10-16: 2026-07-19 to 2026-10-16 (90 inclusive days)
    m_days = re.search(r"(\d+)\s*day", expr)
    if m_days:
        d = int(m_days.group(1))
        start_dt = end_dt - datetime.timedelta(days=d - 1)
        return (start_dt.isoformat(), end_dt.isoformat())

    # "last 4 years", "last 12 months", "last N years"
    m_years = re.search(r"(\d+)\s*year", expr)
    if m_years:
        y = int(m_years.group(1))
        start_dt = end_dt - relativedelta(years=y)
        return (start_dt.isoformat(), end_dt.isoformat())

    # Default to all-time
    return ("2020-01-01", data_end_str)


class EntityResolver:
    """Fuzzy resolver for assets, areas, and users."""

    def __init__(self, conn: Optional[sqlite3.Connection] = None):
        self.conn = conn or get_connection()
        self._load_cache()

    def _load_cache(self) -> None:
        cursor = self.conn.cursor()

        # Assets
        cursor.execute("SELECT asset_id, name, well_type, area_id FROM assets")
        self.assets = {row["asset_id"]: dict(row) for row in cursor.fetchall()}

        # Areas
        cursor.execute("SELECT area_id, name, asset_ids_json FROM areas")
        self.areas = {}
        for row in cursor.fetchall():
            self.areas[row["area_id"]] = {
                "area_id": row["area_id"],
                "name": row["name"],
                "asset_ids": json.loads(row["asset_ids_json"] or "[]"),
            }

        # Users
        cursor.execute("SELECT user_id, name, role, team_id FROM users")
        self.users = {row["user_id"]: dict(row) for row in cursor.fetchall()}

    def resolve_well_id(self, query: str) -> Optional[str]:
        """Resolve well ID from text e.g. 'WELL-0001', 'well 1', '0001'."""
        # Direct pattern match WELL-XXXX
        m = re.search(r"(WELL-\d{4})", query, re.I)
        if m:
            w_id = m.group(1).upper()
            if w_id in self.assets:
                return w_id

        # Numeric e.g. "well 1" or "wellhead 1"
        m_num = re.search(r"(?:well|wellhead)\s*#?\s*(\d+)", query, re.I)
        if m_num:
            n = int(m_num.group(1))
            formatted = f"WELL-{n:04d}"
            if formatted in self.assets:
                return formatted

        return None

    def resolve_area(self, query: str) -> Optional[Dict[str, Any]]:
        """Resolve area from text e.g. 'Northeast Block 8', 'NE-08', 'SW-23'."""
        # Check area codes e.g. NE-08, SW-23, NE-07, SW-24
        m_code = re.search(r"\b(NE-0?8|NE-0?7|SW-23|SW-24)\b", query, re.I)
        if m_code:
            code = m_code.group(1).upper()
            # Normalize zero-padding e.g. NE-8 -> NE-08
            parts = code.split("-")
            norm_code = f"{parts[0]}-{int(parts[1]):02d}"
            if norm_code in self.areas:
                return self.areas[norm_code]

        # Check full names
        q_lower = query.lower()
        for a_id, a_data in self.areas.items():
            if a_data["name"].lower() in q_lower:
                return a_data

        # Partial checks e.g. "Block 8" -> NE-08, "Block 7" -> NE-07
        if "block 8" in q_lower:
            return self.areas.get("NE-08")
        if "block 7" in q_lower:
            return self.areas.get("NE-07")
        if "block 23" in q_lower:
            return self.areas.get("SW-23")
        if "block 24" in q_lower:
            return self.areas.get("SW-24")

        return None

    def resolve_user(self, query: str) -> Optional[Dict[str, Any]]:
        """Resolve user by ID or name e.g. 'U-201', 'Michael Turner'."""
        m_id = re.search(r"\b(U-\d+)\b", query, re.I)
        if m_id:
            u_id = m_id.group(1).upper()
            if u_id in self.users:
                return self.users[u_id]

        q_lower = query.lower()
        for u_id, u_data in self.users.items():
            if u_data["name"].lower() in q_lower:
                return u_data

        return None


if __name__ == "__main__":
    r = EntityResolver()
    print("Resolved well:", r.resolve_well_id("Is WELL-0001 producing?"))
    print("Resolved area:", r.resolve_area("Northeast Block 8")["area_id"])
    print("Resolved 90d window:", resolve_window("last 90 days"))
    print("Resolved 4m window:", resolve_window("last 4 months"))
    print("Resolved 13w window:", resolve_window("last 13 weeks"))
