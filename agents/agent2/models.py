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

class Protocol(BaseModel):
    protocol_id: str
    linked_hypothesis_id: str
    validation_steps: List[Dict[str, Any]] # Each dict could represent a step with details
    feasibility_assessment: "FeasibilityAssessment" # Use forward reference
    status: str = "draft" # e.g., draft, active, completed, aborted
    estimated_cost: float = 0.0
    estimated_duration: str = "N/A" # e.g., "2 weeks"
    actual_results: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class FeasibilityAssessment(BaseModel):
    data_obtainability: Literal['PUBLIC', 'PRIVATE', 'UNAVAILABLE']
    tools_availability: Literal['OPEN_SOURCE', 'COMMERCIAL', 'REQUIRES_DEVELOPMENT']
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    summary: str
