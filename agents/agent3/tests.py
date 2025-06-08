import unittest
import uuid
from .models import AbstractProtocol, BuildPlan, BuildStep
from .plan_translator import translate_protocol_to_build_plan

class TestPlanTranslator(unittest.TestCase):

    def test_translate_basic_protocol(self):
        """Test translation with minimal protocol data."""
        protocol = AbstractProtocol(
            protocol_id="test_proto_123",
            title="Test Experiment",
            research_question="Does this work?",
            data_requirement=None # No specific data requirement
        )

        plan = translate_protocol_to_build_plan(protocol)

        self.assertIsInstance(plan, BuildPlan)
        self.assertEqual(plan.protocol_id, "test_proto_123")
        self.assertIsInstance(plan.steps, list)
        self.assertEqual(len(plan.steps), 0) # No steps expected for None data_requirement
        self.assertEqual(plan.status, "pending_approval")

        # Check if plan_id is a valid UUID string
        try:
            uuid.UUID(plan.plan_id)
        except ValueError:
            self.fail("plan_id is not a valid UUID string")

    def test_translate_with_structured_sql_db_requirement(self):
        """Test translation when 'structured_sql_db' is required."""
        protocol = AbstractProtocol(
            protocol_id="test_proto_sql",
            data_requirement="structured_sql_db"
        )

        plan = translate_protocol_to_build_plan(protocol)

        self.assertEqual(plan.protocol_id, "test_proto_sql")
        self.assertEqual(len(plan.steps), 1)
        step = plan.steps[0]
        self.assertIsInstance(step, BuildStep)
        self.assertEqual(step.action, "create_resource")
        self.assertEqual(step.type, "bigquery_dataset")
        self.assertTrue(step.name.startswith("experiment_data_"))
        self.assertIsNotNone(step.details)
        self.assertEqual(plan.status, "pending_approval")

    def test_translate_with_text_file_requirement(self):
        """Test translation when 'text_file' is required."""
        protocol = AbstractProtocol(
            protocol_id="test_proto_text",
            data_requirement="text_file"
        )

        plan = translate_protocol_to_build_plan(protocol)

        self.assertEqual(plan.protocol_id, "test_proto_text")
        self.assertEqual(len(plan.steps), 1)
        step = plan.steps[0]
        self.assertIsInstance(step, BuildStep)
        self.assertEqual(step.action, "create_resource")
        self.assertEqual(step.type, "cloud_storage_bucket")
        self.assertTrue(step.name.startswith("text_files_"))
        self.assertIsNotNone(step.details)
        self.assertEqual(plan.status, "pending_approval")

if __name__ == '__main__':
    unittest.main()
