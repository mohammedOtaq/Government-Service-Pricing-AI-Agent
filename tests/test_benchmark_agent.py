from agents.benchmark_agent import BenchmarkAgent


def test_benchmark_agent_with_data_flags_competitiveness_risk():
    output = BenchmarkAgent().run({
        "service_id": "SRV-001",
        "current_fee": 500,
        "proposed_fee": 470,
        "benchmark_comparators": [
            {"jurisdiction_or_country": "Comparator 1", "region": "gcc", "fee_amount": 430, "source_or_evidence": "source"},
            {"jurisdiction_or_country": "Comparator 2", "region": "regional", "fee_amount": 440, "source_or_evidence": "source"},
            {"jurisdiction_or_country": "Comparator 3", "region": "international", "fee_amount": 400, "source_or_evidence": "source"},
        ],
    }).to_state()

    assert output["status"] == "completed"
    assert output["analysis"]["benchmark_status"] == "completed"
    assert output["analysis"]["competitiveness_risk"] is True
    assert output["analysis"]["classification"] == "slightly_above_benchmark"


def test_benchmark_agent_missing_data_generates_questions():
    output = BenchmarkAgent().run({
        "service_id": "SRV-002",
        "current_fee": 100,
        "proposed_fee": 120,
    }).to_state()

    assert output["status"] == "insufficient_data"
    assert output["analysis"]["benchmark_status"] == "insufficient_data"
    assert output["analysis"]["classification"] == "benchmark_missing"
    assert len(output["service_owner_questions"]) >= 10
    assert output["blocks_final_approval"] is True
