from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal

class Hypothesis(BaseModel):
    hypothesis_id: str
    statement: str  # Primary field for `decompose_hypothesis`
    core_assumptions: List[str] = Field(default_factory=list) # Primary field for `decompose_hypothesis`
    description: str # Kept as per previous work, can be used for additional details
    status: str = "pending" # e.g., pending, validated, rejected
    evaluation_metrics: List[str] = Field(default_factory=list)
    data_sources: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ValidationStep(BaseModel):
    step_id: str
    description: str
    status: str = "PENDING"  # Default status
    results: str = ""        # To store outcomes or findings for the step

class Protocol(BaseModel):
    protocol_id: str
    linked_hypothesis_id: str
    validation_steps: List[ValidationStep] # Changed from List[Dict[str, Any]]
    feasibility_assessment: "FeasibilityAssessment" # Use forward reference
    status: str = "draft" # e.g., draft, active, completed, aborted
    estimated_cost: float = 0.0
    estimated_duration: str = "N/A" # e.g., "2 weeks"
    actual_results: List[Dict[str, Any]] = Field(default_factory=list) # Or perhaps List[ValidationStepResult]? For now, keeping as dict.
    metadata: Dict[str, Any] = Field(default_factory=dict)

class FeasibilityAssessment(BaseModel):
    data_obtainability: Literal['PUBLIC', 'PRIVATE', 'UNAVAILABLE']
    tools_availability: Literal['OPEN_SOURCE', 'COMMERCIAL', 'REQUIRES_DEVELOPMENT']
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    summary: str

# To handle the forward reference once all models are defined (if FeasibilityAssessment were defined after Protocol)
# Protocol.update_forward_refs() # Not strictly necessary here as FeasibilityAssessment is defined above Protocol's use of it.
# However, if Protocol was defined before FeasibilityAssessment, this would be needed.
# For self-references or circular dependencies, this is crucial.
# In this specific order, it's not an issue.
# FeasibilityAssessment.update_forward_refs() # If it had forward refs
# Hypothesis.update_forward_refs()
# ValidationStep.update_forward_refs()
