from .state_machine import StateMachine, ConversationState
import uuid
import json
import logging # Add logging import

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class HypothesisBuilder:
    def __init__(self):
        self.state_machine = StateMachine()
        self.hypothesis_components = {
            "general_topic": None,
            "independent_variable": None,
            "dependent_variable": None,
            "mechanism": None,
            "full_statement": None
        }
        self.user_confirmed_hypothesis = False
        self.final_hypothesis_json = None

    def _get_user_input(self, prompt_message):
        while True:
            logger.info(f"Agent: {prompt_message}")
            user_response = input("User: ").strip() # Add .strip() to remove leading/trailing whitespace
            if user_response:
                logger.info(f"User response: {user_response}")
                return user_response
            else:
                # Log the empty response and inform the user.
                logger.warning("User provided an empty response.")
                print("Agent: It looks like you didn't enter anything. Could you please provide a response?")
                # The loop will then re-iterate, asking the same prompt_message.

    def _ask_clarifying_questions(self):
        if self.hypothesis_components["general_topic"] is None:
            response = self._get_user_input("What is the general research area or topic you are interested in exploring?")
            self.hypothesis_components["general_topic"] = response
            self.state_machine.transition_to(ConversationState.CLARIFYING)
            return

        if self.hypothesis_components["independent_variable"] is None:
            response = self._get_user_input(f"Okay, regarding '{self.hypothesis_components['general_topic']}', what specific factor or variable are you thinking of changing or manipulating? This will be your independent variable. (Separate multiple with ';')")
            self.hypothesis_components["independent_variable"] = response
            return

        if self.hypothesis_components["dependent_variable"] is None:
            response = self._get_user_input(f"And what measurable outcome or effect do you expect to observe when you change '{self.hypothesis_components['independent_variable']}'? This will be your dependent variable. (Separate multiple with ';')")
            self.hypothesis_components["dependent_variable"] = response
            return

        if self.hypothesis_components["mechanism"] is None:
            response = self._get_user_input(f"Why do you expect that changing '{self.hypothesis_components['independent_variable']}' will lead to an observable change in '{self.hypothesis_components['dependent_variable']}'? What is the underlying reason or assumption (because of Z)? (Separate multiple assumptions with ';')")
            self.hypothesis_components["mechanism"] = response
            self.state_machine.transition_to(ConversationState.REFINING)
            return

    def _refine_hypothesis(self):
        # Construct the hypothesis statement
        iv = self.hypothesis_components['independent_variable']
        dv = self.hypothesis_components['dependent_variable']
        m = self.hypothesis_components['mechanism']

        if not all([iv, dv, m]):
            logger.warning("Attempted to refine hypothesis with missing components.") # Using logger
            print("Agent: It seems we are missing some key components of the hypothesis. Let's go back to clarifying.")
            # Find the first missing component and transition back to CLARIFYING
            # This logic can be more sophisticated
            if self.hypothesis_components["independent_variable"] is None:
                 self.hypothesis_components["general_topic"] = None
            elif self.hypothesis_components["dependent_variable"] is None:
                 self.hypothesis_components["independent_variable"] = None
            else:
                 self.hypothesis_components["dependent_variable"] = None
            self.state_machine.transition_to(ConversationState.CLARIFYING)
            return

        constructed_statement = f"If we change the {iv}, then we will observe a change in the {dv}, because {m}."
        self.hypothesis_components["full_statement"] = constructed_statement

        logger.info(f"Constructed hypothesis statement: {constructed_statement}") # Using logger
        print(f"Agent: Here's a potential hypothesis statement based on our discussion:")
        print(f"'{constructed_statement}'")
        self.state_machine.transition_to(ConversationState.AWAITING_CONFIRMATION)

    def _await_confirmation(self):
        response = self._get_user_input("Does this accurately capture your intended hypothesis? (yes/no)")
        if response.lower() == 'yes':
            self.user_confirmed_hypothesis = True
            logger.info("User confirmed hypothesis.") # Using logger
            print("Agent: Great! Hypothesis confirmed.")
            self.state_machine.transition_to(ConversationState.FINALIZED)
        else:
            logger.info("User rejected hypothesis statement. Returning to CLARIFYING to re-input components.")
            print("Agent: Okay, let's get the new details for the hypothesis.")
            # Reset components to force re-asking
            self.hypothesis_components["independent_variable"] = None
            self.hypothesis_components["dependent_variable"] = None
            self.hypothesis_components["mechanism"] = None
            self.hypothesis_components["full_statement"] = None
            self.state_machine.transition_to(ConversationState.CLARIFYING) # Go to CLARIFYING


    def structure_hypothesis(self):
        if not self.user_confirmed_hypothesis or not self.hypothesis_components["full_statement"]:
            logger.warning("Structure hypothesis called but hypothesis not confirmed or statement missing.") # Using logger
            print("Agent: Cannot structure hypothesis. It has not been finalized or is incomplete.")
            return None

        # For key_variables, we'll assume single strings for now, convert to list of one.
        # For core_assumptions, we'll use the 'mechanism' component.
        # If multiple assumptions were provided (e.g. semicolon separated), split them.

        iv_list = [var.strip() for var in self.hypothesis_components["independent_variable"].split(';') if var.strip()]
        dv_list = [var.strip() for var in self.hypothesis_components["dependent_variable"].split(';') if var.strip()]
        assumptions_list = [asm.strip() for asm in self.hypothesis_components["mechanism"].split(';') if asm.strip()]


        hypothesis_data = {
            "hypothesis_id": str(uuid.uuid4()),
            "statement": self.hypothesis_components["full_statement"],
            "key_variables": {
                "independent": iv_list if iv_list else [self.hypothesis_components["independent_variable"]], # Fallback if no semicolon
                "dependent": dv_list if dv_list else [self.hypothesis_components["dependent_variable"]]    # Fallback if no semicolon
            },
            "core_assumptions": assumptions_list if assumptions_list else [self.hypothesis_components["mechanism"]], # Fallback if no semicolon
            "status": "unverified"
        }
        self.final_hypothesis_json = json.dumps(hypothesis_data, indent=4)
        logger.info("Hypothesis structured into JSON format.") # Using logger
        # print("Agent: Hypothesis structured into JSON format.") # Replaced by logger
        return self.final_hypothesis_json

    def initiate_experiment_design(self, hypothesis_json_payload): # New method
        if not hypothesis_json_payload:
            logger.error("initiate_experiment_design called with no payload.")
            return

        logger.info("Placeholder: initiate_experiment_design called.")
        logger.info(f"Payload to be sent to Agent 2 (Experiment Designer):\n{hypothesis_json_payload}")
        # In a real scenario, this would make an API call to Agent 2.
        # For now, it just logs the payload.
        print("Agent: Handing off to Agent 2 (simulated - logged payload).")


    def run_interaction_loop(self):
        logger.info("Starting Hypothesis Builder interaction loop.") # Using logger
        print("Agent: Hello! I'm Agent 1: Hypothesis Builder. I'll help you create a falsifiable hypothesis.")

        while self.state_machine.current_state != ConversationState.FINALIZED:
            current_state_value = self.state_machine.current_state
            # Using logger for state transitions (already in state_machine.py, but good for context here too)
            logger.debug(f"Interaction loop: Current State: {current_state_value.value}")
            print(f"--- Current State: {current_state_value.value} ---")


            if current_state_value == ConversationState.AWAITING_INPUT:
                # In this version, AWAITING_INPUT implicitly transitions to CLARIFYING
                # by calling _ask_clarifying_questions which will ask the first question.
                self._ask_clarifying_questions()
            elif current_state_value == ConversationState.CLARIFYING:
                self._ask_clarifying_questions()
            elif current_state_value == ConversationState.REFINING:
                self._refine_hypothesis()
            elif current_state_value == ConversationState.AWAITING_CONFIRMATION:
                self._await_confirmation()
            else:
                logger.error(f"Unhandled state in interaction loop: {current_state_value.value}") # Using logger
                print(f"Agent: Error - Unhandled state: {current_state_value.value}")
                break

        if self.user_confirmed_hypothesis and self.hypothesis_components["full_statement"]:
            logger.info("Hypothesis formulation complete.") # Using logger
            # print("Agent: Hypothesis formulation complete.") # Replaced by logger
            self.structure_hypothesis()
            if self.final_hypothesis_json:
                logger.info("Preparing for handoff to Agent 2.") # Using logger
                # print("Agent: Preparing for handoff to Agent 2...") # Replaced by logger
                self.initiate_experiment_design(self.final_hypothesis_json) # Call the new method
        else:
            logger.info("Exiting hypothesis formulation. No hypothesis was finalized.") # Using logger
            # print("Agent: Exiting hypothesis formulation. No hypothesis was finalized.") # Replaced by logger

# Example usage (will be moved to main.py later)
if __name__ == '__main__':
    # Basic configuration for logger when run as main
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    builder = HypothesisBuilder()
    builder.run_interaction_loop()

    if builder.final_hypothesis_json:
        print("\n--- Final Structured Hypothesis (JSON) ---")
        print(builder.final_hypothesis_json)
    elif builder.user_confirmed_hypothesis:
        print("\n--- Final Hypothesis Components (Raw) ---")
        for key, value in builder.hypothesis_components.items():
            print(f"{key}: {value}")
