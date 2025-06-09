# agents/agent3/test_main_execution.py
import unittest
from unittest.mock import patch, MagicMock, ANY
from fastapi.testclient import TestClient
import os

# Assuming main.py and models.py are in the same directory (agents/agent3)
from .main import app
from .models import BuildPlan, BuildStep, ExecutionError
from .state_manager import global_state_manager # direct import for manipulation

class TestMainExecutionEndpoint(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.plan_id = "test-plan-123"
        self.base_url = f"/build_plan/{self.plan_id}/execute"

        self.original_gcp_project_id = os.environ.get("GCP_PROJECT_ID")
        self.original_gcp_location = os.environ.get("GCP_LOCATION")

        os.environ["GCP_PROJECT_ID"] = "test-gcp-project"
        os.environ["GCP_LOCATION"] = "test-gcp-location"

        # Clear plans from previous tests
        global_state_manager._build_plans = {}


    def tearDown(self):
        if self.original_gcp_project_id is None:
            if "GCP_PROJECT_ID" in os.environ: del os.environ["GCP_PROJECT_ID"]
        else:
            os.environ["GCP_PROJECT_ID"] = self.original_gcp_project_id

        if self.original_gcp_location is None:
            if "GCP_LOCATION" in os.environ: del os.environ["GCP_LOCATION"]
        else:
            os.environ["GCP_LOCATION"] = self.original_gcp_location

        global_state_manager._build_plans = {}

    def _create_sample_plan(self, status='approved', steps=None):
        if steps is None:
            steps = [
                BuildStep(action="create_resource", type="gcs_bucket", name="my_bucket"),
                BuildStep(action="create_resource", type="bigquery_dataset", name="my_dataset")
            ]
        plan = BuildPlan(
            plan_id=self.plan_id,
            protocol_id="proto-1",
            steps=steps,
            status=status
        )
        global_state_manager.store_build_plan(plan)
        return plan

    def test_execute_plan_not_found(self):
        response = self.client.post(self.base_url)
        self.assertEqual(response.status_code, 404)
        self.assertIn("Build plan not found", response.json()["detail"])

    def test_execute_plan_not_approved(self):
        self._create_sample_plan(status='pending_approval')
        response = self.client.post(self.base_url)
        self.assertEqual(response.status_code, 400)
        self.assertIn("must be in 'approved' state", response.json()["detail"])

    @patch.dict(os.environ, {"GCP_PROJECT_ID": "", "GCP_LOCATION": "test-location"})
    def test_execute_plan_no_project_id(self):
        self._create_sample_plan()
        # Need to reload app or use a context manager for env var changes with TestClient
        # For simplicity, we assume TestClient picks up env changes if set before endpoint call.
        # More robust testing might involve re-instantiating TestClient or app context.
        with patch.dict(os.environ, {"GCP_PROJECT_ID": "", "GCP_LOCATION": "test-gcp-location"}):
            response = self.client.post(self.base_url)
        self.assertEqual(response.status_code, 500)
        self.assertIn("GCP_PROJECT_ID is not configured", response.json()["detail"])
        updated_plan = global_state_manager.get_build_plan(self.plan_id)
        self.assertEqual(updated_plan.status, "failed")


    @patch.dict(os.environ, {"GCP_PROJECT_ID": "test-project", "GCP_LOCATION": ""})
    def test_execute_plan_no_location(self):
        self._create_sample_plan()
        with patch.dict(os.environ, {"GCP_PROJECT_ID": "test-gcp-project", "GCP_LOCATION": ""}):
            response = self.client.post(self.base_url)
        self.assertEqual(response.status_code, 500)
        self.assertIn("GCP_LOCATION is not configured", response.json()["detail"])
        updated_plan = global_state_manager.get_build_plan(self.plan_id)
        self.assertEqual(updated_plan.status, "failed")


    @patch('agents.agent3.main.execute_build_step') # Path to execute_build_step in main.py
    def test_execute_plan_all_steps_success(self, mock_execute_step):
        mock_execute_step.return_value = True
        plan = self._create_sample_plan()

        response = self.client.post(self.base_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Build plan executed successfully")
        self.assertEqual(response.json()["new_status"], "completed")

        updated_plan = global_state_manager.get_build_plan(self.plan_id)
        self.assertEqual(updated_plan.status, "completed")
        self.assertIsNone(updated_plan.error_details)
        self.assertEqual(mock_execute_step.call_count, len(plan.steps))


    @patch('agents.agent3.main.execute_build_step')
    def test_execute_plan_one_step_fails(self, mock_execute_step):
        mock_execute_step.side_effect = [True, False]

        steps = [
            BuildStep(action="create_resource", type="gcs_bucket", name="my_bucket_ok"),
            BuildStep(action="create_resource", type="bigquery_dataset", name="my_dataset_fail")
        ]
        plan = self._create_sample_plan(steps=steps)

        response = self.client.post(self.base_url)

        self.assertEqual(response.status_code, 500)
        error_detail = response.json()["detail"]
        self.assertEqual(error_detail["step_index"], 1)
        self.assertEqual(error_detail["step_name"], "my_dataset_fail")
        self.assertIn("Execution failed at step 2", error_detail["message"])

        updated_plan = global_state_manager.get_build_plan(self.plan_id)
        self.assertEqual(updated_plan.status, "failed")
        self.assertIsNotNone(updated_plan.error_details)
        self.assertEqual(updated_plan.error_details.step_index, 1)
        self.assertEqual(updated_plan.error_details.step_name, "my_dataset_fail")
        self.assertEqual(mock_execute_step.call_count, 2)

    @patch('agents.agent3.main.execute_build_step')
    def test_execute_plan_first_step_fails(self, mock_execute_step):
        mock_execute_step.return_value = False

        steps = [BuildStep(action="create_resource", type="gcs_bucket", name="my_bucket_fail")]
        plan = self._create_sample_plan(steps=steps)

        response = self.client.post(self.base_url)

        self.assertEqual(response.status_code, 500)
        error_detail = response.json()["detail"]
        self.assertEqual(error_detail["step_index"], 0)

        updated_plan = global_state_manager.get_build_plan(self.plan_id)
        self.assertEqual(updated_plan.status, "failed")
        self.assertIsNotNone(updated_plan.error_details)
        self.assertEqual(updated_plan.error_details.step_index, 0)
        self.assertEqual(mock_execute_step.call_count, 1)

if __name__ == '__main__':
    unittest.main()
