import uuid
from .models import Hypothesis, Protocol, ValidationStep, FeasibilityAssessment # Added ValidationStep and FeasibilityAssessment

def decompose_hypothesis(hypothesis: Hypothesis) -> list[str]:
    """
    Decomposes a hypothesis into its key premises.
    Placeholder implementation.
    """
    premises = []
    premises.extend(hypothesis.core_assumptions)
    # Basic decomposition of the main statement (can be improved)
    if '.' in hypothesis.statement:
        premises.extend([s.strip() for s in hypothesis.statement.split('.') if s.strip()])
    else:
        premises.append(hypothesis.statement)
    # Remove duplicates and filter out empty strings
    return list(filter(None, set(premises)))

def generate_protocol(hypothesis_id: str, premises: list[str]) -> Protocol:
    """
    Generates an experimental protocol based on key premises.
    """
    validation_steps = []
    for i, premise in enumerate(premises):
        validation_steps.append(
            ValidationStep(
                step_id=f"step_{i+1}",
                description=f"Test premise: {premise}",
                # status is "PENDING" by default
                # results is "" by default
            )
        )

    # Define a default FeasibilityAssessment
    default_feasibility = FeasibilityAssessment(
        data_obtainability='UNAVAILABLE', # Default value
        tools_availability='REQUIRES_DEVELOPMENT', # Default value
        confidence_score=0.1, # Default low confidence
        summary='Initial feasibility assessment pending detailed analysis.' # Default summary
    )

    return Protocol(
        protocol_id=str(uuid.uuid4()),
        linked_hypothesis_id=hypothesis_id,
        validation_steps=validation_steps, # Now a list of ValidationStep objects
        feasibility_assessment=default_feasibility # Proper FeasibilityAssessment object
    )
