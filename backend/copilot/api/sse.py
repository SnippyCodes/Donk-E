import json
from typing import Any, Dict, Optional


def format_sse(data: Dict[str, Any], event: Optional[str] = None) -> str:
    """Format dictionary payload as standard Server-Sent Events (SSE) string."""
    msg = ""
    if event:
        msg += f"event: {event}\n"
    json_str = json.dumps(data)
    msg += f"data: {json_str}\n\n"
    return msg
