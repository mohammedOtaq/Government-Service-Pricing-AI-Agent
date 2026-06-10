from __future__ import annotations

from typing import Any


STAGE_ORDER = [
    "service_profile",
    "policy",
    "costing",
    "benchmark",
    "scenarios",
    "risk_impact",
    "business_case",
    "final",
]

STAGE_LABELS = {
    "service_profile": "Service Intake",
    "policy": "Policy Assessment",
    "costing": "Costing",
    "benchmark": "Benchmarking",
    "scenarios": "Scenarios",
    "risk_impact": "Risk & Impact",
    "business_case": "Business Case",
    "final": "Final Recommendation",
}


def next_stage_for(stage: str) -> str:
    if stage not in STAGE_ORDER:
        return ""
    idx = STAGE_ORDER.index(stage)
    if idx + 1 >= len(STAGE_ORDER):
        return ""
    return STAGE_ORDER[idx + 1]


def initial_progress() -> dict[str, str]:
    return {stage: "not_started" for stage in STAGE_ORDER}


def progress_from_outputs(outputs: dict[str, dict[str, Any]]) -> dict[str, str]:
    progress = initial_progress()
    for stage, output in outputs.items():
        if stage in progress:
            progress[stage] = output.get("status", "not_started")
    return progress
