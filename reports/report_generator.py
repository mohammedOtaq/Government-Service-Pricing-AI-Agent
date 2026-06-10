from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from models.journey_state import STAGE_LABELS, STAGE_ORDER
from models.service_input import get_service_info
from utils.formatting import money, pct


REPORT_TITLES = {
    "service_profile": "Service Profile Report",
    "policy": "Policy Assessment Report",
    "costing": "Costing Analysis Report",
    "benchmark": "Benchmark Report",
    "scenarios": "What-if Scenario Report",
    "risk_impact": "Risk and Impact Report",
    "business_case": "Draft Business Case Report",
    "final": "Consolidated Final Recommendation Report",
}


def _bullets(items: list[Any], empty: str) -> str:
    if not items:
        return f"- {empty}"
    lines = []
    for item in items:
        if isinstance(item, dict):
            lines.append(f"- {json.dumps(item, ensure_ascii=False)}")
        else:
            lines.append(f"- {item}")
    return "\n".join(lines)


def _analysis_lines(analysis: dict[str, Any]) -> str:
    if not analysis:
        return "- No analysis available."
    lines = []
    for key, value in analysis.items():
        if isinstance(value, list):
            lines.append(f"- {key.replace('_', ' ').title()}:")
            for item in value:
                lines.append(f"  - {json.dumps(item, ensure_ascii=False) if isinstance(item, dict) else item}")
        elif isinstance(value, dict):
            lines.append(f"- {key.replace('_', ' ').title()}: {json.dumps(value, ensure_ascii=False)}")
        else:
            lines.append(f"- {key.replace('_', ' ').title()}: {value}")
    return "\n".join(lines)


def generate_stage_markdown(output: dict[str, Any], service: dict[str, Any]) -> str:
    title = REPORT_TITLES.get(output.get("stage"), "Agent Report")
    info = get_service_info(service)
    return f"""# {title}

## Service Information
- Service ID: {info.get("service_id") or output.get("service_id", "")}
- Service Name: {info.get("service_name", "")}
- Service Owner: {info.get("service_owner", "")}
- Customer Segment: {info.get("customer_segment", "")}
- Service Type: {info.get("service_type", "")}

## Agent Result
- Agent Name: {output.get("agent_name", "")}
- Stage: {output.get("stage", "")}
- Status: {output.get("status", "")}
- Can Continue: {output.get("can_continue", False)}
- Blocks Final Approval: {output.get("blocks_final_approval", False)}

## Analysis
{_analysis_lines(output.get("analysis", {}))}

## Findings
{_bullets(output.get("findings", []), "No findings recorded.")}

## Missing Data
{_bullets(output.get("missing_data", []), "No critical missing data identified.")}

## Service Owner Questions
{_bullets(output.get("service_owner_questions", []), "No service owner questions at this stage.")}

## Recommendation
{output.get("recommendation", "")}

## Next Step
{output.get("next_stage") or "No further stage."}
"""


def generate_final_markdown(output: dict[str, Any], service: dict[str, Any], all_outputs: dict[str, dict[str, Any]]) -> str:
    analysis = output.get("analysis", {})
    costing = analysis.get("costing", {})
    benchmark = analysis.get("benchmark", {})
    journey = analysis.get("journey_completion", {})
    profile = get_service_info(service)
    scenarios = analysis.get("scenarios", {}).get("scenarios", [])
    risks = analysis.get("risks", {}).get("risks", [])
    business_case = analysis.get("business_case", {})
    proposed_fee = costing.get("proposed_fee")
    unit_cost = costing.get("unit_cost")
    cost_recovery_ratio = costing.get("cost_recovery_ratio")
    total_customer_cost = costing.get("total_customer_cost")
    customer_fee_change = costing.get("customer_fee_change")
    current_fee = costing.get("current_fee")
    current_revenue = costing.get("current_annual_revenue")
    proposed_revenue = costing.get("proposed_annual_revenue")
    revenue_difference = costing.get("revenue_difference")
    reference_benchmark_fee = benchmark.get("reference_benchmark_fee") or benchmark.get("average_benchmark_fee")
    benchmark_gap_pct = None
    if proposed_fee is not None and reference_benchmark_fee:
        benchmark_gap_pct = (float(proposed_fee) - float(reference_benchmark_fee)) / float(reference_benchmark_fee)
    fee_change_pct = None
    if current_fee:
        fee_change_pct = abs(float(customer_fee_change or 0) / float(current_fee))

    journey_lines = "\n".join(f"- {STAGE_LABELS.get(stage, stage)}: {journey.get(stage, 'not_started')}" for stage in STAGE_ORDER[:-1])
    comparator_lines = _bullets(benchmark.get("comparator_summary", []), "No benchmark comparators available.")
    scenario_lines = _bullets(scenarios, "No scenarios available.")
    risk_lines = _bullets(risks, "No risks available.")

    return f"""# Consolidated Final Recommendation Report

## 1. Executive Summary
{service.get("service_name", "This service")} was assessed through the available pricing journey evidence. Final recommendation: {analysis.get("final_decision", output.get("recommendation", ""))}.

## 2. Journey Completion Status
{journey_lines}

## 3. Service Profile Summary
- Service ID: {profile.get("service_id")}
- Service Name: {profile.get("service_name")}
- Service Owner: {profile.get("service_owner")}
- Customer Segment: {profile.get("customer_segment")}
- Service Type: {profile.get("service_type")}
- Description: {service.get("service_description", "")}

## 4. Policy Compliance Assessment
- Status: {all_outputs.get("policy", {}).get("status", "not_started")}
- Blockers: {", ".join(analysis.get("blockers", [])) or "None identified"}
- Summary: {all_outputs.get("policy", {}).get("recommendation", "")}

## 5. Costing Analysis
- Total Cost: {money(costing.get("total_cost"))}
- Unit Cost: {money(costing.get("unit_cost"))}
- Current Annual Revenue: {money(costing.get("current_annual_revenue"))}
- Proposed Annual Revenue: {money(costing.get("proposed_annual_revenue"))}
- Revenue Difference: {money(costing.get("revenue_difference"))}
- Cost Recovery Ratio: {pct(costing.get("cost_recovery_ratio"))}

## 6. Benchmarking Analysis
- Benchmark Status: {benchmark.get("benchmark_status", "Not available")}
- Competitiveness Risk: {benchmark.get("competitiveness_risk", "Not available")}
- Classification: {benchmark.get("classification", "Not available")}
- Average Benchmark Fee: {money(benchmark.get("average_benchmark_fee"))}
- Comparator Summary:
{comparator_lines}

## 7. Scenario Analysis
{scenario_lines}

## 8. Risk and Impact Assessment
{risk_lines}

## 9. Business Case Justification
### Pricing Justification
The proposed fee of AED {money(proposed_fee)} per transaction recovers {pct(cost_recovery_ratio)} of the calculated unit cost of AED {money(unit_cost)}, providing a cost recovery surplus. The total customer cost, including third-party and mandatory charges, is AED {money(total_customer_cost)}. This represents a fee reduction of AED {money(abs(customer_fee_change or 0))}, or {pct(fee_change_pct)}, from the current fee of AED {money(current_fee)}, reducing the annual revenue forecast by AED {money(abs(revenue_difference or 0))}. The proposed fee is {pct(benchmark_gap_pct)} above the average GCC/international benchmark of AED {money(reference_benchmark_fee)} and requires benchmark validation before approval. With {service.get("automation_level_percentage", "not provided")}% automation and a {service.get("average_processing_time_minutes", "not provided")}-minute average processing time, there is further efficiency headroom that could support a lower fee at the next renewal period without reducing cost recovery.

### Government Financial Impact
Annual revenue decreases from AED {money(current_revenue)} to AED {money(proposed_revenue)}, a reduction of AED {money(abs(revenue_difference or 0))}. Cost recovery is maintained above 100% at the proposed fee level.

### Customer Impact
Customers pay AED {money(abs(customer_fee_change or 0))} less per transaction than under the current fee. The total mandatory cost remains competitive with GCC/regional benchmarks once third-party charges are included. The fee reduction supports affordability for SMEs.

### Conditions for Approval
1. Provide verified source evidence for at least two GCC or regional comparators and one international comparator.
2. Confirm that duplication risk is medium and document mitigation measures.
3. Provide economic, social, and environmental impact data.
4. Confirm that legal authority and policy justification for fee collection are formally documented.

### Draft Business Case Summary
- Executive Summary: {business_case.get("executive_summary", "Not available")}
- Pricing Justification: {business_case.get("pricing_justification", "Not available")}

## 10. Data Gaps
{_bullets(output.get("missing_data", []), "No critical missing data identified.")}

## 11. Service Owner Questions
{_bullets(output.get("service_owner_questions", []), "No service owner questions at this stage.")}

## 12. Final Recommendation
{analysis.get("final_decision", output.get("recommendation", ""))}

## 13. Approval Readiness
{analysis.get("approval_readiness", "Not ready for approval")}
"""


def save_report_and_state(output: dict[str, Any], service: dict[str, Any], all_outputs: dict[str, dict[str, Any]] | None = None, base_dir: str | Path = "outputs") -> tuple[Path, Path]:
    stage = output["stage"]
    folder = Path(base_dir) / stage
    folder.mkdir(parents=True, exist_ok=True)
    if stage == "final":
        markdown = generate_final_markdown(output, service, all_outputs or {})
    else:
        markdown = generate_stage_markdown(output, service)
    report_path = folder / f"{stage}_report.md"
    state_path = folder / f"{stage}_state.json"
    report_path.write_text(markdown, encoding="utf-8")
    state_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    return report_path, state_path
