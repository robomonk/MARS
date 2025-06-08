from google.cloud import firestore
import uuid # For generating unique IDs if needed, though Firestore can auto-generate

# Attempt to import the pre-initialized db client from firestore_client.py
# This assumes firestore_client.py handles initialization and credential setup.
# In a production scenario, credential management would be more robust.
try:
    from agents.agent1.firestore_client import db
except ImportError:
    print("Warning: Could not import 'db' from agents.agent1.firestore_client. Initializing a new client.")
    # Fallback to initialize a new client if 'db' is not available.
    # This will likely fail without proper ADC setup, as seen in the previous subtask.
    try:
        db = firestore.Client()
        print("Fallback Firestore client initialized.")
    except Exception as e:
        db = None
        print(f"Error initializing fallback Firestore client: {e}")

class SessionManager:
    """
    Manages user sessions, conversation history, and finalized hypotheses using Firestore.
    """
    def __init__(self, project_id: str = None, firestore_client=None):
        """
        Initializes the SessionManager.

        Args:
            project_id (str, optional): The Google Cloud project ID.
                                         If not provided, the client will try to infer it.
            firestore_client (firestore.Client, optional): An existing Firestore client instance.
                                                           If None, a new client is initialized.
        """
        if firestore_client:
            self.db = firestore_client
        elif db: # Use the imported db if available and no specific client is passed
            self.db = db
        else:
            try:
                # If no client was passed and the global 'db' is not available or failed
                self.db = firestore.Client(project=project_id) if project_id else firestore.Client()
                print("SessionManager initialized a new Firestore client.")
            except Exception as e:
                self.db = None
                print(f"Error initializing Firestore client in SessionManager: {e}")
                # Potentially raise the exception or handle it as per application requirements
                # raise

        if not self.db:
            print("Error: SessionManager could not obtain a Firestore client. Operations will fail.")
            # Depending on requirements, this could raise an exception.
            # For now, it will allow object creation but operations will fail.

    def update_session(self, session_id: str, conversation_history: list, current_state: str, hypothesis_drafts: list):
        """
        Creates or updates a session document in Firestore in the 'hypothesis_sessions' collection.

        Args:
            session_id (str): The unique identifier for the session.
            conversation_history (list): A list of messages exchanged.
            current_state (str): The current state of the state machine.
            hypothesis_drafts (list): A list or dictionary of hypothesis drafts.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        if not self.db:
            print("Error: Firestore client not available in SessionManager. Cannot update session.")
            return False

        if not session_id:
            print("Error: session_id must be provided for update_session.")
            return False

        try:
            session_doc_ref = self.db.collection(u'hypothesis_sessions').document(session_id)
            session_data = {
                u'conversation_history': conversation_history,
                u'current_state': current_state,
                u'hypothesis_drafts': hypothesis_drafts,
                u'last_updated': firestore.SERVER_TIMESTAMP
            }
            session_doc_ref.set(session_data, merge=True)
            print(f"Session '{session_id}' updated successfully in Firestore.")
            return True
        except Exception as e:
            print(f"Error updating session '{session_id}' in Firestore: {e}")
            return False

    def save_final_hypothesis(self, session_id: str, final_hypothesis: dict):
        """
        Saves a finalized hypothesis to the 'finalized_hypotheses' collection in Firestore.
        A new document with an auto-generated ID is created for each hypothesis.

        Args:
            session_id (str): The identifier of the session this hypothesis belongs to.
            final_hypothesis (dict): The finalized hypothesis data (JSON object).

        Returns:
            str or None: The ID of the newly created document if successful, None otherwise.
        """
        if not self.db:
            print("Error: Firestore client not available in SessionManager. Cannot save hypothesis.")
            return None

        if not session_id:
            print("Error: session_id must be provided for save_final_hypothesis.")
            return None

        if not final_hypothesis or not isinstance(final_hypothesis, dict):
            print("Error: final_hypothesis must be a non-empty dictionary.")
            return None

        try:
            hypothesis_data = {
                u'session_id': session_id,
                u'hypothesis_content': final_hypothesis,
                u'saved_at': firestore.SERVER_TIMESTAMP
            }
            # Add a new document with an auto-generated ID.
            update_time, doc_ref = self.db.collection(u'finalized_hypotheses').add(hypothesis_data)
            print(f"Finalized hypothesis for session '{session_id}' saved with ID '{doc_ref.id}'.")
            return doc_ref.id
        except Exception as e:
            print(f"Error saving finalized hypothesis for session '{session_id}': {e}")
            return None

if __name__ == '__main__':
    # This is example usage and will likely fail without Google Cloud authentication
    print("Attempting to use SessionManager (this will likely fail without ADC)...")

    manager = SessionManager()

    if manager.db:
        # Example data for update_session
        test_session_id = f"test_session_{uuid.uuid4()}" # Ensure unique session for testing
        test_history = [
            {"role": "user", "content": "Hello there!"},
            {"role": "assistant", "content": "Hi! How can I help you?"}
        ]
        test_state = "greeting_state"
        test_drafts = [{"id": "H1", "text": "Initial hypothesis draft."}]

        update_success = manager.update_session(test_session_id, test_history, test_state, test_drafts)
        print(f"Update session call successful: {update_success}")

        # Example data for save_final_hypothesis
        final_hypo = {
            "title": "Hypothesis Alpha",
            "details": "This is a well-formed hypothesis based on extensive research.",
            "confidence": 0.95,
            "evidence_links": ["link1", "link2"]
        }

        saved_hypo_id = manager.save_final_hypothesis(test_session_id, final_hypo)
        if saved_hypo_id:
            print(f"Saved final hypothesis with document ID: {saved_hypo_id}")
        else:
            print("Failed to save final hypothesis.")

    else:
        print("SessionManager could not be initialized with a Firestore client. Skipping example usage.")
