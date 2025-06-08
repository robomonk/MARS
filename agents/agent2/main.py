from fastapi import FastAPI, HTTPException
# Removed pydantic import as models will handle it
import uuid
from .models import Hypothesis, Protocol # Added import

# Actual imports for models and functions
from .experiment_designer import decompose_hypothesis, generate_protocol
from .collaboration import confirm_protocol_with_hypothesizer, check_build_feasibility

# Removed local Pydantic model definitions

app = FastAPI()

# Functions are now imported from other modules.

@app.post("/design_experiment/", response_model=Protocol)
async def design_experiment_endpoint(hypothesis: Hypothesis):
    '''
    Accepts a hypothesis from Agent 1, decomposes it, generates an experiment protocol,
    and (simulates) communication with other agents.
    '''
    print(f"Received hypothesis: {hypothesis.hypothesis_id}")

    try:
        # 1. Decompose Hypothesis
        key_premises = decompose_hypothesis(hypothesis)
        if not key_premises:
            raise HTTPException(status_code=400, detail="Could not extract key premises from hypothesis.")
        print(f"Key premises: {key_premises}")

        # 2. Generate Protocol
        protocol = generate_protocol(hypothesis.hypothesis_id, key_premises)
        print(f"Generated protocol: {protocol.protocol_id}")

        # 3. Confirm Protocol with Hypothesizer (Agent 1) - Placeholder
        confirmation_status = confirm_protocol_with_hypothesizer(protocol)
        if not confirmation_status:
            # In a real system, might wait, retry, or escalate
            raise HTTPException(status_code=503, detail="Protocol confirmation failed with Agent 1.")
        print(f"Protocol confirmed with Agent 1: {confirmation_status}")

        # 4. Check Build Feasibility (Agent 3)
        # The check_build_feasibility function now takes validation_steps and linked_hypothesis_id
        # and returns a FeasibilityAssessment object.

        feasibility_assessment_obj = check_build_feasibility(
            validation_steps=protocol.validation_steps,
            linked_hypothesis_id=protocol.linked_hypothesis_id
        )
        protocol.feasibility_assessment = feasibility_assessment_obj # Assign the object directly

        print(f"Feasibility assessment for Hypothesis {protocol.linked_hypothesis_id}:")
        print(f"  Data Obtainability: {protocol.feasibility_assessment.data_obtainability}")
        print(f"  Tools Availability: {protocol.feasibility_assessment.tools_availability}")
        print(f"  Confidence Score: {protocol.feasibility_assessment.confidence_score}")
        print(f"  Summary: {protocol.feasibility_assessment.summary}")

        # Example: Check confidence score
        if protocol.feasibility_assessment.confidence_score < 0.5:
            print(f"Warning: Confidence score for experiment feasibility is low ({protocol.feasibility_assessment.confidence_score}).")
        # For now, we proceed regardless of the score, but this is where one might halt or adapt.

        return protocol

    except HTTPException as http_exc:
        # Re-raise HTTPExceptions to let FastAPI handle them
        raise http_exc
    except Exception as e:
        # Catch any other unexpected errors
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# To run this app (for local testing):
# uvicorn agents.agent2.main:app --reload --port 8001
