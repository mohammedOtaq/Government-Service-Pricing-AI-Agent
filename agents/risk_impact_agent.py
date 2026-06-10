from __future__ import annotations

from typing import Any

from models.agent_output import AgentOutput


class RiskImpactAgent:
    agent_name = "Risk and Impact Agent"
    stage = "risk_impact"

    def run(self, service: dict[str, Any], prior_outputs: dict[str, dict[str, Any]] | None = None) -> AgentOutput:
        prior_outputs = prior_outputs or {}
        benchmark = prior_outputs.get("benchmark", {}).get("analysis", {})
        costing = prior_outputs.get("costing", {}).get("analysis", {})
        risks = []

        if benchmark.get("competitiveness_risk"):
            risks.append({"risk": "competitiveness risk", "level": "Medium", "mitigation": "Validate benchmark evidence and consider conditional fee review."})
        if str(service.get("duplication_risk", "")).lower() in {"medium", "high"}:
            risks.append({"risk": "duplication risk", "level": str(service.get("duplication_risk")).title(), "mitigation": "Review overlap with other mandatory charges or permits."})
        if (costing.get("customer_fee_change") or 0) > 0:
            risks.append({"risk": "customer perception risk", "level": "Medium", "mitigation": "Explain service value and phase any increase if needed."})
        else:
            risks.append({"risk": "customer perception risk", "level": "Low", "mitigation": "Communicate that the proposed fee is lower than the current fee."})

        risks.extend([
            {"risk": "compliance risk", "level": "Low" if service.get("legal_authority_available") else "High", "mitigation": "Keep legal or policy authority evidence with the business case."},
            {"risk": "operational risk", "level": "Medium", "mitigation": "Confirm implementation readiness and system changes."},
            {"risk": "data quality risk", "level": "Medium", "mitigation": "Validate prototype sample evidence before real approval."},
        ])

        missing = []
        if service.get("economic_impact") is None:
            missing.append("economic_impact")
        if service.get("social_impact") is None:
            missing.append("social_impact")
        if service.get("environmental_impact") is None:
            missing.append("environmental_impact")

        return AgentOutput(
            agent_name=self.agent_name,
            stage=self.stage,
            status="completed_with_gaps" if missing else "completed",
            service_id=str(service.get("service_id", "")),
            inputs_used={"benchmark": benchmark, "costing": costing},
            analysis={
                "risks": risks,
                "economic_impact": service.get("economic_impact", "Not provided"),
                "social_impact": service.get("social_impact", "Not provided"),
                "environmental_impact": service.get("environmental_impact", "Not provided"),
            },
            findings=["Key risks and impacts have been assessed using available evidence."],
            missing_data=missing,
            service_owner_questions=["Provide economic, social, and environmental impact evidence where available."] if missing else [],
            recommendation="Proceed with conditions focused on benchmark validation, duplication review, and data quality.",
            next_stage="business_case",
            can_continue=True,
            blocks_final_approval=False,
        )
