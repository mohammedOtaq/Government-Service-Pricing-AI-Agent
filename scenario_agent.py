from __future__ import annotations

from typing import Any

from models.agent_output import AgentOutput
from utils.calculations import calculate_costing


class ScenarioAgent:
    agent_name = "Scenario Agent"
    stage = "scenarios"

    def run(self, service: dict[str, Any], prior_outputs: dict[str, dict[str, Any]] | None = None) -> AgentOutput:
        prior_outputs = prior_outputs or {}
        costing = prior_outputs.get("costing", {}).get("analysis") or calculate_costing(service)[0]
        annual_transactions = costing.get("annual_transactions")
        unit_cost = costing.get("unit_cost")
        proposed_fee = costing.get("proposed_fee") or service.get("proposed_fee")
        current_fee = costing.get("current_fee") or service.get("current_fee") or 0
        benchmark = prior_outputs.get("benchmark", {}).get("analysis", {})
        reference_benchmark_fee = benchmark.get("reference_benchmark_fee") or service.get("benchmark_fee")
        automation_level = float(service.get("automation_level_percentage") or 0)

        if not annual_transactions or not proposed_fee:
            return AgentOutput(
                agent_name=self.agent_name,
                stage=self.stage,
                status="blocked",
                service_id=str(service.get("service_id", "")),
                inputs_used={"costing": costing},
                analysis={},
                findings=["Scenario analysis requires completed costing evidence."],
                missing_data=["costing_data"],
                service_owner_questions=["Complete costing data before scenario analysis."],
                recommendation="Complete costing before generating scenarios.",
                next_stage="risk_impact",
                can_continue=False,
                blocks_final_approval=True,
            )

        proposed_fee_float = float(proposed_fee)
        current_fee_float = float(current_fee)
        unit_cost_float = float(unit_cost or proposed_fee_float)
        benchmark_fee_float = float(reference_benchmark_fee or proposed_fee_float)

        conservative_fee = max(unit_cost_float, min(proposed_fee_float, current_fee_float * 0.9, benchmark_fee_float))
        balanced_fee = max(unit_cost_float, min(proposed_fee_float, benchmark_fee_float * 1.05))
        efficiency_factor = 0.85 if automation_level >= 60 else 0.9
        transformational_fee = max(unit_cost_float, min(balanced_fee * efficiency_factor, benchmark_fee_float * 0.95))

        scenarios = [
            {
                "scenario_name": "Conservative scenario",
                "proposed_fee": round(conservative_fee, 2),
                "estimated_revenue": round(conservative_fee * float(annual_transactions), 2),
                "customer_impact": "Minimizes fee shock and keeps the proposed fee below or close to current fee.",
                "government_impact": "Maintains revenue while protecting cost recovery where possible.",
                "risk_level": "Low",
                "rationale": "Avoid sharp fee increase and protect customer acceptance.",
                "assumptions": ["No major service redesign.", "Transaction volumes remain stable.", "Fee remains at or above calculated unit cost."],
            },
            {
                "scenario_name": "Balanced scenario",
                "proposed_fee": round(float(balanced_fee), 2),
                "estimated_revenue": round(float(balanced_fee) * float(annual_transactions), 2),
                "customer_impact": "Balances affordability, cost recovery, and benchmark position.",
                "government_impact": "Uses the proposed fee as the core policy option.",
                "risk_level": "Medium",
                "rationale": "Balances cost recovery, competitiveness, and customer impact.",
                "assumptions": ["Benchmark evidence is validated.", "Policy authority remains confirmed.", "Fee remains close to the benchmark reference where possible."],
            },
            {
                "scenario_name": "Transformational scenario",
                "proposed_fee": round(transformational_fee, 2),
                "estimated_revenue": round(transformational_fee * float(annual_transactions), 2),
                "customer_impact": "Assumes automation or redesign can lower customer cost over time.",
                "government_impact": "May reduce revenue but supports digital transformation and customer experience.",
                "risk_level": "Medium",
                "rationale": "Uses automation, bundling, or service redesign to reduce processing burden.",
                "assumptions": ["Automation reduces processing cost.", "Service owner can implement journey improvements.", "Digital efficiency allows future fee review without dropping below current unit cost."],
            },
        ]

        benchmark_status = prior_outputs.get("benchmark", {}).get("status")
        status = "completed" if benchmark_status in {"completed", "completed_with_gaps"} else "completed_with_gaps"
        missing = [] if status == "completed" else ["validated_benchmark_evidence"]

        return AgentOutput(
            agent_name=self.agent_name,
            stage=self.stage,
            status=status,
            service_id=str(service.get("service_id", "")),
            inputs_used={"costing": costing, "benchmark_status": benchmark_status, "reference_benchmark_fee": reference_benchmark_fee},
            analysis={"scenarios": scenarios},
            findings=["Three what-if scenarios generated from available costing evidence."],
            missing_data=missing,
            service_owner_questions=[] if not missing else ["Validate benchmark evidence before selecting a final scenario."],
            recommendation="Use the balanced scenario as the base case, with conditions linked to benchmark validation.",
            next_stage="risk_impact",
            can_continue=True,
            blocks_final_approval=False,
        )
