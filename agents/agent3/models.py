# agents/agent3/models.py
from pydantic import BaseModel
from typing import Optional, List, Dict # Added Dict for variables in ExperimentData

# Original models from earlier steps (ensure they are compatible or updated)
class TestModel(BaseModel):
    id: int
    name: str

class ExperimentData(BaseModel):
    research_question: str
    hypotheses: List[str]
    variables: Dict[str, str]  # e.g., {"independent": "IV_name", "dependent": "DV_name"}
    experimental_design: str
    target_population: str
    sample_size: int
    materials_and_procedures: str
    data_analysis_plan: str

class ExperimentPlan(BaseModel):
    title: str
    introduction: str
    methods: Dict[str, str]
    expected_outcomes: str
    timeline: str

# Models defined/redefined by the latest setup script
class AbstractProtocol(BaseModel):
    protocol_id: str
    title: Optional[str] = None # Made title optional to match potential use in main.py
    research_question: Optional[str] = None # Made optional
    data_requirement: Optional[str] = None
    computation_steps: Optional[List[str]] = None

class BuildStep(BaseModel):
    action: str
    type: str
    name: str
    details: Optional[Dict] = None # Changed from dict to Dict

class ExecutionError(BaseModel): # New model for structured errors
    step_index: int
    step_name: str
    step_type: str
    message: str

class BuildPlan(BaseModel):
    plan_id: str
    protocol_id: str # Added by me in previous step, setup script also has it
    steps: List[BuildStep]
    status: str = 'pending_approval' # e.g., pending_approval, approved, failed, execution_started, completed
    error_details: Optional[ExecutionError] = None # Changed from error_message: Optional[str]

class FeasibilityResponse(BaseModel):
    status: str # e.g., FEASIBLE, NOT_FEASIBLE
    message: Optional[str] = None

class ConfirmationStatus(BaseModel):
    plan_id: str
    confirmed: bool
    message: Optional[str] = None
