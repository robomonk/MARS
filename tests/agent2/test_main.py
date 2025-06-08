import pytest
from fastapi.testclient import TestClient
from agents.agent2.main import app
from agents.agent2.models import Hypothesis, Protocol

client = TestClient(app)

def test_design_experiment_endpoint_success():
    hypothesis_payload = {
        "hypothesis_id": "hyp_main_001",
        "statement": "If sunlight exposure increases, plant growth will accelerate. This is observable.",
        "core_assumptions": ["Sunlight provides energy for photosynthesis.", "The plant is healthy."],
        "description": "A test hypothesis regarding plant growth and sunlight."
    }
    response = client.post("/design_experiment/", json=hypothesis_payload)

    assert response.status_code == 200, response.text
    protocol_data = response.json()

    assert "protocol_id" in protocol_data
    assert protocol_data["linked_hypothesis_id"] == "hyp_main_001"
    assert "validation_steps" in protocol_data
    assert isinstance(protocol_data["validation_steps"], list)

    expected_premises_in_steps = {
        "If sunlight exposure increases, plant growth will accelerate",
        "This is observable",
        "Sunlight provides energy for photosynthesis.",
        "The plant is healthy."
    }
    assert len(protocol_data["validation_steps"]) == len(expected_premises_in_steps)

    step_descriptions = {step['description'] for step in protocol_data["validation_steps"]}
    for expected_premise in expected_premises_in_steps:
        assert any(expected_premise in full_desc for full_desc in step_descriptions)

    assert "feasibility_assessment" in protocol_data
    # This test calls the actual check_build_feasibility, which (without specific mocks for fetch_external_data)
    # will result in default findings (no "Found " in results from the default fetch_external_data).
    actual_assessment = protocol_data["feasibility_assessment"]
    assert actual_assessment["data_obtainability"] == 'UNAVAILABLE' # Default from no "Found " in data queries
    assert actual_assessment["tools_availability"] == 'REQUIRES_DEVELOPMENT' # Default from no "Found " in tool queries
    assert actual_assessment["confidence_score"] == 0.5 # Base 0.5, no positive findings for data/tools
    assert "Feasibility assessment for Hypothesis ID: hyp_main_001" in actual_assessment["summary"]
    assert "Initial feasibility assessment pending detailed analysis." not in actual_assessment["summary"]
    # Check for part of the generated query summary
    assert "simulated_abstract_for_Public_datasets_for_Test_premise" in actual_assessment["summary"]


def test_design_experiment_endpoint_empty_hypothesis():
    hypothesis_payload = {
        "hypothesis_id": "hyp_empty_002",
        "statement": "",
        "core_assumptions": [],
        "description": "An empty hypothesis for testing."
    }
    response = client.post("/design_experiment/", json=hypothesis_payload)

    assert response.status_code == 400
    assert "Could not extract key premises" in response.json()["detail"]

def test_design_experiment_endpoint_invalid_payload():
    response = client.post("/design_experiment/", json={"hypothesis_id": "test_only_id"})
    assert response.status_code == 422
