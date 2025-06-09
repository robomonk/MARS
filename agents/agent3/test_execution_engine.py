# agents/agent3/test_execution_engine.py
import unittest
from unittest.mock import patch, MagicMock
from google.api_core.exceptions import GoogleAPICallError, Forbidden, NotFound # Import relevant exceptions

# Assuming models.py and execution_engine.py are in the same directory (agents/agent3)
from .models import BuildStep
from .execution_engine import execute_build_step

class TestExecutionEngine(unittest.TestCase):

    def setUp(self):
        self.project_id = "test-project"
        self.location = "us-central1"
        self.common_step_details = {"description": "Test details"}

    @patch('agents.agent3.execution_engine.bigquery.Client')
    def test_execute_bigquery_dataset_success(self, MockBigQueryClient):
        mock_client_instance = MockBigQueryClient.return_value
        step = BuildStep(action="create_resource", type="bigquery_dataset", name="test_dataset", details=self.common_step_details)

        result = execute_build_step(step, self.project_id, self.location)

        self.assertTrue(result)
        MockBigQueryClient.assert_called_once_with(project=self.project_id)
        mock_client_instance.create_dataset.assert_called_once()
        created_dataset_arg = mock_client_instance.create_dataset.call_args[0][0]
        self.assertEqual(created_dataset_arg.dataset_id, f"{self.project_id}.{step.name}")
        self.assertEqual(created_dataset_arg.description, self.common_step_details["description"])

    @patch('agents.agent3.execution_engine.bigquery.Client')
    def test_execute_bigquery_dataset_failure(self, MockBigQueryClient):
        mock_client_instance = MockBigQueryClient.return_value
        mock_client_instance.create_dataset.side_effect = GoogleAPICallError("BigQuery API Error")
        step = BuildStep(action="create_resource", type="bigquery_dataset", name="test_dataset_fail")

        result = execute_build_step(step, self.project_id, self.location)
        self.assertFalse(result)

    @patch('agents.agent3.execution_engine.storage.Client')
    def test_execute_gcs_bucket_success(self, MockStorageClient):
        mock_client_instance = MockStorageClient.return_value
        step = BuildStep(action="create_resource", type="gcs_bucket", name="test_bucket_name")

        result = execute_build_step(step, self.project_id, self.location)

        self.assertTrue(result)
        MockStorageClient.assert_called_once_with(project=self.project_id)
        mock_client_instance.create_bucket.assert_called_once_with(step.name, location=self.location)

    @patch('agents.agent3.execution_engine.storage.Client')
    def test_execute_gcs_bucket_failure(self, MockStorageClient):
        mock_client_instance = MockStorageClient.return_value
        mock_client_instance.create_bucket.side_effect = Forbidden("GCS Forbidden Error")
        step = BuildStep(action="create_resource", type="gcs_bucket", name="test_bucket_fail")

        result = execute_build_step(step, self.project_id, self.location)
        self.assertFalse(result)

    @patch('agents.agent3.execution_engine.aiplatform.NotebookServiceClient')
    def test_execute_vertex_ai_notebook_success(self, MockNotebookClient):
        mock_client_instance = MockNotebookClient.return_value
        mock_operation = MagicMock()
        mock_operation.result.return_value = None # Simulate successful LRO
        mock_client_instance.create_instance.return_value = mock_operation

        step = BuildStep(
            action="create_resource",
            type="vertex_ai_notebook",
            name="test_notebook_instance",
            details={"instance_config": {"machine_type": "n1-standard-1"}}
        )

        result = execute_build_step(step, self.project_id, self.location)

        self.assertTrue(result)
        # Check client options if necessary, e.g. if api_endpoint is explicitly set
        # MockNotebookClient.assert_called_once_with(client_options=ANY)
        mock_client_instance.create_instance.assert_called_once()
        call_args = mock_client_instance.create_instance.call_args[1]
        self.assertEqual(call_args['parent'], f"projects/{self.project_id}/locations/{self.location}")
        self.assertEqual(call_args['instance_id'], step.name)
        self.assertIsNotNone(call_args['instance'])
        self.assertEqual(call_args['instance'].machine_type, "n1-standard-1")

    @patch('agents.agent3.execution_engine.aiplatform.NotebookServiceClient')
    def test_execute_vertex_ai_notebook_failure(self, MockNotebookClient):
        mock_client_instance = MockNotebookClient.return_value
        mock_client_instance.create_instance.side_effect = NotFound("Vertex AI Notebook API Error")
        step = BuildStep(action="create_resource", type="vertex_ai_notebook", name="test_notebook_fail")

        result = execute_build_step(step, self.project_id, self.location)
        self.assertFalse(result)

    def test_execute_unsupported_type(self):
        step = BuildStep(action="create_resource", type="unsupported_type", name="test_invalid_type")
        result = execute_build_step(step, self.project_id, self.location)
        self.assertFalse(result)

    def test_execute_unsupported_action(self):
        step = BuildStep(action="delete_resource", type="bigquery_dataset", name="test_invalid_action")
        result = execute_build_step(step, self.project_id, self.location)
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
