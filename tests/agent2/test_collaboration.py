import unittest
from unittest.mock import patch, call
from agents.agent2.collaboration import fetch_external_data, check_build_feasibility
from agents.agent2.models import FeasibilityAssessment

class TestCollaboration(unittest.TestCase):

    def test_fetch_external_data_basic(self):
        queries = ["query1", "another query"]
        expected_results = {
            "query1": "mocked_result_for_query1",
            "another query": "mocked_result_for_another_query"
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
        expected_results = {
            "query with spaces & chars!": "mocked_result_for_query_with_spaces_&_chars!"
        }
        results = fetch_external_data(queries)
        self.assertEqual(results, expected_results)

    @patch('agents.agent2.collaboration.fetch_external_data')
    def test_check_build_feasibility_basic_scenario(self, mock_fetch_external_data):
        validation_steps = [
            {"description": "Step 1 Data Collection"},
            {"description": "Step 2 Analysis Model"}
        ]
        linked_hypothesis_id = "H001"

        # Mock the return value of fetch_external_data
        mock_search_results = {
            "Public datasets for Step 1 Data Collection": "mocked_result_for_Public_datasets_for_Step_1_Data_Collection",
            "Python libraries for Step 1 Data Collection": "mocked_result_for_Python_libraries_for_Step_1_Data_Collection",
            "Availability of computational model for Step 1 Data Collection": "mocked_result_for_Availability_of_computational_model_for_Step_1_Data_Collection",
            "Public datasets for Step 2 Analysis Model": "mocked_result_for_Public_datasets_for_Step_2_Analysis_Model",
            "Python libraries for Step 2 Analysis Model": "mocked_result_for_Python_libraries_for_Step_2_Analysis_Model",
            "Availability of computational model for Step 2 Analysis Model": "mocked_result_for_Availability_of_computational_model_for_Step_2_Analysis_Model"
        }
        mock_fetch_external_data.return_value = mock_search_results

        assessment = check_build_feasibility(validation_steps, linked_hypothesis_id)

        # Verify calls to fetch_external_data
        expected_queries = [
            "Public datasets for Step 1 Data Collection",
            "Python libraries for Step 1 Data Collection",
            "Availability of computational model for Step 1 Data Collection",
            "Public datasets for Step 2 Analysis Model",
            "Python libraries for Step 2 Analysis Model",
            "Availability of computational model for Step 2 Analysis Model"
        ]
        mock_fetch_external_data.assert_called_once_with(expected_queries)

        # Verify FeasibilityAssessment content
        self.assertIsInstance(assessment, FeasibilityAssessment)
        self.assertEqual(assessment.data_obtainability, "PUBLIC") # Both steps found public data
        self.assertEqual(assessment.tools_availability, "OPEN_SOURCE") # Both steps found python libs
        self.assertAlmostEqual(assessment.confidence_score, 0.80) # 0.5 + 0.15 + 0.15
        self.assertIn("Feasibility assessment for Hypothesis ID: H001", assessment.summary)
        for query, result in mock_search_results.items():
            self.assertIn(f"- Query '{query}': {result}", assessment.summary)

    @patch('agents.agent2.collaboration.fetch_external_data')
    def test_check_build_feasibility_no_public_data(self, mock_fetch_external_data):
        validation_steps = [{"description": "Only one step"}]
        linked_hypothesis_id = "H002"

        mock_search_results = {
            "Public datasets for Only one step": "no relevant public data found", # Assume this means not found
            "Python libraries for Only one step": "mocked_result_for_Python_libraries_for_Only_one_step",
            "Availability of computational model for Only one step": "mocked_result_for_Availability_of_computational_model_for_Only_one_step"
        }
        mock_fetch_external_data.return_value = mock_search_results

        assessment = check_build_feasibility(validation_steps, linked_hypothesis_id)
        self.assertEqual(assessment.data_obtainability, "UNAVAILABLE")
        self.assertEqual(assessment.tools_availability, "OPEN_SOURCE")
        self.assertAlmostEqual(assessment.confidence_score, 0.65) # 0.5 + 0.15

    @patch('agents.agent2.collaboration.fetch_external_data')
    def test_check_build_feasibility_no_tools(self, mock_fetch_external_data):
        validation_steps = [{"description": "Another step"}]
        linked_hypothesis_id = "H003"

        mock_search_results = {
            "Public datasets for Another step": "mocked_result_for_Public_datasets_for_Another_step",
            "Python libraries for Another step": "no libraries found", # Assume this means not found
            "Availability of computational model for Another step": "mocked_result_for_Availability_of_computational_model_for_Another_step"
        }
        mock_fetch_external_data.return_value = mock_search_results

        assessment = check_build_feasibility(validation_steps, linked_hypothesis_id)
        self.assertEqual(assessment.data_obtainability, "PUBLIC")
        self.assertEqual(assessment.tools_availability, "REQUIRES_DEVELOPMENT")
        self.assertAlmostEqual(assessment.confidence_score, 0.65) # 0.5 + 0.15

    @patch('agents.agent2.collaboration.fetch_external_data')
    def test_check_build_feasibility_no_data_no_tools(self, mock_fetch_external_data):
        validation_steps = [{"description": "Problematic step"}]
        linked_hypothesis_id = "H004"

        mock_search_results = {
            "Public datasets for Problematic step": "nothing found",
            "Python libraries for Problematic step": "nothing found",
            "Availability of computational model for Problematic step": "mocked_result_for_Availability_of_computational_model_for_Problematic_step"
        }
        mock_fetch_external_data.return_value = mock_search_results

        assessment = check_build_feasibility(validation_steps, linked_hypothesis_id)
        self.assertEqual(assessment.data_obtainability, "UNAVAILABLE")
        self.assertEqual(assessment.tools_availability, "REQUIRES_DEVELOPMENT")
        self.assertAlmostEqual(assessment.confidence_score, 0.50) # Base 0.5

    def test_check_build_feasibility_empty_validation_steps(self):
        # No need to mock fetch_external_data as it shouldn't be called
        assessment = check_build_feasibility([], "H005")
        self.assertEqual(assessment.data_obtainability, "UNAVAILABLE")
        self.assertEqual(assessment.tools_availability, "REQUIRES_DEVELOPMENT")
        self.assertAlmostEqual(assessment.confidence_score, 0.25)
        self.assertEqual(assessment.summary, "No validation steps provided to assess feasibility.")

    @patch('agents.agent2.collaboration.fetch_external_data')
    def test_check_build_feasibility_step_without_description(self, mock_fetch_external_data):
        validation_steps = [{}] # Step with no 'description' key
        linked_hypothesis_id = "H006"

        mock_search_results = {
            "Public datasets for step_0_unnamed": "mocked_result_public",
            "Python libraries for step_0_unnamed": "mocked_result_libs",
            "Availability of computational model for step_0_unnamed": "mocked_result_model"
        }
        mock_fetch_external_data.return_value = mock_search_results

        assessment = check_build_feasibility(validation_steps, linked_hypothesis_id)

        expected_queries = [
            "Public datasets for step_0_unnamed",
            "Python libraries for step_0_unnamed",
            "Availability of computational model for step_0_unnamed"
        ]
        mock_fetch_external_data.assert_called_once_with(expected_queries)

        self.assertEqual(assessment.data_obtainability, "PUBLIC")
        self.assertEqual(assessment.tools_availability, "OPEN_SOURCE")
        self.assertAlmostEqual(assessment.confidence_score, 0.80)


if __name__ == '__main__':
    unittest.main()
