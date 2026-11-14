from __future__ import annotations

import json
from typing import Any

from models.agent_output import validate_agent_output_dict


def load_json_bytes(content: bytes) -> tuple[dict[str, Any] | None, str]:
    try:
        data = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, f"Invalid JSON file: {exc}"
    if not isinstance(data, dict):
        return None, "State file must contain a JSON object"
    valid, message = validate_agent_output_dict(data)
    if not valid:
        return None, message
    return data, message
