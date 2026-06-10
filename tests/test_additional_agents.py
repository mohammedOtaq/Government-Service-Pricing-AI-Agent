from agents.business_case_agent import BusinessCaseAgent
from agents.final_recommendation_agent import FinalRecommendationAgent
from agents.orchestrator import JourneyOrchestrator
from agents.policy_agent import PolicyComplianceAgent
from agents.risk_impact_agent import RiskImpactAgent
from agents.scenario_agent import ScenarioAgent
from agents.service_intake_agent import ServiceIntakeAgent
from models.agent_output import REQUIRED_AGENT_OUTPUT_KEYS, VALID_STATUSES


def assert_standard_output(output):
    assert REQUIRED_AGENT_OUTPUT_KEYS.issubset(output)
    assert output["status"] in VALID_STATUSES
    assert isinstance(output["can_continue"], bool)
    assert isinstance(output["blocks_final_approval"], bool)


def base_service():
    return {
        "service_id": "SRV-T",
        "service_name": "Test Service",
        "service_type": "Administrative",
        "service_owner": "Owner",
        "customer_segment": "Companies",
        "service_description": "A complete service description for testing purposes.",
        "is_recurring": True,
        "renewal_period_months": 12,
        "service_is_value_added": True,
        "clear_beneficiary": True,
        "legal_authority_available": True,
        "fee_collectable": True,
        "duplication_risk": "low",
        "renewal_justified": True,
        "customer_journey_reviewed": True,
        "benchmark_available": True,
        "direct_cost": 1000,
        "indirect_cost": 500,
        "annual_transactions": 10,
        "current_fee": 200,
        "proposed_fee": 180,
        "benchmark_fee": 170,
        "third_party_fee": 5,
        "other_mandatory_charges": 5,
        "automation_level_percentage": 60,
        "benchmark_comparators": [
            {"region": "gcc", "jurisdiction_or_country": "A", "fee_amount": 170, "source_or_evidence": "source"},
            {"region": "regional", "jurisdiction_or_country": "B", "fee_amount": 175, "source_or_evidence": "source"},
            {"region": "international", "jurisdiction_or_country": "C", "fee_amount": 165, "source_or_evidence": "source"},
        ],
    }


def test_service_intake_missing_owner_requires_input():
    service = base_service()
    service["service_owner"] = ""
    output = ServiceIntakeAgent().run(service).to_state()

    assert_standard_output(output)
    assert output["status"] == "requires_service_owner_input"
    assert output["can_continue"] is False
    assert output["blocks_final_approval"] is True


def test_policy_non_compliant_blocks_final_approval():
    service = base_service()
    service["service_is_value_added"] = False
    output = PolicyComplianceAgent().run(service).to_state()

    assert_standard_output(output)
    assert output["status"] == "non_compliant"
    assert output["can_continue"] is False
    assert output["blocks_final_approval"] is True


def test_scenario_agent_generates_distinct_fees():
    service = base_service()
    outputs = JourneyOrchestrator().run_all(service)
    scenario_output = outputs["scenarios"]
    fees = [item["proposed_fee"] for item in scenario_output["analysis"]["scenarios"]]

    assert_standard_output(scenario_output)
    assert len(set(fees)) == 3
    assert scenario_output["can_continue"] is True


def test_risk_impact_missing_impact_data_is_gap_not_blocker():
    service = base_service()
    output = RiskImpactAgent().run(service, {}).to_state()

    assert_standard_output(output)
    assert output["status"] == "completed_with_gaps"
    assert "economic_impact" in output["missing_data"]
    assert output["blocks_final_approval"] is False


def test_business_case_insufficient_without_key_evidence():
    service = base_service()
    output = BusinessCaseAgent().run(service, {}).to_state()

    assert_standard_output(output)
    assert output["status"] == "insufficient_data"
    assert output["can_continue"] is False
    assert output["blocks_final_approval"] is True


def test_final_recommendation_not_recommended_for_policy_blocker():
    service = base_service()
    service["service_is_value_added"] = False
    outputs = JourneyOrchestrator().run_all(service)
    final = FinalRecommendationAgent().run(service, outputs).to_state()

    assert_standard_output(final)
    assert final["recommendation"] == "Not recommended"
    assert final["blocks_final_approval"] is True
