import unittest
from unittest.mock import patch, call
import sys
import os
import json
import uuid # For checking hypothesis_id format

# Adjust path to import from the project's 'agents' folder
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from agents.agent1.hypothesis_builder import HypothesisBuilder, ConversationState

# Helper to capture print output (for agent's messages to user)
from io import StringIO

class TestHypothesisBuilder(unittest.TestCase):

    def setUp(self):
        self.builder = HypothesisBuilder()

    def test_initialization(self):
        self.assertEqual(self.builder.state_machine.current_state, ConversationState.AWAITING_INPUT)
        self.assertIsNone(self.builder.hypothesis_components["general_topic"])
        self.assertFalse(self.builder.user_confirmed_hypothesis)
        self.assertIsNone(self.builder.final_hypothesis_json)
        print("TestHypothesisBuilder: test_initialization PASSED")

    @patch('builtins.input')
    def test_get_user_input_valid(self, mock_input):
        mock_input.return_value = "Test response"
        response = self.builder._get_user_input("Test prompt")
        self.assertEqual(response, "Test response")
        mock_input.assert_called_once_with("User: ") # Check prompt to input
        print("TestHypothesisBuilder: test_get_user_input_valid PASSED")

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO) # Capture print output
    def test_get_user_input_empty_then_valid(self, mock_stdout, mock_input):
        # Simulate empty input, then valid input
        mock_input.side_effect = ["", "  ", "Valid response"]

        prompt = "Please provide input:"
        response = self.builder._get_user_input(prompt)

        self.assertEqual(response, "Valid response")
        # Check that input was called three times
        self.assertEqual(mock_input.call_count, 3)
        # Check that the agent prompted about empty input
        # Note: logger also prints to console by default in hypothesis_builder,
        # so we check for the direct print output.
        output = mock_stdout.getvalue()
        self.assertIn("Agent: It looks like you didn't enter anything. Could you please provide a response?", output)
        print("TestHypothesisBuilder: test_get_user_input_empty_then_valid PASSED")

    @patch('builtins.input')
    @patch('agents.agent1.hypothesis_builder.logger') # Mock the logger
    def test_interaction_flow_to_confirmation(self, mock_logger, mock_input):
        # Simulate a full conversation flow up to confirmation
        mock_input.side_effect = [
            "AI Ethics",  # General topic
            "Bias in LLMs",  # Independent variable
            "Fairness metrics",  # Dependent variable
            "Algorithmic auditing"  # Mechanism
        ]

        # AWAITING_INPUT -> CLARIFYING (asks topic)
        self.builder._ask_clarifying_questions()
        self.assertEqual(self.builder.hypothesis_components["general_topic"], "AI Ethics")
        self.assertEqual(self.builder.state_machine.current_state, ConversationState.CLARIFYING)

        # CLARIFYING (asks IV)
        self.builder._ask_clarifying_questions()
        self.assertEqual(self.builder.hypothesis_components["independent_variable"], "Bias in LLMs")
        self.assertEqual(self.builder.state_machine.current_state, ConversationState.CLARIFYING)

        # CLARIFYING (asks DV)
        self.builder._ask_clarifying_questions()
        self.assertEqual(self.builder.hypothesis_components["dependent_variable"], "Fairness metrics")
        self.assertEqual(self.builder.state_machine.current_state, ConversationState.CLARIFYING)

        # CLARIFYING (asks Mechanism) -> REFINING
        self.builder._ask_clarifying_questions()
        self.assertEqual(self.builder.hypothesis_components["mechanism"], "Algorithmic auditing")
        self.assertEqual(self.builder.state_machine.current_state, ConversationState.REFINING)

        # REFINING -> AWAITING_CONFIRMATION
        self.builder._refine_hypothesis()
        expected_statement = "If we change the Bias in LLMs, then we will observe a change in the Fairness metrics, because Algorithmic auditing."
        self.assertEqual(self.builder.hypothesis_components["full_statement"], expected_statement)
        self.assertEqual(self.builder.state_machine.current_state, ConversationState.AWAITING_CONFIRMATION)
        print("TestHypothesisBuilder: test_interaction_flow_to_confirmation PASSED")

    @patch('builtins.input')
    @patch('agents.agent1.hypothesis_builder.logger')
    def test_hypothesis_confirmation_yes(self, mock_logger, mock_input):
        # Setup state as if we just refined
        self.builder.state_machine.transition_to(ConversationState.AWAITING_CONFIRMATION)
        self.builder.hypothesis_components["full_statement"] = "Test statement"
        mock_input.return_value = "yes"

        self.builder._await_confirmation()

        self.assertTrue(self.builder.user_confirmed_hypothesis)
        self.assertEqual(self.builder.state_machine.current_state, ConversationState.FINALIZED)
        print("TestHypothesisBuilder: test_hypothesis_confirmation_yes PASSED")

    @patch('builtins.input')
    @patch('agents.agent1.hypothesis_builder.logger')
    def test_hypothesis_confirmation_no(self, mock_logger, mock_input):
        # Set a topic so that CLARIFYING will ask for IV next
        self.builder.hypothesis_components["general_topic"] = "Initial Topic"
        self.builder.state_machine.transition_to(ConversationState.AWAITING_CONFIRMATION)
        self.builder.hypothesis_components["full_statement"] = "Test statement"
        # Also pre-fill other components to check they are cleared
        self.builder.hypothesis_components["independent_variable"] = "Old IV"
        self.builder.hypothesis_components["dependent_variable"] = "Old DV"
        self.builder.hypothesis_components["mechanism"] = "Old Mech"

        mock_input.return_value = "no"

        self.builder._await_confirmation()

        self.assertFalse(self.builder.user_confirmed_hypothesis)
        self.assertIsNone(self.builder.hypothesis_components["full_statement"])
        self.assertIsNone(self.builder.hypothesis_components["independent_variable"]) # Check reset
        self.assertIsNone(self.builder.hypothesis_components["dependent_variable"]) # Check reset
        self.assertIsNone(self.builder.hypothesis_components["mechanism"]) # Check reset
        self.assertEqual(self.builder.state_machine.current_state, ConversationState.CLARIFYING) # Expect CLARIFYING
        print("TestHypothesisBuilder: test_hypothesis_confirmation_no (updated expectations) PASSED")

    def test_structure_hypothesis_unconfirmed(self):
        # Hypothesis not confirmed
        self.builder.user_confirmed_hypothesis = False
        self.assertIsNone(self.builder.structure_hypothesis())
        print("TestHypothesisBuilder: test_structure_hypothesis_unconfirmed PASSED")

    def test_structure_hypothesis_valid_single_vars(self):
        self.builder.user_confirmed_hypothesis = True
        self.builder.hypothesis_components = {
            "independent_variable": "IV1",
            "dependent_variable": "DV1",
            "mechanism": "Reason1",
            "full_statement": "If IV1 then DV1 because Reason1"
        }

        json_output = self.builder.structure_hypothesis()
        self.assertIsNotNone(json_output)
        data = json.loads(json_output)

        self.assertTrue(uuid.UUID(data["hypothesis_id"], version=4)) # Check if valid UUIDv4
        self.assertEqual(data["statement"], "If IV1 then DV1 because Reason1")
        self.assertEqual(data["key_variables"]["independent"], ["IV1"])
        self.assertEqual(data["key_variables"]["dependent"], ["DV1"])
        self.assertEqual(data["core_assumptions"], ["Reason1"])
        self.assertEqual(data["status"], "unverified")
        print("TestHypothesisBuilder: test_structure_hypothesis_valid_single_vars PASSED")

    def test_structure_hypothesis_valid_multiple_vars(self):
        self.builder.user_confirmed_hypothesis = True
        self.builder.hypothesis_components = {
            "independent_variable": "IV1 ; IV2", # Semicolon separated
            "dependent_variable": "DV1;DV2 ; DV3",
            "mechanism": "Reason1 ; Reason2",
            "full_statement": "Complex statement"
        }

        json_output = self.builder.structure_hypothesis()
        self.assertIsNotNone(json_output)
        data = json.loads(json_output)

        self.assertEqual(data["key_variables"]["independent"], ["IV1", "IV2"])
        self.assertEqual(data["key_variables"]["dependent"], ["DV1", "DV2", "DV3"])
        self.assertEqual(data["core_assumptions"], ["Reason1", "Reason2"])
        print("TestHypothesisBuilder: test_structure_hypothesis_valid_multiple_vars PASSED")

    def test_structure_hypothesis_empty_vars_remain_single_string(self):
        # If a variable string is empty but not due to semicolon (e.g. user entered nothing for one part)
        # the current logic might make it an empty list or list with empty string.
        # Let's test current behavior: it should take the component as a single string if no semicolon.
        self.builder.user_confirmed_hypothesis = True
        self.builder.hypothesis_components = {
            "independent_variable": "",
            "dependent_variable": "DV1",
            "mechanism": "Reason1",
            "full_statement": "Statement"
        }
        json_output = self.builder.structure_hypothesis()
        data = json.loads(json_output)
        self.assertEqual(data["key_variables"]["independent"], [""]) # Handled as a single, empty string item
        print("TestHypothesisBuilder: test_structure_hypothesis_empty_vars_remain_single_string PASSED")


    @patch('agents.agent1.hypothesis_builder.logger') # Mock logger
    def test_initiate_experiment_design(self, mock_logger):
        test_payload = '{"test": "payload"}'
        self.builder.initiate_experiment_design(test_payload)

        # Check that logger.info was called with the payload
        # We expect two calls: one for "Placeholder..." and one for the payload itself
        self.assertIn(call("Placeholder: initiate_experiment_design called."), mock_logger.info.call_args_list)
        self.assertIn(call(f"Payload to be sent to Agent 2 (Experiment Designer):\n{test_payload}"), mock_logger.info.call_args_list)
        print("TestHypothesisBuilder: test_initiate_experiment_design PASSED")

    @patch('agents.agent1.hypothesis_builder.logger')
    def test_initiate_experiment_design_no_payload(self, mock_logger):
        self.builder.initiate_experiment_design(None)
        mock_logger.error.assert_called_with("initiate_experiment_design called with no payload.")
        print("TestHypothesisBuilder: test_initiate_experiment_design_no_payload PASSED")

    @patch('builtins.input')
    @patch('agents.agent1.hypothesis_builder.HypothesisBuilder.initiate_experiment_design') # Mock this method
    @patch('agents.agent1.hypothesis_builder.logger') # Mock logger
    def test_run_interaction_loop_full_cycle(self, mock_logger, mock_initiate_experiment_design, mock_input):
        mock_input.side_effect = [
            "Topic", "IV", "DV", "Mech", # for _ask_clarifying_questions
            "yes" # for _await_confirmation
        ]

        self.builder.run_interaction_loop()

        self.assertTrue(self.builder.user_confirmed_hypothesis)
        self.assertIsNotNone(self.builder.final_hypothesis_json)
        mock_initiate_experiment_design.assert_called_once_with(self.builder.final_hypothesis_json)
        self.assertEqual(self.builder.state_machine.current_state, ConversationState.FINALIZED)
        print("TestHypothesisBuilder: test_run_interaction_loop_full_cycle PASSED")

    @patch('builtins.input')
    @patch('agents.agent1.hypothesis_builder.logger') # Mock logger
    def test_run_interaction_loop_exit_no_confirmation(self, mock_logger, mock_input):
        mock_input.side_effect = [
            "Topic", "IV", "DV", "Mech", # for _ask_clarifying_questions
            "no" # for _await_confirmation
            # Loop will ask to refine, we need more inputs if we want to continue
            # For this test, we'll assume it exits after one 'no' if not handled further
            # The current _await_confirmation with "no" transitions to REFINING.
            # _refine_hypothesis will then run. If components are present, it re-proposes.
            # To truly exit, the loop would need to break, or state go to FINALIZED by other means
            # or user input leads to an unhandled state.
            # Let's refine this test to check it goes back to REFINING and tries again.
            , "IV_new", "DV_new", "Mech_new" # For the second round of questions after 'no'
            , "yes" # Confirm the second time
        ]

        # To prevent infinite loop in test if logic is flawed, we can patch refine or await
        # or limit input. For now, provide enough input for two cycles.

        self.builder.run_interaction_loop()

        self.assertTrue(self.builder.user_confirmed_hypothesis) # Should be true after second attempt
        self.assertEqual(self.builder.state_machine.current_state, ConversationState.FINALIZED)
        self.assertIn("IV_new", self.builder.hypothesis_components["full_statement"])
        print("TestHypothesisBuilder: test_run_interaction_loop_exit_no_confirmation PASSED")


if __name__ == '__main__':
    unittest.main(verbosity=1) # verbosity=1 is default, 2 is more verbose
