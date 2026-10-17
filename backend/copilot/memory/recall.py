"""
backend/copilot/memory/recall.py — Re-exports from src.memory.recall for backwards compatibility.
"""
from src.memory.recall import (
    record_turn,
    get_recent_wells,
    resolve_referent_wells,
    get_user_history,
    has_conversation_history,
    save_interaction,
    recall_wells,
    recall_entities,
)

__all__ = [
    "record_turn",
    "get_recent_wells",
    "resolve_referent_wells",
    "get_user_history",
    "has_conversation_history",
    "save_interaction",
    "recall_wells",
    "recall_entities",
]
