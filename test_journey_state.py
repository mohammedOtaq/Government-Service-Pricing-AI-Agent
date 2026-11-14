import json

from models.agent_output import REQUIRED_AGENT_OUTPUT_KEYS
from models.journey_state import next_stage_for
from utils.validation import load_json_bytes


def valid_state():
    return {
        "agent_name": "Test Agent",
        "stage": "benchmark",
        "status": "completed",
        "service_id": "SRV-001",
        "inputs_used": {},
        "analysis": {},
        "findings": [],
        "missing_data": [],
        "service_owner_questions": [],
        "recommendation": "Continue.",
        "next_stage": "scenarios",
        "can_continue": True,
        "blocks_final_approval": False,
    }


def test_standard_output_contains_required_keys():
    assert REQUIRED_AGENT_OUTPUT_KEYS.issubset(valid_state())


def test_upload_validation_accepts_valid_json():
    data, message = load_json_bytes(json.dumps(valid_state()).encode("utf-8"))

    assert data is not None
    assert message == "Valid state file"


def test_upload_validation_rejects_invalid_json():
    state = valid_state()
    del state["agent_name"]

    data, message = load_json_bytes(json.dumps(state).encode("utf-8"))

    assert data is None
    assert "Missing required keys" in message


def test_next_stage_identified():
    assert next_stage_for("benchmark") == "scenarios"
    assert next_stage_for("final") == ""
