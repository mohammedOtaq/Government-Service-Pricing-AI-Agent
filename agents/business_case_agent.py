from __future__ import annotations

from typing import Any

from models.agent_output import AgentOutput


class BusinessCaseAgent:
    agent_name = "Business Case Agent"
    stage = "business_case"

    def run(self, service: dict[str, Any], prior_outputs: dict[str, dict[str, Any]] | None = None) -> AgentOutput:
        prior_outputs = prior_outputs or {}
        required = ["policy", "costing", "benchmark"]
        missing_evidence = [stage for stage in required if stage not in prior_outputs]
        blocker_stages = [stage for stage in required if prior_outputs.get(stage, {}).get("blocks_final_approval")]

        sections = {
            "executive_summary": f"Draft business case for {service.get('service_name', 'the service')}.",
            "service_description": service.get("service_description", ""),
            "pricing_justification": prior_outputs.get("costing", {}).get("recommendation", ""),
            "policy_compliance_summary": prior_outputs.get("policy", {}).get("recommendation", ""),
            "costing_summary": prior_outputs.get("costing", {}).get("analysis", {}),
            "benchmark_summary": prior_outputs.get("benchmark", {}).get("analysis", {}),
            "scenario_summary": prior_outputs.get("scenarios", {}).get("analysis", {}),
            "risk_and_impact_summary": prior_outputs.get("risk_impact", {}).get("analysis", {}),
            "financial_impact_on_government": prior_outputs.get("costing", {}).get("analysis", {}).get("revenue_difference"),
            "financial_impact_on_customers": prior_outputs.get("costing", {}).get("analysis", {}).get("customer_fee_change"),
        }
        questions = []
        missing = list(missing_evidence)
        for output in prior_outputs.values():
            missing.extend(output.get("missing_data", []))
            questions.extend(output.get("service_owner_questions", []))

        if missing_evidence or blocker_stages:
            status = "insufficient_data"
        elif missing:
            status = "completed_with_gaps"
        else:
            status = "completed"

        return AgentOutput(
            agent_name=self.agent_name,
            stage=self.stage,
            status=status,
            service_id=str(service.get("service_id", "")),
            inputs_used={"available_stages": sorted(prior_outputs)},
            analysis=sections,
            findings=["Draft business case assembled from available agent evidence."],
            missing_data=sorted(set(missing)),
            service_owner_questions=sorted(set(questions)),
            recommendation="Draft business case is ready for final consolidation." if status != "insufficient_data" else "Complete missing critical evidence before final recommendation.",
            next_stage="final",
            can_continue=status != "insufficient_data",
            blocks_final_approval=status == "insufficient_data",
        )
