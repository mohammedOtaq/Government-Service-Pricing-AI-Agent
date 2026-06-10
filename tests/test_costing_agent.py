from agents.costing_agent import CostingAgent


def test_costing_agent_sample_calculations():
    service = {
        "service_id": "SRV-001",
        "direct_cost": 2800000,
        "indirect_cost": 1400000,
        "annual_transactions": 12000,
        "current_fee": 500,
        "proposed_fee": 450,
        "third_party_fee": 20,
        "other_mandatory_charges": 10,
    }
    output = CostingAgent().run(service).to_state()
    analysis = output["analysis"]

    assert analysis["total_cost"] == 4200000
    assert analysis["unit_cost"] == 350
    assert analysis["current_annual_revenue"] == 6000000
    assert analysis["proposed_annual_revenue"] == 5400000
    assert analysis["revenue_difference"] == -600000
    assert round(analysis["cost_recovery_ratio"], 4) == 1.2857
    assert analysis["total_customer_cost"] == 480
    assert output["status"] == "completed"


def test_costing_agent_blocks_zero_transactions():
    output = CostingAgent().run({
        "service_id": "SRV-002",
        "direct_cost": 100,
        "indirect_cost": 50,
        "annual_transactions": 0,
        "current_fee": 10,
        "proposed_fee": 12,
    }).to_state()

    assert output["status"] == "blocked"
    assert output["blocks_final_approval"] is True
    assert "Provide annual transaction volume greater than zero." in output["service_owner_questions"]
