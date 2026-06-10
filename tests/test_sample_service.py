import json
from pathlib import Path

from agents.orchestrator import JourneyOrchestrator


def test_sample_service_loads_and_full_journey_runs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    service_path = Path(__file__).resolve().parents[1] / "data" / "sample_service.json"
    service = json.loads(service_path.read_text(encoding="utf-8"))

    outputs = JourneyOrchestrator().run_all(service)
    final = outputs["final"]

    assert service["service_id"] == "SRV-001"
    assert outputs["costing"]["analysis"]["total_cost"] == 4200000
    assert final["recommendation"]
    assert final["recommendation"] == "Recommended with conditions"
