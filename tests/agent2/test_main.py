import pytest
from fastapi.testclient import TestClient
from agents.agent2.main import app
from agents.agent2.models import Hypothesis, Protocol # Adjusted path

client = TestClient(app)

def test_design_experiment_endpoint_success():
    hypothesis_payload = {
        "hypothesis_id": "hyp_main_001",
        "statement": "If sunlight exposure increases, plant growth will accelerate. This is observable.",
        "core_assumptions": ["Sunlight provides energy for photosynthesis.", "The plant is healthy."],
        "description": "A test hypothesis regarding plant growth and sunlight." # Added mandatory description
    }
    response = client.post("/design_experiment/", json=hypothesis_payload)

    assert response.status_code == 200
    protocol_data = response.json()

    assert "protocol_id" in protocol_data
    assert protocol_data["linked_hypothesis_id"] == "hyp_main_001"
    assert "validation_steps" in protocol_data
    assert isinstance(protocol_data["validation_steps"], list)

    # Check if premises from statement and core_assumptions are in validation steps descriptions
    # Original statement parts: "If sunlight exposure increases, plant growth will accelerate", "This is observable"
    # Core assumptions: "Sunlight provides energy for photosynthesis.", "The plant is healthy."
    # Expected decomposed unique premises:
    expected_premises_in_steps = {
        "If sunlight exposure increases, plant growth will accelerate",
        "This is observable",
        "Sunlight provides energy for photosynthesis.", # Retains period from assumption
        "The plant is healthy." # Retains period from assumption
    }
    assert len(protocol_data["validation_steps"]) == len(expected_premises_in_steps)


    found_in_steps_count = 0
    step_descriptions = [step['description'] for step in protocol_data["validation_steps"]]

    for expected_premise in expected_premises_in_steps:
        found = False
        for desc in step_descriptions:
            if expected_premise in desc: # Check if the exact premise is part of the step description
                found = True
                break
        if found:
            found_in_steps_count +=1

    assert found_in_steps_count == len(expected_premises_in_steps), \
        f"Expected {len(expected_premises_in_steps)} premises to be represented in step descriptions, but found {found_in_steps_count}"


    assert "feasibility_assessment" in protocol_data
    # Default feasibility from placeholder:
    assert protocol_data["feasibility_assessment"]["feasible"] == True
    assert "details" in protocol_data["feasibility_assessment"]

def test_design_experiment_endpoint_empty_hypothesis():
    # Test with a hypothesis that might result in no key premises
    hypothesis_payload = {
        "hypothesis_id": "hyp_empty_002",
        "statement": "",
        "core_assumptions": [],
        "description": "An empty hypothesis for testing." # Added mandatory description
    }
    response = client.post("/design_experiment/", json=hypothesis_payload)

    # This should result in an error because decompose_hypothesis would return empty
    assert response.status_code == 400
    assert "Could not extract key premises" in response.json()["detail"]

def test_design_experiment_endpoint_invalid_payload():
    # Missing required fields (e.g. statement, description, core_assumptions)
    response = client.post("/design_experiment/", json={"hypothesis_id": "test_only_id"})
    assert response.status_code == 422 # Unprocessable Entity for Pydantic validation error
