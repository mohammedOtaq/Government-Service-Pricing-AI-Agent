from __future__ import annotations

from typing import Any

from models.agent_output import AgentOutput


class PolicyComplianceAgent:
    agent_name = "Policy Compliance Agent"
    stage = "policy"

    def run(self, service: dict[str, Any]) -> AgentOutput:
        blockers = []
        missing = []
        findings = []
        questions = []

        critical_checks = {
            "service_is_value_added": "Confirm whether the service is value-added.",
            "clear_beneficiary": "Confirm the direct beneficiary of the service.",
            "legal_authority_available": "Provide the legal or policy authority for collecting the fee.",
        }
        for field, question in critical_checks.items():
            value = service.get(field)
            if value is False:
                blockers.append(field)
            if value is None:
                missing.append(field)
                questions.append(question)

        if service.get("service_is_value_added") is True:
            findings.append("Service is identified as value-added.")
        if service.get("clear_beneficiary") is True:
            findings.append("A clear beneficiary is identified.")
        if service.get("legal_authority_available") is True:
            findings.append("Legal or policy authority is available.")

        non_critical = ["fee_collectable", "customer_journey_reviewed", "renewal_justified", "benchmark_available"]
        for field in non_critical:
            if service.get(field) is None:
                missing.append(field)
                questions.append(f"Confirm {field.replace('_', ' ')}.")

        duplication_risk = service.get("duplication_risk")
        if duplication_risk:
            findings.append(f"Duplication risk is recorded as {duplication_risk}.")
            if str(duplication_risk).lower() in {"medium", "high"}:
                questions.append("Review duplication risk and confirm mitigation before approval.")
        else:
            missing.append("duplication_risk")

        if blockers:
            status = "non_compliant"
        elif any(field in missing for field in critical_checks):
            status = "insufficient_data"
        elif missing:
            status = "completed_with_gaps"
        else:
            status = "approved_for_next_stage"

        return AgentOutput(
            agent_name=self.agent_name,
            stage=self.stage,
            status=status,
            service_id=str(service.get("service_id", "")),
            inputs_used={k: service.get(k) for k in [
                "service_is_value_added", "clear_beneficiary", "legal_authority_available",
                "fee_collectable", "duplication_risk", "renewal_justified",
                "customer_journey_reviewed", "benchmark_available", "subsidy_reason"
            ]},
            analysis={
                "critical_blockers": blockers,
                "duplication_risk": duplication_risk,
                "policy_ready": status in {"approved_for_next_stage", "completed_with_gaps"},
            },
            findings=findings or ["Policy evidence requires further confirmation."],
            missing_data=missing,
            service_owner_questions=questions,
            recommendation="Policy assessment supports continuation." if status in {"approved_for_next_stage", "completed_with_gaps"} else "Resolve policy blockers before approval.",
            next_stage="costing",
            can_continue=status != "non_compliant",
            blocks_final_approval=status in {"non_compliant", "insufficient_data"} or bool(blockers),
        )
