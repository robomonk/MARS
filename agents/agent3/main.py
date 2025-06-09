# agents/agent3/main.py
from fastapi import FastAPI, HTTPException
from typing import List, Optional # Ensure these are imported if models use them
import uuid
import os # For environment variables

from .models import AbstractProtocol, BuildPlan, FeasibilityResponse, ConfirmationStatus, BuildStep, ExecutionError # Add ExecutionError
from .plan_translator import translate_protocol_to_build_plan
from .state_manager import global_state_manager
from .execution_engine import execute_build_step # Import the new function

app = FastAPI(title="Agent 3: Experiment Builder")

# Retrieve GCP Project ID and Location from environment variables
# These would need to be set in the environment where Agent 3 runs.
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "your-gcp-project-id") # Add a default for local testing if not set
GCP_LOCATION = os.getenv("GCP_LOCATION", "your-gcp-location")     # e.g., "us-central1"

@app.post("/check_build_feasibility", response_model=FeasibilityResponse)
async def check_build_feasibility(protocol_snippet: dict): # Simplified input for now
    # In future, this might take specific parts of a protocol to check
    # For now, static response as per requirements
    return FeasibilityResponse(status='FEASIBLE')

@app.post("/receive_experiment_protocol", response_model=BuildPlan)
async def receive_experiment_protocol(protocol: AbstractProtocol):
    plan = translate_protocol_to_build_plan(protocol)
    global_state_manager.store_build_plan(plan)
    return plan

@app.get("/build_plan/{plan_id}", response_model=BuildPlan)
async def get_build_plan_endpoint(plan_id: str): # Renamed to avoid conflict
    plan = global_state_manager.get_build_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Build plan not found")
    return plan

@app.post("/build_plan/{plan_id}/confirm", response_model=ConfirmationStatus)
async def confirm_build_plan_endpoint(plan_id: str): # Renamed
    # In a real system, this might require authentication/authorization
    success = global_state_manager.update_plan_status(plan_id, 'approved')
    if not success:
        raise HTTPException(status_code=404, detail="Build plan not found for confirmation")
    return ConfirmationStatus(plan_id=plan_id, confirmed=True, message="Build plan approved by user.")

@app.post("/build_plan/{plan_id}/execute")
async def execute_build_plan_endpoint(plan_id: str):
    plan = global_state_manager.get_build_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Build plan not found for execution")

    # Only allow execution if the plan is in 'approved' state
    if plan.status != 'approved':
        raise HTTPException(status_code=400, detail=f"Build plan must be in 'approved' state to execute. Current status: {plan.status}")

    if not GCP_PROJECT_ID or GCP_PROJECT_ID == "your-gcp-project-id":
        global_state_manager.update_plan_status(plan_id, 'failed')
        raise HTTPException(status_code=500, detail="GCP_PROJECT_ID is not configured. Cannot execute plan.")
    if not GCP_LOCATION or GCP_LOCATION == "your-gcp-location":
        global_state_manager.update_plan_status(plan_id, 'failed')
        raise HTTPException(status_code=500, detail="GCP_LOCATION is not configured. Cannot execute plan.")

    global_state_manager.update_plan_status(plan_id, 'execution_started')

    # Ensure plan.error_details is reset if plan is re-executed (optional, depends on desired behavior)
    # plan.error_details = None # Uncomment if errors should be cleared on new execution attempt
    # global_state_manager.store_build_plan(plan) # Persist the cleared error

    for step_index, step in enumerate(plan.steps):
        success = execute_build_step(step, project_id=GCP_PROJECT_ID, location=GCP_LOCATION)
        if not success:
            global_state_manager.update_plan_status(plan_id, 'failed')

            error_info = ExecutionError(
                step_index=step_index,
                step_name=step.name,
                step_type=step.type,
                message=f"Execution failed at step {step_index + 1}: {step.action} {step.type} {step.name}"
            )
            plan.status = 'failed'
            plan.error_details = error_info # Assign the structured error
            global_state_manager.store_build_plan(plan) # Re-store plan to save error details

            # The HTTPException detail can be the dict representation of error_info for client consumption
            raise HTTPException(status_code=500, detail=error_info.model_dump())

    global_state_manager.update_plan_status(plan_id, 'completed')
    plan.error_details = None # Clear any previous error details on successful completion
    global_state_manager.store_build_plan(plan) # Persist the cleared error state
    return {"message": "Build plan executed successfully", "plan_id": plan_id, "new_status": "completed"}

@app.get("/")
async def root():
    return {"message": "Agent 3: Experiment Builder. See /docs for API details."}
