from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


VALID_STATUSES = {
    "not_started",
    "in_progress",
    "completed",
    "completed_with_gaps",
    "requires_service_owner_input",
    "blocked",
    "approved_for_next_stage",
    "insufficient_data",
    "non_compliant",
}


REQUIRED_AGENT_OUTPUT_KEYS = {
    "agent_name",
    "stage",
    "status",
    "service_id",
    "inputs_used",
    "analysis",
    "findings",
    "missing_data",
    "service_owner_questions",
    "recommendation",
    "next_stage",
    "can_continue",
    "blocks_final_approval",
}


class AgentOutput(BaseModel):
    agent_name: str
    stage: str
    status: str
    service_id: str = ""
    inputs_used: dict[str, Any] = Field(default_factory=dict)
    analysis: dict[str, Any] = Field(default_factory=dict)
    findings: list[str] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    service_owner_questions: list[str] = Field(default_factory=list)
    recommendation: str = ""
    next_stage: str = ""
    can_continue: bool = True
    blocks_final_approval: bool = False

    def to_state(self) -> dict[str, Any]:
        return self.model_dump()


def validate_agent_output_dict(data: dict[str, Any]) -> tuple[bool, str]:
    missing = sorted(REQUIRED_AGENT_OUTPUT_KEYS - set(data))
    if missing:
        return False, f"Missing required keys: {', '.join(missing)}"
    if data.get("status") not in VALID_STATUSES:
        return False, f"Invalid status: {data.get('status')}"
    if not isinstance(data.get("analysis"), dict):
        return False, "analysis must be an object"
    if not isinstance(data.get("missing_data"), list):
        return False, "missing_data must be a list"
    if not isinstance(data.get("can_continue"), bool):
        return False, "can_continue must be true or false"
    if not isinstance(data.get("blocks_final_approval"), bool):
        return False, "blocks_final_approval must be true or false"
    return True, "Valid state file"
