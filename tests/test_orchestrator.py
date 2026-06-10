from agents.orchestrator import JourneyOrchestrator


def test_run_all_stops_when_stage_cannot_continue():
    service = {
        "service_id": "SRV-BLOCK",
        "service_name": "Blocked Service",
        "service_type": "Administrative",
        "service_description": "A service without an owner should stop at intake.",
        "customer_segment": "Companies",
    }

    outputs = JourneyOrchestrator().run_all(service)

    assert outputs["service_profile"]["can_continue"] is False
    assert "_journey_warning" in outputs
    assert outputs["_journey_warning"]["stage"] == "service_profile"
    assert "policy" not in outputs
