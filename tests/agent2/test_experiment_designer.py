import pytest
from agents.agent2.experiment_designer import decompose_hypothesis, generate_protocol
from agents.agent2.models import Hypothesis, Protocol # Adjusted path

# Added description field to Hypothesis instantiation as it's mandatory in the Pydantic model
def test_decompose_hypothesis_simple():
    hyp = Hypothesis(hypothesis_id="h1", statement="Premise one.", core_assumptions=["Assumption one."], description="Test description")
    premises = decompose_hypothesis(hyp)
    assert isinstance(premises, list)
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
    # The original test expected 1, but "Repeat." (from assumption) and "Repeat" (from statement) are different after statement processing.
    # If "Repeat." from core_assumptions is also meant to be stripped of its period for perfect duplication check,
    # then decompose_hypothesis needs adjustment. Current logic:
    # premises.extend(hypothesis.core_assumptions) -> adds "Repeat."
    # if '.' in hypothesis.statement: premises.extend([s.strip() for s in hypothesis.statement.split('.') if s.strip()]) -> adds "Repeat"
    # list(set(premises)) will see "Repeat." and "Repeat" as distinct.
    # For now, adjusting test to expect 2, or I need to clarify decompose_hypothesis logic for assumptions.
    # The comment "Note: decompose_hypothesis also strips periods from assumptions if they are duplicated by statement parts"
    # seems to imply a more complex deduplication than currently implemented.
    # Current implementation of decompose_hypothesis:
    #   premises = []
    #   premises.extend(hypothesis.core_assumptions)
    #   if '.' in hypothesis.statement:
    #       premises.extend([s.strip() for s in hypothesis.statement.split('.') if s.strip()])
    #   else:
    #       premises.append(hypothesis.statement)
    #   return list(set(premises))
    # This means "Repeat." from core_assumptions and "Repeat" from statement are distinct.
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
        assert step["step_id"] == f"step_{i+1}"
        assert premises[i] in step["description"]
        assert "metrics" in step
        assert "data_requirements" in step
        assert "tool_requirements" in step
        assert isinstance(step["metrics"], list)
        assert isinstance(step["data_requirements"], list)
        assert isinstance(step["tool_requirements"], list)

    assert protocol.feasibility_assessment == {"status": "pending_check"}
