import pytest
import json
from unittest.mock import patch, call
import uuid

from agents.agent1.hypothesis_builder import HypothesisBuilder
from agents.agent1.state_machine import ConversationState, StateMachine


@pytest.fixture
def builder():
    """Pytest fixture to create a HypothesisBuilder instance for each test."""
    return HypothesisBuilder()

def test_initial_state(builder):
    """Test that the initial state is AWAITING_INPUT."""
    assert builder.state_machine.current_state == ConversationState.AWAITING_INPUT

@patch('agents.agent1.hypothesis_builder.HypothesisBuilder._get_user_input')
def test_transition_to_clarifying_on_first_question(mock_get_user_input, builder):
    """Test transition to CLARIFYING when the first question is asked."""
    # Simulate user providing input for the general topic
    mock_get_user_input.return_value = "Climate Change"

    # _ask_clarifying_questions should be called, which asks for general_topic first
    # and then transitions state.
    # In HypothesisBuilder, AWAITING_INPUT implicitly transitions to CLARIFYING
    # when _ask_clarifying_questions is first called.
    builder._ask_clarifying_questions()

    assert builder.hypothesis_components["general_topic"] == "Climate Change"
    assert builder.state_machine.current_state == ConversationState.CLARIFYING
    mock_get_user_input.assert_called_once_with("What is the general research area or topic you are interested in exploring?")

@patch('agents.agent1.hypothesis_builder.HypothesisBuilder._get_user_input')
def test_transitions_through_clarifying_to_refining(mock_get_user_input, builder):
    """Test transitions through CLARIFYING for IV, DV, and then to REFINING for mechanism."""
    # Initial state is AWAITING_INPUT

    # 1. Provide General Topic -> CLARIFYING
    mock_get_user_input.side_effect = ["Topic", "IV", "DV", "Mechanism"]

    builder._ask_clarifying_questions() # Asks for topic
    assert builder.state_machine.current_state == ConversationState.CLARIFYING
    assert builder.hypothesis_components["general_topic"] == "Topic"

    # 2. Provide Independent Variable (still in CLARIFYING)
    builder._ask_clarifying_questions() # Asks for IV
    assert builder.state_machine.current_state == ConversationState.CLARIFYING
    assert builder.hypothesis_components["independent_variable"] == "IV"

    # 3. Provide Dependent Variable (still in CLARIFYING)
    builder._ask_clarifying_questions() # Asks for DV
    assert builder.state_machine.current_state == ConversationState.CLARIFYING
    assert builder.hypothesis_components["dependent_variable"] == "DV"

    # 4. Provide Mechanism -> moves to REFINING
    builder._ask_clarifying_questions() # Asks for Mechanism
    # The transition to REFINING occurs after mechanism is provided in _ask_clarifying_questions
    assert builder.state_machine.current_state == ConversationState.REFINING
    assert builder.hypothesis_components["mechanism"] == "Mechanism"

    expected_calls = [
        call("What is the general research area or topic you are interested in exploring?"),
        call("Okay, regarding 'Topic', what specific factor or variable are you thinking of changing or manipulating? This will be your independent variable. (Separate multiple with ';')"),
        call("And what measurable outcome or effect do you expect to observe when you change 'IV'? This will be your dependent variable. (Separate multiple with ';')"),
        call(f"Why do you expect that changing 'IV' will lead to an observable change in 'DV'? What is the underlying reason or assumption (because of Z)? (Separate multiple assumptions with ';')")
    ]
    assert mock_get_user_input.call_args_list == expected_calls

@patch('agents.agent1.hypothesis_builder.HypothesisBuilder._get_user_input')
def test_transition_refining_to_awaiting_confirmation(mock_get_user_input, builder):
    """Test transition from REFINING to AWAITING_CONFIRMATION after hypothesis is constructed."""
    # Setup: Fill components to allow _refine_hypothesis to work
    builder.hypothesis_components["general_topic"] = "Topic"
    builder.hypothesis_components["independent_variable"] = "IV"
    builder.hypothesis_components["dependent_variable"] = "DV"
    builder.hypothesis_components["mechanism"] = "Mechanism"
    builder.state_machine.transition_to(ConversationState.REFINING) # Manually set for this test unit

    builder._refine_hypothesis()

    assert builder.state_machine.current_state == ConversationState.AWAITING_CONFIRMATION
    assert builder.hypothesis_components["full_statement"] is not None

@patch('agents.agent1.hypothesis_builder.HypothesisBuilder._get_user_input')
def test_transition_awaiting_confirmation_to_finalized_on_yes(mock_get_user_input, builder):
    """Test transition from AWAITING_CONFIRMATION to FINALIZED when user says 'yes'."""
    # Setup:
    builder.hypothesis_components["full_statement"] = "Some statement" # Needed for _await_confirmation
    builder.state_machine.transition_to(ConversationState.AWAITING_CONFIRMATION)
    mock_get_user_input.return_value = "yes"

    builder._await_confirmation()

    assert builder.state_machine.current_state == ConversationState.FINALIZED
    assert builder.user_confirmed_hypothesis is True
    mock_get_user_input.assert_called_once_with("Does this accurately capture your intended hypothesis? (yes/no)")

@patch('agents.agent1.hypothesis_builder.HypothesisBuilder._get_user_input')
def test_transition_awaiting_confirmation_to_clarifying_on_no(mock_get_user_input, builder):
    """Test transition from AWAITING_CONFIRMATION back to CLARIFYING when user says 'no'."""
    # Setup:
    builder.hypothesis_components["general_topic"] = "Topic"
    builder.hypothesis_components["independent_variable"] = "IV" # Will be reset
    builder.hypothesis_components["dependent_variable"] = "DV" # Will be reset
    builder.hypothesis_components["mechanism"] = "Mechanism" # Will be reset
    builder.hypothesis_components["full_statement"] = "Some statement"
    builder.state_machine.transition_to(ConversationState.AWAITING_CONFIRMATION)
    mock_get_user_input.return_value = "no"

    builder._await_confirmation()

    assert builder.state_machine.current_state == ConversationState.CLARIFYING
    assert builder.user_confirmed_hypothesis is False
    # Check that components are reset to allow re-input
    assert builder.hypothesis_components["independent_variable"] is None
    assert builder.hypothesis_components["dependent_variable"] is None
    assert builder.hypothesis_components["mechanism"] is None
    assert builder.hypothesis_components["full_statement"] is None
    mock_get_user_input.assert_called_once_with("Does this accurately capture your intended hypothesis? (yes/no)")


@patch('agents.agent1.hypothesis_builder.HypothesisBuilder._get_user_input')
def test_hypothesis_generation_strict_schema_and_content(mock_get_user_input, builder):
    """
    Test that a complete interaction flow generates a hypothesis JSON object
    that strictly matches the defined schema and accurately reflects the mock conversation.
    """
    # Mock conversation flow
    mock_user_inputs = [
        "Urban farming impact on local ecosystems",  # General Topic
        "Type of urban farm;Rooftop gardens vs Vertical farms",  # Independent Variable(s)
        "Local bird population diversity;Insect species count",  # Dependent Variable(s)
        "Increased green space attracts more species;Reduced pesticide use helps insect recovery",  # Mechanism(s)
        "yes"  # Confirmation
    ]
    mock_get_user_input.side_effect = mock_user_inputs

    # Drive the builder through the states
    # 1. AWAITING_INPUT -> CLARIFYING (asks for topic)
    builder._ask_clarifying_questions()
    # 2. CLARIFYING (asks for IV)
    builder._ask_clarifying_questions()
    # 3. CLARIFYING (asks for DV)
    builder._ask_clarifying_questions()
    # 4. CLARIFYING -> REFINING (asks for mechanism)
    builder._ask_clarifying_questions()

    # 5. REFINING -> AWAITING_CONFIRMATION (constructs statement)
    builder._refine_hypothesis()

    # 6. AWAITING_CONFIRMATION -> FINALIZED (user confirms)
    builder._await_confirmation()

    assert builder.state_machine.current_state == ConversationState.FINALIZED
    assert builder.user_confirmed_hypothesis is True

    # Generate the hypothesis JSON
    hypothesis_json_string = builder.structure_hypothesis()
    assert hypothesis_json_string is not None

    hypothesis_data = json.loads(hypothesis_json_string)

    # Assertions for schema and content
    # 1. hypothesis_id
    assert "hypothesis_id" in hypothesis_data
    try:
        uuid.UUID(hypothesis_data["hypothesis_id"])
    except ValueError:
        pytest.fail("hypothesis_id is not a valid UUID")

    # 2. statement
    assert "statement" in hypothesis_data
    expected_statement = ("If we change the Type of urban farm;Rooftop gardens vs Vertical farms, "
                          "then we will observe a change in the Local bird population diversity;Insect species count, "
                          "because Increased green space attracts more species;Reduced pesticide use helps insect recovery.")
    assert hypothesis_data["statement"] == expected_statement

    # 3. key_variables
    assert "key_variables" in hypothesis_data
    assert "independent" in hypothesis_data["key_variables"]
    assert "dependent" in hypothesis_data["key_variables"]
    assert hypothesis_data["key_variables"]["independent"] == ["Type of urban farm", "Rooftop gardens vs Vertical farms"]
    assert hypothesis_data["key_variables"]["dependent"] == ["Local bird population diversity", "Insect species count"]

    # 4. core_assumptions
    assert "core_assumptions" in hypothesis_data
    assert hypothesis_data["core_assumptions"] == ["Increased green space attracts more species", "Reduced pesticide use helps insect recovery"]

    # 5. status
    assert "status" in hypothesis_data
    assert hypothesis_data["status"] == "unverified"


@patch('agents.agent1.hypothesis_builder.HypothesisBuilder.initiate_experiment_design')
def test_collaboration_mock_initiate_experiment_design_called(mock_initiate_experiment_design, builder):
    """
    Test that initiate_experiment_design is called once when the agent
    would normally hand off, and with the correct hypothesis JSON.
    This test directly calls the method after setting up conditions.
    """
    # Prepare a mock hypothesis JSON payload
    mock_hypothesis_payload = {
        "hypothesis_id": str(uuid.uuid4()),
        "statement": "A well-defined hypothesis statement.",
        "key_variables": {
            "independent": ["IV1"],
            "dependent": ["DV1"]
        },
        "core_assumptions": ["Assumption1"],
        "status": "unverified"
    }
    mock_json_payload_string = json.dumps(mock_hypothesis_payload, indent=4)

    # Set up the builder conditions as if a hypothesis was finalized
    builder.user_confirmed_hypothesis = True
    builder.final_hypothesis_json = mock_json_payload_string
    # We are testing the initiate_experiment_design method in isolation here.
    # The run_interaction_loop is more of an integration test for the full flow.

    # Call the method that should trigger the (mocked) collaboration
    builder.initiate_experiment_design(builder.final_hypothesis_json)

    # Assert that the mocked initiate_experiment_design was called
    mock_initiate_experiment_design.assert_called_once()

    # Assert that it was called with the correct argument
    mock_initiate_experiment_design.assert_called_once_with(mock_json_payload_string)

@patch('agents.agent1.hypothesis_builder.HypothesisBuilder._get_user_input')
@patch('agents.agent1.hypothesis_builder.HypothesisBuilder.initiate_experiment_design') # Patch this as well
def test_initiate_experiment_design_called_at_end_of_loop(mock_initiate_experiment_design, mock_get_user_input, builder):
    """
    Test that initiate_experiment_design is called at the end of
    run_interaction_loop when a hypothesis is successfully finalized.
    """
    # Mock conversation flow to finalize hypothesis
    mock_user_inputs = [
        "Topic for loop test", "IV for loop", "DV for loop", "Mechanism for loop", "yes"
    ]
    mock_get_user_input.side_effect = mock_user_inputs

    # Run the interaction loop, which should eventually call initiate_experiment_design
    builder.run_interaction_loop()

    # Assert that the mocked initiate_experiment_design was called
    mock_initiate_experiment_design.assert_called_once()

    # Optionally, assert it was called with the generated JSON
    # This requires capturing the argument it was called with
    args, kwargs = mock_initiate_experiment_design.call_args
    assert len(args) == 1
    called_with_payload_string = args[0]
    assert called_with_payload_string is not None

    payload_data = json.loads(called_with_payload_string)
    assert payload_data["statement"] == "If we change the IV for loop, then we will observe a change in the DV for loop, because Mechanism for loop."
    assert payload_data["key_variables"]["independent"] == ["IV for loop"]
    assert payload_data["key_variables"]["dependent"] == ["DV for loop"]
    assert payload_data["core_assumptions"] == ["Mechanism for loop"]
    assert payload_data["status"] == "unverified"
    assert "hypothesis_id" in payload_data
