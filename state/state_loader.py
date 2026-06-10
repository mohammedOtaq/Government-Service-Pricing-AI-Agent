from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from models.agent_output import validate_agent_output_dict


def load_state_file(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    valid, message = validate_agent_output_dict(data)
    if not valid:
        raise ValueError(message)
    return data


def validate_uploaded_state(data: dict[str, Any]) -> tuple[bool, str]:
    return validate_agent_output_dict(data)
