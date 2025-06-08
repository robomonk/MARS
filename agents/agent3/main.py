# agents/agent3/main.py
from fastapi import FastAPI, HTTPException
from typing import List, Optional # Ensure these are imported if models use them
import uuid
from .models import AbstractProtocol, BuildPlan, FeasibilityResponse, ConfirmationStatus, BuildStep
from .plan_translator import translate_protocol_to_build_plan
from .state_manager import global_state_manager

app = FastAPI(title="Agent 3: Experiment Builder")

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

    success = global_state_manager.update_plan_status(plan_id, 'execution_started')
    if not success:
        # This case implies the plan was deleted between get and update, or another issue.
        raise HTTPException(status_code=500, detail="Failed to update plan status for execution, plan may have been modified or deleted.")

    return {"message": "Build plan execution started", "plan_id": plan_id, "new_status": "execution_started"}

# Placeholder for root path or API documentation
@app.get("/")
async def root():
    return {"message": "Agent 3: Experiment Builder. See /docs for API details."}
