from __future__ import annotations

from typing import Any

from models.agent_output import AgentOutput
from models.journey_state import STAGE_ORDER


class FinalRecommendationAgent:
    agent_name = "Final Recommendation Agent"
    stage = "final"

    def run(self, service: dict[str, Any], prior_outputs: dict[str, dict[str, Any]] | None = None) -> AgentOutput:
        prior_outputs = prior_outputs or {}
        missing_stages = [stage for stage in STAGE_ORDER[:-1] if stage not in prior_outputs]
        missing_evidence = []
        questions = []
        blockers = []

        for stage, output in prior_outputs.items():
            missing_evidence.extend(output.get("missing_data", []))
            questions.extend(output.get("service_owner_questions", []))
            if output.get("blocks_final_approval"):
                blockers.append(stage)

        policy = prior_outputs.get("policy", {})
        costing = prior_outputs.get("costing", {})
        benchmark = prior_outputs.get("benchmark", {})

        policy_status = policy.get("status", "not_started")
        costing_status = costing.get("status", "not_started")
        benchmark_status = benchmark.get("status", "not_started")
        critical_governance_blocker = False

        if policy_status == "non_compliant":
            blockers.append("critical_policy_blocker")
            critical_governance_blocker = True
        elif policy_status == "insufficient_data":
            blockers.append("critical_policy_evidence")
        if costing_status in {"blocked", "insufficient_data"}:
            blockers.append("costing_blocked")
        if benchmark_status == "insufficient_data" and not service.get("benchmark_limitation_justification"):
            blockers.append("benchmark_insufficient")
        if service.get("service_is_value_added") is None:
            blockers.append("service_value_added_missing")
        if service.get("clear_beneficiary") is None:
            blockers.append("clear_beneficiary_missing")
        if service.get("service_is_value_added") is False or service.get("clear_beneficiary") is False:
            blockers.append("core_fee_justification_failed")
            critical_governance_blocker = True

        costing_analysis = costing.get("analysis", {})
        benchmark_analysis = benchmark.get("analysis", {})
        cost_recovery = (costing_analysis.get("cost_recovery_ratio") or 0) >= 1
        fee_lower_than_current = (costing_analysis.get("customer_fee_change") or 0) <= 0
        total_customer_cost = costing_analysis.get("total_customer_cost")
        competitiveness_risk = bool(benchmark_analysis.get("competitiveness_risk"))
        benchmark_classification = benchmark_analysis.get("classification", "insufficient_data")
        duplication_medium = str(service.get("duplication_risk", "")).lower() in {"medium", "high"}
        automation_level = float(service.get("automation_level_percentage") or 0)
        benchmark_limited = bool(service.get("benchmark_limitation_justification")) or benchmark_status in {"completed_with_gaps", "insufficient_data"}
        material_missing_evidence = bool(missing_stages or blockers or len(set(missing_evidence)) >= 3)

        if critical_governance_blocker:
            final_decision = "Not recommended"
            readiness = "Not ready for approval"
            status = "completed_with_gaps"
            can_continue = False
        elif blockers or missing_stages or material_missing_evidence and not cost_recovery:
            final_decision = "Insufficient data for decision"
            readiness = "Not ready for approval"
            status = "insufficient_data"
            can_continue = False
        elif cost_recovery and (
            competitiveness_risk
            or duplication_medium
            or benchmark_limited
            or benchmark_classification in {"slightly_above_benchmark", "significantly_above_benchmark", "insufficient_data"}
            or missing_evidence
            or total_customer_cost is None
            or automation_level >= 50
        ):
            final_decision = "Recommended with conditions"
            readiness = "Ready for conditional review"
            status = "completed_with_gaps"
            can_continue = True
        elif cost_recovery:
            final_decision = "Recommended for approval"
            readiness = "Ready for approval"
            status = "completed"
            can_continue = True
        else:
            final_decision = "Not recommended"
            readiness = "Not ready for approval"
            status = "completed_with_gaps"
            can_continue = True

        findings = [
            f"Final decision: {final_decision}.",
            "Cost recovery is achieved." if cost_recovery else "Cost recovery is not achieved.",
        ]
        if fee_lower_than_current:
            findings.append("Proposed fee is lower than or equal to the current fee, supporting customer affordability.")
        if total_customer_cost is not None:
            findings.append(f"Total customer cost is {total_customer_cost:,.2f}.")
        if competitiveness_risk:
            findings.append("Proposed fee is above available benchmark evidence, so benchmark validation is required.")
        if duplication_medium:
            findings.append("Duplication risk is medium or high and should be reviewed before approval.")
        if automation_level >= 50:
            findings.append("Automation level suggests future efficiency headroom should be considered in renewal review.")

        return AgentOutput(
            agent_name=self.agent_name,
            stage=self.stage,
            status=status,
            service_id=str(service.get("service_id", "")),
            inputs_used={"available_stages": sorted(prior_outputs)},
            analysis={
                "final_decision": final_decision,
                "approval_readiness": readiness,
                "journey_completion": {stage: prior_outputs.get(stage, {}).get("status", "not_started") for stage in STAGE_ORDER[:-1]},
                "missing_stages": missing_stages,
                "blockers": sorted(set(blockers)),
                "policy_status": policy_status,
                "costing_status": costing_status,
                "benchmark_status": benchmark_status,
                "benchmark_classification": benchmark_classification,
                "customer_total_cost": total_customer_cost,
                "customer_fee_impact": costing_analysis.get("customer_fee_change"),
                "automation_level_percentage": automation_level,
                "benchmark_limitation_justification": service.get("benchmark_limitation_justification", ""),
                "costing": costing_analysis,
                "benchmark": benchmark_analysis,
                "scenarios": prior_outputs.get("scenarios", {}).get("analysis", {}),
                "risks": prior_outputs.get("risk_impact", {}).get("analysis", {}),
                "business_case": prior_outputs.get("business_case", {}).get("analysis", {}),
            },
            findings=findings,
            missing_data=sorted(set(missing_evidence + missing_stages)),
            service_owner_questions=sorted(set(questions)),
            recommendation=final_decision,
            next_stage="",
            can_continue=can_continue,
            blocks_final_approval=status == "insufficient_data" or final_decision in {"Not recommended", "Insufficient data for decision"},
        )
