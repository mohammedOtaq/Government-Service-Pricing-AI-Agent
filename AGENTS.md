# AGENTS.md

## Project Name
Government Service Pricing AI Prototype

## Purpose
This project is a local Mac prototype for an AI-assisted government service pricing model. The app uses Streamlit, Python, and SQLite. It must support a modular multi-agent workflow where each agent produces an independent evidence report and the final agent consolidates the evidence into a recommendation.

## Completed Phases
- Phase 1: Local Mac prototype using Streamlit + Python + SQLite
- Phase 2: Codex and Claude Code available

## Pending Phases
- Phase 3: Add multi-agent logic
- Phase 4: Test with one government service
- Phase 5: Prepare Streamlit Cloud deployment

## Technology Stack
Use:
- Python 3.11+
- Streamlit
- SQLite
- Pandas
- Pydantic where useful
- python-dotenv
- Local JSON/Markdown files for reports and state

Avoid:
- Kubernetes
- Docker unless absolutely necessary
- Heavy enterprise architecture
- Unnecessary external APIs
- Hardcoded secrets
- Over-complicated orchestration frameworks

## Domain Methodology
The prototype supports government service pricing analysis. The logic must consider:
- Value-added service assessment
- Clear beneficiary
- Legal authority or policy justification
- Fee collectability
- Direct costs
- Indirect costs
- Unit cost
- Current fee
- Proposed fee
- Annual transactions
- Current annual revenue
- Proposed annual revenue
- Cost recovery
- Customer journey cost
- Third-party charges
- Other mandatory charges
- Benchmarking
- Renewal period
- Duplication risk
- Automation level
- Processing time
- What-if scenarios
- Financial impact on government
- Financial impact on customers
- Economic, social, and environmental impact where available
- Risks and mitigation
- Business case justification

## Mandatory Principle
The final recommendation must not be a black-box AI answer. It must be evidence-based. Each agent creates evidence. The final recommendation is only as strong as the evidence collected.

## Required Journey Stages
1. Service Intake Agent
2. Policy Compliance Agent
3. Costing Agent
4. Benchmark Agent
5. Scenario Agent
6. Risk and Impact Agent
7. Business Case Agent
8. Final Recommendation Agent

## Required Reports
The prototype should be able to generate up to 8 reports:
1. Service Profile Report
2. Policy Assessment Report
3. Costing Analysis Report
4. Benchmark Report
5. What-if Scenario Report
6. Risk and Impact Report
7. Draft Business Case Report
8. Consolidated Final Recommendation Report

## Standard Agent Output
Every agent must return the same standard output structure:

{
  "agent_name": "",
  "stage": "",
  "status": "",
  "service_id": "",
  "inputs_used": {},
  "analysis": {},
  "findings": [],
  "missing_data": [],
  "service_owner_questions": [],
  "recommendation": "",
  "next_stage": "",
  "can_continue": true,
  "blocks_final_approval": false
}

## Valid Status Values
Use only:
- not_started
- in_progress
- completed
- completed_with_gaps
- requires_service_owner_input
- blocked
- approved_for_next_stage
- insufficient_data
- non_compliant

## Governance Rule
The journey may continue with gaps, but final approval must be blocked if critical evidence is missing.

## Report Format
Each stage should generate:
1. Markdown report for human review
2. JSON state file for resuming the journey

Example:
- benchmark_report.md
- benchmark_state.json

## Resume Rule
The user must be able to upload a previous JSON state file. The app should validate it, update the journey progress, and allow continuation from the next stage.

## Benchmark Rule
The Benchmark Agent may conduct benchmark analysis only using available data. It must not invent benchmark prices, countries, fees, processing times, or renewal periods. If data is missing, it must generate service owner questions.

Each benchmark comparator should include a `region` field using one of:
- `gcc`
- `regional`
- `international`
- `unknown`

The optional field `benchmark_limitation_justification` may be used when benchmark evidence is incomplete but the service owner provides a documented reason why direct comparison is limited. This field does not automatically approve the fee. It only explains benchmark limitations and may support conditional review.

## Testing Rule
Before completing work, run:
- python -m compileall .
- pytest if installed

If tests cannot run, explain why.

## Final Output Expected
At the end, provide:
1. Files changed
2. New workflow summary
3. How to run locally
4. How to test
5. How to use the staged reports
6. Known limitations
7. Next recommended step
