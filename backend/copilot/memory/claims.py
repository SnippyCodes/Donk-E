"""
backend/copilot/memory/claims.py — Re-exports from src.domain.claims for backwards compatibility.
"""
from src.domain.claims import (
    check_claim,
    check_note_disagreement,
    check_correction_conflicts,
    check,
    check_spill_disagreement,
)

__all__ = [
    "check_claim",
    "check_note_disagreement",
    "check_correction_conflicts",
    "check",
    "check_spill_disagreement",
]
