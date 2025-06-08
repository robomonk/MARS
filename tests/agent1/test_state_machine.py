import unittest
import sys
import os

# Adjust the path to import from the parent directory's 'agents' folder
# This assumes 'tests' is at the same level as the main project directory containing 'agents'
# Get the absolute path to the project root (assuming 'tests' is one level down)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from agents.agent1.state_machine import StateMachine, ConversationState

class TestStateMachine(unittest.TestCase):

    def test_initial_state(self):
        sm = StateMachine()
        self.assertEqual(sm.current_state, ConversationState.AWAITING_INPUT)
        sm_custom = StateMachine(initial_state=ConversationState.CLARIFYING)
        self.assertEqual(sm_custom.current_state, ConversationState.CLARIFYING)
        print("TestStateMachine: test_initial_state PASSED")

    def test_valid_transitions(self):
        sm = StateMachine()
        # AWAITING_INPUT -> CLARIFYING
        sm.transition_to(ConversationState.CLARIFYING)
        self.assertEqual(sm.current_state, ConversationState.CLARIFYING)
        # CLARIFYING -> REFINING
        sm.transition_to(ConversationState.REFINING)
        self.assertEqual(sm.current_state, ConversationState.REFINING)
        # REFINING -> AWAITING_CONFIRMATION
        sm.transition_to(ConversationState.AWAITING_CONFIRMATION)
        self.assertEqual(sm.current_state, ConversationState.AWAITING_CONFIRMATION)
        # AWAITING_CONFIRMATION -> FINALIZED
        sm.transition_to(ConversationState.FINALIZED)
        self.assertEqual(sm.current_state, ConversationState.FINALIZED)
        print("TestStateMachine: test_valid_transitions PASSED")

    def test_flexible_transition_allowed(self):
        # Test a transition that is not in the 'allowed_transitions' but should still work
        # due to the flexible design (prints a message but performs the transition)
        sm = StateMachine(ConversationState.AWAITING_INPUT)
        sm.transition_to(ConversationState.FINALIZED) # Not a direct defined path
        self.assertEqual(sm.current_state, ConversationState.FINALIZED)
        print("TestStateMachine: test_flexible_transition_allowed PASSED")

    def test_transition_to_same_state(self):
        sm = StateMachine(ConversationState.CLARIFYING)
        sm.transition_to(ConversationState.CLARIFYING)
        self.assertEqual(sm.current_state, ConversationState.CLARIFYING)
        # Check that it prints "Already in state..." (requires capturing stdout or checking logs if implemented)
        # For now, just ensuring state remains the same is the primary check.
        print("TestStateMachine: test_transition_to_same_state PASSED")

    def test_no_transition_from_finalized(self):
        # Based on current allowed_transitions, FINALIZED has no outgoing paths.
        # However, the flexible design might still allow it with a warning.
        # Let's test the defined behavior first.
        sm = StateMachine(ConversationState.FINALIZED)
        # If we strictly followed allowed_transitions, this would raise an error or do nothing.
        # With the current flexible design, it will transition.
        # This test highlights the flexibility rather than strictness.
        sm.transition_to(ConversationState.AWAITING_INPUT)
        self.assertEqual(sm.current_state, ConversationState.AWAITING_INPUT)
        print("TestStateMachine: test_no_transition_from_finalized (flexibility check) PASSED")


    def test_initial_state_type_error(self):
        with self.assertRaises(TypeError):
            StateMachine(initial_state="INVALID_STATE_TYPE")
        print("TestStateMachine: test_initial_state_type_error PASSED")

    def test_transition_to_invalid_type(self):
        sm = StateMachine()
        with self.assertRaises(TypeError):
            sm.transition_to("INVALID_STATE_TYPE")
        print("TestStateMachine: test_transition_to_invalid_type PASSED")

if __name__ == '__main__':
    # This allows running the tests directly from this file
    unittest.main()
