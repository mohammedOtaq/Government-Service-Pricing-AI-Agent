from __future__ import annotations

from statistics import mean
from typing import Any

from models.agent_output import AgentOutput


BENCHMARK_QUESTIONS = [
    "Provide comparable services in at least 2 GCC/regional jurisdictions.",
    "Provide at least 1 high-performing international comparator, where available.",
    "Provide fee amount and currency.",
    "Provide renewal frequency.",
    "Provide mandatory third-party charges.",
    "Provide other mandatory charges.",
    "Provide processing time.",
    "Provide number of steps.",
    "Provide source link, document, or official evidence.",
    "Explain if this service should not be directly compared and why.",
]

VALID_REGIONS = {"gcc", "regional", "international", "unknown"}


class BenchmarkAgent:
    agent_name = "Benchmark Agent"
    stage = "benchmark"

    def run(self, service: dict[str, Any]) -> AgentOutput:
        comparators = service.get("benchmark_comparators") or []
        proposed_fee = service.get("proposed_fee")
        explicit_benchmark_fee = service.get("benchmark_fee")
        current_fee = service.get("current_fee")
        missing: list[str] = []
        findings: list[str] = []
        questions: list[str] = []

        valid_comparators = []
        for item in comparators:
            if not isinstance(item, dict) or item.get("fee_amount") is None or not item.get("source_or_evidence"):
                continue
            normalized = dict(item)
            region = str(normalized.get("region") or "unknown").lower()
            normalized["region"] = region if region in VALID_REGIONS else "unknown"
            valid_comparators.append(normalized)

        gcc_count = sum(1 for item in valid_comparators if item.get("region") in {"gcc", "regional"})
        international_count = sum(1 for item in valid_comparators if item.get("region") == "international")

        if not valid_comparators:
            missing.append("benchmark_comparators")
            questions.extend(BENCHMARK_QUESTIONS)
            benchmark_status = "insufficient_data"
            classification = "benchmark_missing"
            avg_fee = None
        else:
            fees = [float(item["fee_amount"]) for item in valid_comparators]
            avg_fee = mean(fees)
            reference_fee = float(explicit_benchmark_fee) if explicit_benchmark_fee is not None else avg_fee
            if proposed_fee is None:
                missing.append("proposed_fee")
                classification = "insufficient_data"
            else:
                ratio = float(proposed_fee) / reference_fee if reference_fee else None
                if ratio is None:
                    classification = "insufficient_data"
                elif ratio <= 0.95:
                    classification = "below_benchmark"
                elif ratio <= 1:
                    classification = "competitive"
                elif ratio <= 1.2:
                    classification = "slightly_above_benchmark"
                else:
                    classification = "significantly_above_benchmark"

            if gcc_count < 2:
                missing.append("2_gcc_or_regional_comparators")
                questions.append(BENCHMARK_QUESTIONS[0])
            if international_count < 1:
                missing.append("international_comparator")
                questions.append(BENCHMARK_QUESTIONS[1])
            benchmark_status = "completed" if not missing else "completed_with_gaps"

        if avg_fee is not None:
            findings.append(f"Average benchmark fee from available evidence is {avg_fee:,.2f}.")
        if classification in {"slightly_above_benchmark", "significantly_above_benchmark"}:
            findings.append("Proposed fee is above available benchmark evidence, creating competitiveness risk.")
        elif classification == "competitive":
            findings.append("Proposed fee is broadly aligned with available benchmark evidence.")
        elif classification == "below_benchmark":
            findings.append("Proposed fee is below available benchmark evidence.")

        if benchmark_status == "insufficient_data":
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
            inputs_used={
                "current_fee": current_fee,
                "proposed_fee": proposed_fee,
                "benchmark_fee": explicit_benchmark_fee,
                "benchmark_comparators": comparators,
            },
            analysis={
                "benchmark_status": benchmark_status,
                "comparator_count": len(valid_comparators),
                "gcc_or_regional_comparator_count": gcc_count,
                "international_comparator_count": international_count,
                "average_benchmark_fee": avg_fee,
                "reference_benchmark_fee": explicit_benchmark_fee if explicit_benchmark_fee is not None else avg_fee,
                "classification": classification,
                "competitiveness_risk": classification in {"slightly_above_benchmark", "significantly_above_benchmark"},
                "comparator_summary": valid_comparators,
            },
            findings=findings or ["Benchmark evidence is not sufficient for a reliable comparison."],
            missing_data=missing,
            service_owner_questions=questions,
            recommendation="Validate benchmark evidence before final approval." if missing else "Benchmark evidence supports continuation with documented assumptions.",
            next_stage="scenarios",
            can_continue=True,
            blocks_final_approval=status == "insufficient_data",
        )
