import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, ANY

from agents.agent2.main import app # Assuming app is in main
from agents.agent2.models import Hypothesis, FeasibilityAssessment, Protocol, ValidationStep

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def sample_hypothesis_data():
    return {
        "hypothesis_id": "test_hyp_001",
        "statement": "If we increase user engagement, then product adoption will increase.",
        "core_assumptions": [
            "Users find the new features engaging.",
            "Increased engagement directly translates to trying more product features."
        ],
        "description": "A sample hypothesis for testing."
    }

@pytest.fixture
def sample_hypothesis(sample_hypothesis_data):
    return Hypothesis(**sample_hypothesis_data)

def test_hypothesis_parsing(client, sample_hypothesis, sample_hypothesis_data):
    mocked_premises_for_simple_test = [
        "Premise 1: New features are engaging.",
        "Premise 2: Engagement leads to feature exploration.",
        "Premise 3: Feature exploration leads to adoption."
    ]
    with patch('agents.agent2.main.decompose_hypothesis') as mock_decompose:
        mock_decompose.return_value = mocked_premises_for_simple_test
        response = client.post("/design_experiment/", json=sample_hypothesis_data)
        assert response.status_code == 200, response.text
        mock_decompose.assert_called_once()
        called_args, _ = mock_decompose.call_args
        assert called_args[0].model_dump() == sample_hypothesis.model_dump()
        response_json = response.json()
        assert "protocol_id" in response_json
        expected_structured_steps = sorted(
            [{"step_id": ANY, "description": f"Test premise: {p}", "status": "PENDING", "results": ""}
             for p in mocked_premises_for_simple_test],
            key=lambda x: x["description"]
        )
        actual_steps_sorted = sorted(response_json.get("validation_steps", []), key=lambda x: x["description"])
        assert actual_steps_sorted == expected_structured_steps

def test_tool_use_mocking(client):
    hypothesis_payload = {
        "hypothesis_id": "hyp_tool_test",
        "statement": "Statement for tool test. Second part of statement.",
        "core_assumptions": ["Assumption for tool test"],
        "description": "Tool use test description"
    }
    expected_raw_premises_tool_test = {"Statement for tool test", "Second part of statement", "Assumption for tool test"}
    expected_json_validation_steps_tool_test = sorted(
        [{"step_id": ANY, "description": f"Test premise: {p}", "status": "PENDING", "results": ""}
         for p in expected_raw_premises_tool_test],
        key=lambda x: x["description"]
    )
    expected_queries = []
    for p in expected_raw_premises_tool_test:
         expected_queries.extend([
            f"Public datasets for Test premise: {p}",
            f"Python libraries for Test premise: {p}",
            f"Availability of computational model for Test premise: {p}"
        ])
    mock_search_results = {query: "mocked_no_result" for query in expected_queries}
    mock_search_results["Public datasets for Test premise: Statement for tool test"] = "Found public dataset XYZ."
    mock_search_results["Python libraries for Test premise: Statement for tool test"] = "Found library ABC."

    with patch('agents.agent2.collaboration.fetch_external_data') as mock_fetch_external_data:
        mock_fetch_external_data.return_value = mock_search_results
        response = client.post("/design_experiment/", json=hypothesis_payload)
        assert response.status_code == 200, response.text

        mock_fetch_external_data.assert_called_once()
        called_args_tuple, _ = mock_fetch_external_data.call_args
        assert isinstance(called_args_tuple[0], list)
        assert set(called_args_tuple[0]) == set(expected_queries)

        response_json = response.json()
        assessment = response_json["feasibility_assessment"]
        assert assessment["data_obtainability"] == "PUBLIC"
        assert assessment["tools_availability"] == "OPEN_SOURCE"
        assert assessment["confidence_score"] == 0.8
        actual_steps_sorted = sorted(response_json.get("validation_steps", []), key=lambda x: x["description"])
        assert actual_steps_sorted == expected_json_validation_steps_tool_test

def test_collaboration_mocks_success(client):
    hypothesis_payload = {
        "hypothesis_id": "hyp_collab_test",
        "statement": "Collab statement.",
        "core_assumptions": ["Collab assumption"],
        "description": "Collab success test description"
    }
    expected_raw_premises_set = {"Collab statement", "Collab assumption"}
    expected_json_validation_steps = sorted(
        [{"step_id": ANY, "description": f"Test premise: {p}", "status": "PENDING", "results": ""}
         for p in expected_raw_premises_set],
        key=lambda x: x["description"]
    )
    mock_feasibility_assessment_obj = FeasibilityAssessment(
        data_obtainability='PUBLIC', tools_availability='OPEN_SOURCE',
        confidence_score=0.75, summary='Mocked feasibility assessment for collaboration test'
    )

    with patch('agents.agent2.main.confirm_protocol_with_hypothesizer') as mock_confirm, \
         patch('agents.agent2.main.check_build_feasibility') as mock_feasibility:

        mock_confirm.return_value = True
        mock_feasibility.return_value = mock_feasibility_assessment_obj

        response = client.post("/design_experiment/", json=hypothesis_payload)
        assert response.status_code == 200, response.text

        mock_confirm.assert_called_once()
        args_confirm, _ = mock_confirm.call_args
        protocol_to_confirm = args_confirm[0]
        assert isinstance(protocol_to_confirm, Protocol)
        assert protocol_to_confirm.linked_hypothesis_id == hypothesis_payload["hypothesis_id"]

        actual_descriptions = sorted([s.description for s in protocol_to_confirm.validation_steps])
        expected_descriptions = sorted([f"Test premise: {p}" for p in expected_raw_premises_set])
        assert actual_descriptions == expected_descriptions
        for step_obj in protocol_to_confirm.validation_steps:
            assert isinstance(step_obj, ValidationStep)
            assert step_obj.step_id is not None and isinstance(step_obj.step_id, str)
            assert step_obj.status == "PENDING"

        mock_feasibility.assert_called_once_with(
            validation_steps=protocol_to_confirm.validation_steps,
            linked_hypothesis_id=hypothesis_payload["hypothesis_id"]
        )

        response_data = response.json()
        assert response_data["protocol_id"] == protocol_to_confirm.protocol_id
        actual_response_steps_sorted = sorted(response_data["validation_steps"], key=lambda x: x["description"])
        assert actual_response_steps_sorted == expected_json_validation_steps
        assert response_data["feasibility_assessment"] == mock_feasibility_assessment_obj.model_dump()
        # Aligning with current SUT behavior where status is not updated from "draft"
        assert response_data.get("status") == "draft"

def test_collaboration_confirmation_fails(client):
    hypothesis_payload = {
        "hypothesis_id": "hyp_collab_fail_test",
        "statement": "Collab fail statement.",
        "core_assumptions": ["Collab fail assumption"],
        "description": "Collab fail test description"
    }
    expected_raw_premises_set_fail = {"Collab fail statement", "Collab fail assumption"}

    with patch('agents.agent2.main.confirm_protocol_with_hypothesizer') as mock_confirm_fail, \
         patch('agents.agent2.main.check_build_feasibility') as mock_feasibility_not_called:

        mock_confirm_fail.return_value = False
        response_fail = client.post("/design_experiment/", json=hypothesis_payload)
        assert response_fail.status_code == 503
        assert response_fail.json() == {"detail": "Protocol confirmation failed with Agent 1."}

        mock_confirm_fail.assert_called_once()
        args_confirm_fail, _ = mock_confirm_fail.call_args
        protocol_to_confirm_fail = args_confirm_fail[0]
        assert isinstance(protocol_to_confirm_fail, Protocol)

        actual_descriptions_fail = sorted([s.description for s in protocol_to_confirm_fail.validation_steps])
        expected_descriptions_fail = sorted([f"Test premise: {p}" for p in expected_raw_premises_set_fail])
        assert actual_descriptions_fail == expected_descriptions_fail
        for step_obj in protocol_to_confirm_fail.validation_steps:
            assert isinstance(step_obj, ValidationStep)
            assert step_obj.step_id is not None and isinstance(step_obj.step_id, str)
            assert step_obj.status == "PENDING"

        mock_feasibility_not_called.assert_not_called()
