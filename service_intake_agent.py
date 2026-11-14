from __future__ import annotations

from typing import Any

from models.agent_output import AgentOutput


class ServiceIntakeAgent:
    agent_name = "Service Intake Agent"
    stage = "service_profile"

    def run(self, service: dict[str, Any]) -> AgentOutput:
        critical = ["service_name", "service_owner", "service_type", "service_description", "customer_segment"]
        missing = [field for field in critical if not service.get(field)]
        findings: list[str] = []
        questions: list[str] = []

        if service.get("service_name"):
            findings.append(f"Service identified as {service.get('service_name')}.")
        if service.get("is_recurring") and not service.get("renewal_period_months"):
            missing.append("renewal_period_months")
            questions.append("Confirm the renewal period for this recurring service.")
        description = str(service.get("service_description") or "")
        if description and len(description.split()) < 8:
            missing.append("service_description_detail")
            questions.append("Provide a fuller service description, including purpose and beneficiary.")

        if any(field in missing for field in ["service_owner", "service_type", "service_description"]):
            status = "requires_service_owner_input"
        elif missing:
            status = "completed_with_gaps"
        else:
            status = "completed"

        if service.get("automation_level_percentage") is not None:
            findings.append(f"Automation level recorded at {service.get('automation_level_percentage')}%.")
        if service.get("average_processing_time_minutes") is not None:
            findings.append(f"Average processing time recorded as {service.get('average_processing_time_minutes')} minutes.")

        return AgentOutput(
            agent_name=self.agent_name,
            stage=self.stage,
            status=status,
            service_id=str(service.get("service_id", "")),
            inputs_used={k: service.get(k) for k in [
                "service_id", "service_name", "service_type", "service_owner", "customer_segment",
                "is_mandatory", "is_recurring", "renewal_period_months", "service_description",
                "channel", "automation_level_percentage", "average_processing_time_minutes"
            ]},
            analysis={
                "core_fields_complete": not missing,
                "is_recurring": service.get("is_recurring"),
                "renewal_period_months": service.get("renewal_period_months"),
            },
            findings=findings or ["Basic service profile reviewed."],
            missing_data=missing,
            service_owner_questions=questions,
            recommendation="Proceed to policy assessment once core service profile fields are confirmed.",
            next_stage="policy",
            can_continue=status != "requires_service_owner_input",
            blocks_final_approval=bool(missing),
        )
