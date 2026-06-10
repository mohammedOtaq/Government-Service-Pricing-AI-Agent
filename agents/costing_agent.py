from __future__ import annotations

from typing import Any

from models.agent_output import AgentOutput
from utils.calculations import calculate_costing


class CostingAgent:
    agent_name = "Costing Agent"
    stage = "costing"

    def run(self, service: dict[str, Any]) -> AgentOutput:
        analysis, missing = calculate_costing(service)
        annual_transactions = analysis.get("annual_transactions")
        findings: list[str] = []
        questions: list[str] = []

        if "negative_values_not_allowed" in missing:
            questions.append("Correct negative costing values; costs, fees, and transaction volumes must be zero or greater.")
        if annual_transactions in (None, 0):
            questions.append("Provide annual transaction volume greater than zero.")
        if "direct_cost" in missing:
            questions.append("Provide direct cost evidence.")
        if "indirect_cost" in missing:
            questions.append("Provide indirect cost evidence.")

        if analysis.get("total_cost") is not None:
            findings.append(f"Total cost is {analysis['total_cost']:,.2f}.")
        if analysis.get("unit_cost") is not None:
            findings.append(f"Unit cost is {analysis['unit_cost']:,.2f}.")
        if analysis.get("cost_recovery_ratio") is not None:
            findings.append(f"Cost recovery ratio is {analysis['cost_recovery_ratio']:.4f}.")
        if analysis.get("revenue_difference") is not None:
            findings.append(f"Proposed annual revenue change is {analysis['revenue_difference']:,.2f}.")

        if annual_transactions in (None, 0):
            status = "blocked"
        elif "direct_cost" in missing or "indirect_cost" in missing:
            status = "insufficient_data"
        elif "negative_values_not_allowed" in missing:
            status = "blocked"
        elif service.get("third_party_fee") is None or service.get("other_mandatory_charges") is None:
            status = "completed_with_gaps"
            if service.get("third_party_fee") is None:
                missing.append("third_party_fee")
            if service.get("other_mandatory_charges") is None:
                missing.append("other_mandatory_charges")
        else:
            status = "completed"

        recommendation = "Cost recovery is achieved under the proposed fee." if (analysis.get("cost_recovery_ratio") or 0) >= 1 else "Proposed fee does not fully recover unit cost."

        return AgentOutput(
            agent_name=self.agent_name,
            stage=self.stage,
            status=status,
            service_id=str(service.get("service_id", "")),
            inputs_used={k: service.get(k) for k in [
                "direct_cost", "indirect_cost", "annual_transactions", "current_fee",
                "proposed_fee", "third_party_fee", "other_mandatory_charges"
            ]},
            analysis=analysis,
            findings=findings or ["Costing data is incomplete."],
            missing_data=missing,
            service_owner_questions=questions,
            recommendation=recommendation,
            next_stage="benchmark",
            can_continue=status not in {"blocked", "insufficient_data"},
            blocks_final_approval=status in {"blocked", "insufficient_data"},
        )
