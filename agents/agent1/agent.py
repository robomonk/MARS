import uuid
from agents.agent1.session_manager import SessionManager

class Agent1:
    """
    Agent1 class that handles user interactions, manages session state,
    and saves hypotheses using SessionManager.
    """
    def __init__(self, session_id: str = None):
        """
        Initializes Agent1.

        Args:
            session_id (str, optional): An existing session ID to resume.
                                        If None, a new session ID is generated.
        """
        self.session_manager = SessionManager() # Assumes SessionManager can be initialized
                                                # without args or handles its own client setup.

        if not self.session_manager.db:
            print("Warning: Agent1 initialized, but SessionManager has no Firestore client. "
                  "Session operations will not be persisted.")

        self.session_id = session_id if session_id else str(uuid.uuid4())
        self.current_state = "START"
        self.conversation_history = []
        self.hypothesis_drafts = []
        self.message_count = 0 # To simulate state changes

        print(f"Agent1 initialized with session ID: {self.session_id}")
        # Optionally, load existing session data if session_id was provided
        # self._load_session() # Placeholder for potential future load logic

    def _add_message_to_history(self, role: str, content: str):
        """Helper to add a message to the conversation history."""
        self.conversation_history.append({"role": role, "content": content})

    def handle_message(self, user_message_content: str) -> str:
        """
        Handles an incoming user message, updates state, persists session,
        and potentially saves a finalized hypothesis.

        Args:
            user_message_content (str): The content of the user's message.

        Returns:
            str: A response to the user.
        """
        self._add_message_to_history("user", user_message_content)
        self.message_count += 1
        assistant_response_content = "Message processed."

        # Mock logic for state and hypothesis draft updates
        if self.current_state == "START":
            self.current_state = "PROCESSING_USER_INPUT"
            self.hypothesis_drafts.append({"id": f"draft_{self.message_count}", "text": f"Draft based on '{user_message_content[:20]}...'"})
            assistant_response_content = f"Thanks for your message: '{user_message_content}'. I'm processing it."
        elif self.current_state == "PROCESSING_USER_INPUT":
            self.current_state = "GENERATING_HYPOTHESIS"
            self.hypothesis_drafts[-1]["text"] += " - further elaborated."
            assistant_response_content = "I'm now generating a hypothesis draft."
        elif self.current_state == "GENERATING_HYPOTHESIS":
            self.current_state = "AWAITING_FEEDBACK"
            assistant_response_content = f"Here is a draft: {self.hypothesis_drafts[-1]}. What are your thoughts?"

        # Mock condition to enter FINALIZED state (e.g., after 3 messages or specific keyword)
        if user_message_content.lower() == "finalize please" or self.message_count >= 3:
            if self.current_state != "FINALIZED": # Avoid multiple finalizations if already in state
                self.current_state = "FINALIZED"
                assistant_response_content = "Finalizing the hypothesis based on our conversation."
                print(f"Agent state changed to FINALIZED for session {self.session_id}")


        self._add_message_to_history("assistant", assistant_response_content)

        # Persist session
        if self.session_manager.db: # Only attempt if client is available
            self.session_manager.update_session(
                session_id=self.session_id,
                conversation_history=self.conversation_history,
                current_state=self.current_state,
                hypothesis_drafts=self.hypothesis_drafts
            )
        else:
            print("Skipping session update as Firestore client is not available.")

        # Handle finalized state
        if self.current_state == "FINALIZED":
            mock_final_hypothesis = {
                "title": f"Final Hypothesis for Session {self.session_id}",
                "summary": f"Based on {self.message_count} interactions.",
                "details": self.hypothesis_drafts[-1] if self.hypothesis_drafts else "No drafts available.",
                "conversation_summary": [msg["content"] for msg in self.conversation_history]
            }
            if self.session_manager.db: # Only attempt if client is available
                print(f"Attempting to save final hypothesis for session {self.session_id}...")
                saved_id = self.session_manager.save_final_hypothesis(self.session_id, mock_final_hypothesis)
                if saved_id:
                    assistant_response_content += f" Hypothesis saved with ID: {saved_id}."
                else:
                    assistant_response_content += " Failed to save hypothesis to Firestore."
            else:
                print("Skipping final hypothesis saving as Firestore client is not available.")
            # Potentially reset state or drafts after finalization if needed for the agent's lifecycle
            # self.current_state = "SESSION_ENDED"
            # self.hypothesis_drafts = []

        return assistant_response_content

if __name__ == '__main__':
    print("Starting Agent1 example usage...")
    # Note: Firestore operations will likely fail if Google Cloud ADC are not set up.
    # The SessionManager and firestore_client.py have fallbacks/warnings for this.

    agent = Agent1()

    print("\n--- Interaction 1 ---")
    response1 = agent.handle_message("Tell me about climate change impacts on agriculture.")
    print(f"Agent Response: {response1}")
    print(f"Current State: {agent.current_state}")
    print(f"History: {agent.conversation_history[-2:]}") # Last user and assistant message
    print(f"Drafts: {agent.hypothesis_drafts}")

    print("\n--- Interaction 2 ---")
    response2 = agent.handle_message("That's interesting, what are some mitigation strategies?")
    print(f"Agent Response: {response2}")
    print(f"Current State: {agent.current_state}")
    print(f"History: {agent.conversation_history[-2:]}")
    print(f"Drafts: {agent.hypothesis_drafts}")

    print("\n--- Interaction 3 (triggering FINALIZED state) ---")
    # This message will trigger finalization due to message_count >= 3
    response3 = agent.handle_message("Okay, that sounds good enough. Finalize please.")
    print(f"Agent Response: {response3}")
    print(f"Current State: {agent.current_state}")
    print(f"History: {agent.conversation_history[-2:]}")
    print(f"Drafts: {agent.hypothesis_drafts}")

    # Example of starting agent with existing session_id (won't load data in this simple version)
    # print("\n--- Starting agent with existing session ID (no load implemented) ---")
    # existing_session_agent = Agent1(session_id=agent.session_id)
    # print(f"Agent for existing session {existing_session_agent.session_id} created.")
    # response4 = existing_session_agent.handle_message("Can you add more details about carbon sequestration?")
    # print(f"Agent Response: {response4}")

    print("\nExample usage finished.")
