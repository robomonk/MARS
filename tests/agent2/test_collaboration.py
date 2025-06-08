import unittest
from unittest.mock import patch, call
from agents.agent2.collaboration import fetch_external_data, check_build_feasibility
from agents.agent2.models import FeasibilityAssessment, ValidationStep # Added ValidationStep

class TestCollaboration(unittest.TestCase):

    def test_fetch_external_data_basic(self):
        queries = ["query1", "another query"]
        # Expect the "simulated_abstract_for_" format from the actual function
        expected_results = {
            "query1": "simulated_abstract_for_query1",
            "another query": "simulated_abstract_for_another_query"
        }
        results = fetch_external_data(queries)
        self.assertEqual(results, expected_results)

    def test_fetch_external_data_empty_list(self):
        queries = []
        expected_results = {}
        results = fetch_external_data(queries)
        self.assertEqual(results, expected_results)

    def test_fetch_external_data_special_chars(self):
        queries = ["query with spaces & chars!"]
        # Expect the "simulated_abstract_for_" format
        expected_results = {
            "query with spaces & chars!": "simulated_abstract_for_query_with_spaces_&_chars!"
        }
        results = fetch_external_data(queries)
        self.assertEqual(results, expected_results)

    @patch('agents.agent2.collaboration.fetch_external_data')
    def test_check_build_feasibility_basic_scenario(self, mock_fetch_external_data):
        validation_steps = [
            ValidationStep(step_id="s1", description="Step 1 Data Collection"),
            ValidationStep(step_id="s2", description="Step 2 Analysis Model")
        ]
        linked_hypothesis_id = "H001"

        mock_search_results = {
            "Public datasets for Step 1 Data Collection": "Found dataset for Step 1", # Contains "Found "
            "Python libraries for Step 1 Data Collection": "Found library for Step 1", # Contains "Found "
            "Availability of computational model for Step 1 Data Collection": "No model found for Step 1",
            "Public datasets for Step 2 Analysis Model": "Found dataset for Step 2", # Contains "Found "
            "Python libraries for Step 2 Analysis Model": "Found library for Step 2", # Contains "Found "
            "Availability of computational model for Step 2 Analysis Model": "Model available for Step 2" # Does not contain "Found " for this category
        }
        mock_fetch_external_data.return_value = mock_search_results
        assessment = check_build_feasibility(validation_steps, linked_hypothesis_id)

        expected_queries = [
            "Public datasets for Step 1 Data Collection", "Python libraries for Step 1 Data Collection", "Availability of computational model for Step 1 Data Collection",
            "Public datasets for Step 2 Analysis Model", "Python libraries for Step 2 Analysis Model", "Availability of computational model for Step 2 Analysis Model"
        ]
        mock_fetch_external_data.assert_called_once_with(expected_queries)

        self.assertEqual(assessment.data_obtainability, "PUBLIC")
        self.assertEqual(assessment.tools_availability, "OPEN_SOURCE")
        self.assertAlmostEqual(assessment.confidence_score, 0.80) # 0.5 + 0.15 + 0.15

    @patch('agents.agent2.collaboration.fetch_external_data')
    def test_check_build_feasibility_no_public_data(self, mock_fetch_external_data):
        validation_steps = [ValidationStep(step_id="s1", description="Only one step")]
        linked_hypothesis_id = "H002"
        mock_search_results = {
            "Public datasets for Only one step": "no relevant public data found", # Does not contain "Found "
            "Python libraries for Only one step": "Found library for step",      # Contains "Found "
            "Availability of computational model for Only one step": "No model"
        }
        mock_fetch_external_data.return_value = mock_search_results
        assessment = check_build_feasibility(validation_steps, linked_hypothesis_id)
        self.assertEqual(assessment.data_obtainability, "UNAVAILABLE")
        self.assertEqual(assessment.tools_availability, "OPEN_SOURCE")
        self.assertAlmostEqual(assessment.confidence_score, 0.65) # 0.5 + 0.15 (tools)

    @patch('agents.agent2.collaboration.fetch_external_data')
    def test_check_build_feasibility_no_tools(self, mock_fetch_external_data):
        validation_steps = [ValidationStep(step_id="s1", description="Another step")]
        linked_hypothesis_id = "H003"
        mock_search_results = {
            "Public datasets for Another step": "Found public data for this", # Contains "Found "
            "Python libraries for Another step": "no libraries found",      # Does not contain "Found "
            "Availability of computational model for Another step": "No model"
        }
        mock_fetch_external_data.return_value = mock_search_results
        assessment = check_build_feasibility(validation_steps, linked_hypothesis_id)
        self.assertEqual(assessment.data_obtainability, "PUBLIC")
        self.assertEqual(assessment.tools_availability, "REQUIRES_DEVELOPMENT")
        self.assertAlmostEqual(assessment.confidence_score, 0.65) # 0.5 + 0.15 (data)

    @patch('agents.agent2.collaboration.fetch_external_data')
    def test_check_build_feasibility_no_data_no_tools(self, mock_fetch_external_data):
        validation_steps = [ValidationStep(step_id="s1", description="Problematic step")]
        linked_hypothesis_id = "H004"
        mock_search_results = {
            "Public datasets for Problematic step": "nothing found",
            "Python libraries for Problematic step": "nothing found",
            "Availability of computational model for Problematic step": "No model"
        }
        mock_fetch_external_data.return_value = mock_search_results
        assessment = check_build_feasibility(validation_steps, linked_hypothesis_id)
        self.assertEqual(assessment.data_obtainability, "UNAVAILABLE")
        self.assertEqual(assessment.tools_availability, "REQUIRES_DEVELOPMENT")
        self.assertAlmostEqual(assessment.confidence_score, 0.50) # Base 0.5

    def test_check_build_feasibility_empty_validation_steps(self):
        assessment = check_build_feasibility([], "H005") # Empty list of ValidationStep
        self.assertEqual(assessment.data_obtainability, "UNAVAILABLE")
        self.assertEqual(assessment.tools_availability, "REQUIRES_DEVELOPMENT")
        self.assertAlmostEqual(assessment.confidence_score, 0.25)

    @patch('agents.agent2.collaboration.fetch_external_data')
    def test_check_build_feasibility_step_without_description(self, mock_fetch_external_data):
        # ValidationStep model requires description. If it can be None/empty, the model should allow it.
        # Assuming description is mandatory, an empty string might be passed.
        # The current model ValidationStep(step_id="s1", description="") is valid.
        # The collaboration.py logic `step.description if step.description else f'step_{i}_unnamed'` handles empty.
        validation_steps = [ValidationStep(step_id="s_no_desc", description="")]
        linked_hypothesis_id = "H006"

        mock_search_results = {
            "Public datasets for step_0_unnamed": "Found public data", # Contains "Found "
            "Python libraries for step_0_unnamed": "Found some libs", # Contains "Found "
            "Availability of computational model for step_0_unnamed": "No model"
        }
        mock_fetch_external_data.return_value = mock_search_results
        assessment = check_build_feasibility(validation_steps, linked_hypothesis_id)
        self.assertEqual(assessment.data_obtainability, "PUBLIC")
        self.assertEqual(assessment.tools_availability, "OPEN_SOURCE")
        self.assertAlmostEqual(assessment.confidence_score, 0.80)

if __name__ == '__main__':
    unittest.main()
