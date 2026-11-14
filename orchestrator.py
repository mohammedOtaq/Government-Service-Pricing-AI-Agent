from __future__ import annotations

from typing import Any

from agents.benchmark_agent import BenchmarkAgent
from agents.business_case_agent import BusinessCaseAgent
from agents.costing_agent import CostingAgent
from agents.final_recommendation_agent import FinalRecommendationAgent
from agents.policy_agent import PolicyComplianceAgent
from agents.risk_impact_agent import RiskImpactAgent
from agents.scenario_agent import ScenarioAgent
from agents.service_intake_agent import ServiceIntakeAgent
from models.journey_state import STAGE_ORDER
from reports.report_generator import save_report_and_state


class JourneyOrchestrator:
    def __init__(self) -> None:
        self.simple_agents = {
            "service_profile": ServiceIntakeAgent(),
            "policy": PolicyComplianceAgent(),
            "costing": CostingAgent(),
            "benchmark": BenchmarkAgent(),
        }
        self.context_agents = {
            "scenarios": ScenarioAgent(),
            "risk_impact": RiskImpactAgent(),
            "business_case": BusinessCaseAgent(),
            "final": FinalRecommendationAgent(),
        }

    def run_stage(self, stage: str, service: dict[str, Any], outputs: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
        outputs = {key: value for key, value in (outputs or {}).items() if key in STAGE_ORDER}
        if stage in self.simple_agents:
            result = self.simple_agents[stage].run(service)
        elif stage in self.context_agents:
            result = self.context_agents[stage].run(service, outputs)
        else:
            raise ValueError(f"Unknown stage: {stage}")
        state = result.to_state()
        new_outputs = {**outputs, stage: state}
        save_report_and_state(state, service, new_outputs)
        return state

    def run_all(self, service: dict[str, Any], outputs: dict[str, dict[str, Any]] | None = None) -> dict[str, dict[str, Any]]:
        all_outputs = dict(outputs or {})
        for stage in STAGE_ORDER:
            all_outputs[stage] = self.run_stage(stage, service, all_outputs)
            if not all_outputs[stage].get("can_continue", True):
                all_outputs["_journey_warning"] = {
                    "stage": stage,
                    "status": all_outputs[stage].get("status"),
                    "message": f"Full journey stopped at {stage} because this agent returned can_continue=false.",
                    "blocks_final_approval": all_outputs[stage].get("blocks_final_approval", False),
                }
                break
        return all_outputs
