# agents/agent3/state_manager.py
from typing import Dict, Optional
from .models import BuildPlan

class StateManager:
    def __init__(self):
        self._build_plans: Dict[str, BuildPlan] = {}

    def store_build_plan(self, plan: BuildPlan):
        self._build_plans[plan.plan_id] = plan

    def get_build_plan(self, plan_id: str) -> Optional[BuildPlan]:
        return self._build_plans.get(plan_id)

    def update_plan_status(self, plan_id: str, status: str) -> bool:
        plan = self.get_build_plan(plan_id)
        if plan:
            plan.status = status
            # Pydantic models are mutable, so the object in the dict is updated directly.
            # If it were a non-mutable type, we'd need: self.store_build_plan(plan)
            return True
        return False

# Global instance for simplicity in this example
global_state_manager = StateManager()
