import enum

class ConversationState(enum.Enum):
    AWAITING_INPUT = "AWAITING_INPUT"
    CLARIFYING = "CLARIFYING"
    REFINING = "REFINING"
    AWAITING_CONFIRMATION = "AWAITING_CONFIRMATION"
    FINALIZED = "FINALIZED"

class StateMachine:
    def __init__(self, initial_state=ConversationState.AWAITING_INPUT):
        if not isinstance(initial_state, ConversationState):
            raise TypeError("initial_state must be an instance of ConversationState")
        self._current_state = initial_state
        print(f"State machine initialized. Current state: {self._current_state.value}")

    @property
    def current_state(self):
        return self._current_state

    def transition_to(self, new_state):
        if not isinstance(new_state, ConversationState):
            raise TypeError("new_state must be an instance of ConversationState")

        print(f"Attempting transition from {self._current_state.value} to {new_state.value}")

        # Define allowed transitions (optional, but good practice)
        allowed_transitions = {
            ConversationState.AWAITING_INPUT: [ConversationState.CLARIFYING],
            ConversationState.CLARIFYING: [ConversationState.REFINING, ConversationState.AWAITING_INPUT],
            ConversationState.REFINING: [ConversationState.AWAITING_CONFIRMATION, ConversationState.CLARIFYING],
            ConversationState.AWAITING_CONFIRMATION: [ConversationState.FINALIZED, ConversationState.REFINING],
            ConversationState.FINALIZED: [] # No transitions out of FINALIZED by default
        }

        if new_state in allowed_transitions.get(self._current_state, []):
            self._current_state = new_state
            print(f"Transition successful. New state: {self._current_state.value}")
        elif self._current_state == new_state:
            print(f"Already in state {self._current_state.value}. No transition needed.")
        else:
            # Fallback or error for disallowed transitions. For now, allow any transition if not specified.
            # This makes the state machine more flexible for initial development.
            # In a stricter implementation, you might raise an error here.
            print(f"Transition from {self._current_state.value} to {new_state.value} is not explicitly defined, but allowing it.")
            self._current_state = new_state
            print(f"Transition successful. New state: {self._current_state.value}")

        return self._current_state

if __name__ == '__main__':
    # Example Usage
    sm = StateMachine()
    print(f"Initial state: {sm.current_state.value}")

    sm.transition_to(ConversationState.CLARIFYING)
    sm.transition_to(ConversationState.REFINING)
    sm.transition_to(ConversationState.AWAITING_CONFIRMATION)
    sm.transition_to(ConversationState.FINALIZED)

    # Example of a transition that might be considered disallowed if strict rules were enforced
    # but is allowed by the current flexible design
    sm_flexible = StateMachine(ConversationState.AWAITING_INPUT)
    sm_flexible.transition_to(ConversationState.FINALIZED)

    # Example of trying to transition to the same state
    sm_same_state = StateMachine(ConversationState.CLARIFYING)
    sm_same_state.transition_to(ConversationState.CLARIFYING)

    # Example of invalid state type
    try:
        StateMachine("INVALID_STATE")
    except TypeError as e:
        print(f"Error during instantiation: {e}")

    try:
        sm.transition_to("ANOTHER_INVALID_STATE")
    except TypeError as e:
        print(f"Error during transition: {e}")
