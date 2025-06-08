import pytest
from agents.agent2.experiment_designer import decompose_hypothesis, generate_protocol
from agents.agent2.models import Hypothesis, Protocol, ValidationStep, FeasibilityAssessment # Added ValidationStep, FeasibilityAssessment

# Added description field to Hypothesis instantiation as it's mandatory in the Pydantic model
def test_decompose_hypothesis_simple():
    hyp = Hypothesis(hypothesis_id="h1", statement="Premise one.", core_assumptions=["Assumption one."], description="Test description")
    premises = decompose_hypothesis(hyp)
    assert isinstance(premises, list)
    # Order is not guaranteed due to set usage in decompose_hypothesis
    assert len(premises) == 2
    assert "Premise one" in premises
    assert "Assumption one." in premises

def test_decompose_hypothesis_multiple_statements_and_assumptions():
    hyp = Hypothesis(
        hypothesis_id="h2",
        statement="First main point. Second main point.",
        core_assumptions=["Core A.", "Core B."],
        description="Test description"
    )
    premises = decompose_hypothesis(hyp)
    assert len(premises) == 4
    assert "First main point" in premises
    assert "Second main point" in premises
    assert "Core A." in premises
    assert "Core B." in premises

def test_decompose_hypothesis_no_period_statement():
    hyp = Hypothesis(hypothesis_id="h3", statement="Single idea", core_assumptions=["Single assumption"], description="Test description")
    premises = decompose_hypothesis(hyp)
    assert len(premises) == 2
    assert "Single idea" in premises
    assert "Single assumption" in premises

def test_decompose_hypothesis_duplicates():
    hyp = Hypothesis(hypothesis_id="h4", statement="Repeat. Repeat.", core_assumptions=["Repeat."], description="Test description")
    premises = decompose_hypothesis(hyp)
    # "Repeat." from core_assumptions and "Repeat" from statement are distinct.
    assert len(premises) == 2
    assert "Repeat" in premises
    assert "Repeat." in premises


def test_generate_protocol():
    hyp_id = "test_hyp_001"
    premises = ["Test premise 1", "Test premise 2"]
    protocol = generate_protocol(hypothesis_id=hyp_id, premises=premises)

    assert isinstance(protocol, Protocol)
    assert protocol.protocol_id is not None
    assert protocol.linked_hypothesis_id == hyp_id
    assert len(protocol.validation_steps) == 2

    for i, step in enumerate(protocol.validation_steps):
        assert isinstance(step, ValidationStep) # Check it's a ValidationStep object
        assert step.step_id == f"step_{i+1}"
        assert step.description == f"Test premise: {premises[i]}" # Exact match for description
        assert step.status == "PENDING" # Default status
        assert step.results == ""       # Default results

    # Check the default FeasibilityAssessment
    assert isinstance(protocol.feasibility_assessment, FeasibilityAssessment)
    assert protocol.feasibility_assessment.data_obtainability == 'UNAVAILABLE'
    assert protocol.feasibility_assessment.tools_availability == 'REQUIRES_DEVELOPMENT'
    assert protocol.feasibility_assessment.confidence_score == 0.1
    assert protocol.feasibility_assessment.summary == 'Initial feasibility assessment pending detailed analysis.'
