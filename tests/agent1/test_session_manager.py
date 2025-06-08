import unittest
from unittest.mock import MagicMock, patch, ANY

from google.cloud.firestore_v1 import Client as FirestoreClient
from google.cloud.firestore_v1.collection import CollectionReference
from google.cloud.firestore_v1.document import DocumentReference
from google.cloud import firestore as google_firestore

from agents.agent1.session_manager import SessionManager

class TestSessionManager(unittest.TestCase):

    def setUp(self):
        self.mock_firestore_client_instance = MagicMock(spec=FirestoreClient)

        self.mock_sessions_collection_ref = MagicMock(spec=CollectionReference)
        self.mock_session_doc_ref = MagicMock(spec=DocumentReference)

        self.mock_finalized_collection_ref = MagicMock(spec=CollectionReference)
        self.mock_final_hypothesis_doc_ref = MagicMock(spec=DocumentReference)
        self.mock_final_hypothesis_doc_ref.id = "mock_final_hypothesis_id_123"

        def collection_side_effect(collection_name):
            if collection_name == u'hypothesis_sessions':
                return self.mock_sessions_collection_ref
            elif collection_name == u'finalized_hypotheses':
                return self.mock_finalized_collection_ref
            return MagicMock()

        self.mock_firestore_client_instance.collection.side_effect = collection_side_effect

        self.mock_sessions_collection_ref.document.return_value = self.mock_session_doc_ref
        self.mock_finalized_collection_ref.add.return_value = (MagicMock(spec=google_firestore.SERVER_TIMESTAMP), self.mock_final_hypothesis_doc_ref)

        # Patch firestore.Client constructor used in SessionManager.__init__ fallback
        patcher_client_constructor = patch('agents.agent1.session_manager.firestore.Client')
        self.mock_client_constructor = patcher_client_constructor.start()
        self.mock_client_constructor.return_value = self.mock_firestore_client_instance
        self.addCleanup(patcher_client_constructor.stop)

        # Patch the global 'db' object imported at module level in session_manager.py
        # 'create=True' makes sure the patch works even if 'db' isn't there initially (e.g. import error)
        patcher_db_module_level = patch('agents.agent1.session_manager.db', self.mock_firestore_client_instance, create=True)
        self.mock_db_module_level = patcher_db_module_level.start()
        self.addCleanup(patcher_db_module_level.stop)

        # Standard SessionManager instance for most tests, should use the mocks above
        self.session_manager = SessionManager()
        # Explicitly set its db to our main mock to simplify reasoning about which client is used
        self.session_manager.db = self.mock_firestore_client_instance


    def test_update_session_creates_or_updates_document(self):
        session_id = "test_session_001"
        conversation_history = [{"role": "user", "content": "Hello"}]
        current_state = "PROCESSING"
        hypothesis_drafts = [{"id": "d1", "text": "Draft 1"}]

        result = self.session_manager.update_session(session_id, conversation_history, current_state, hypothesis_drafts)

        self.assertTrue(result)
        self.mock_firestore_client_instance.collection.assert_any_call(u'hypothesis_sessions')
        self.mock_sessions_collection_ref.document.assert_called_once_with(session_id)
        expected_data = {
            u'conversation_history': conversation_history,
            u'current_state': current_state,
            u'hypothesis_drafts': hypothesis_drafts,
            u'last_updated': ANY
        }
        self.mock_session_doc_ref.set.assert_called_once_with(expected_data, merge=True)

    def test_update_session_handles_firestore_errors(self):
        self.mock_session_doc_ref.set.side_effect = Exception("Firestore network error")
        session_id = "test_session_002"
        result = self.session_manager.update_session(session_id, [], "ERROR_STATE", [])
        self.assertFalse(result)

    def test_update_session_no_client(self):
        with patch('agents.agent1.session_manager.db', None), \
             patch('agents.agent1.session_manager.firestore.Client') as mock_constructor_fails:

            mock_constructor_fails.side_effect = Exception("No client available")

            manager_no_client = SessionManager(firestore_client=None)
            self.assertIsNone(manager_no_client.db, "SessionManager's db attribute should be None if all init paths fail.")

            result = manager_no_client.update_session("test_session_003", [], "STATE", [])
            self.assertFalse(result)

    def test_update_session_no_session_id(self):
        result_none = self.session_manager.update_session(None, [], "STATE", [])
        self.assertFalse(result_none)
        result_empty = self.session_manager.update_session("", [], "STATE", [])
        self.assertFalse(result_empty)

    def test_save_final_hypothesis_adds_document(self):
        session_id = "test_session_004"
        final_hypothesis = {"title": "Final Hypo", "details": "It's good."}
        returned_id = self.session_manager.save_final_hypothesis(session_id, final_hypothesis)

        self.assertEqual(returned_id, "mock_final_hypothesis_id_123")
        self.mock_firestore_client_instance.collection.assert_any_call(u'finalized_hypotheses')
        expected_data = {
            u'session_id': session_id,
            u'hypothesis_content': final_hypothesis,
            u'saved_at': ANY
        }
        self.mock_finalized_collection_ref.add.assert_called_once_with(expected_data)

    def test_save_final_hypothesis_returns_id(self):
        session_id = "test_session_005"
        final_hypothesis = {"title": "Another Hypo"}
        returned_id = self.session_manager.save_final_hypothesis(session_id, final_hypothesis)
        self.assertEqual(returned_id, "mock_final_hypothesis_id_123")

    def test_save_final_hypothesis_handles_firestore_errors(self):
        self.mock_finalized_collection_ref.add.side_effect = Exception("Firestore network error on add")
        session_id = "test_session_006"
        final_hypothesis = {"title": "Error Hypo"}
        returned_id = self.session_manager.save_final_hypothesis(session_id, final_hypothesis)
        self.assertIsNone(returned_id)

    def test_save_final_hypothesis_no_client(self):
        with patch('agents.agent1.session_manager.db', None), \
             patch('agents.agent1.session_manager.firestore.Client') as mock_constructor_fails:

            mock_constructor_fails.side_effect = Exception("No client available")

            manager_no_client = SessionManager(firestore_client=None)
            self.assertIsNone(manager_no_client.db, "SessionManager's db attribute should be None if all init paths fail.")

            returned_id = manager_no_client.save_final_hypothesis("test_session_007", {"title": "Hypo"})
            self.assertIsNone(returned_id)

    def test_save_final_hypothesis_invalid_inputs(self):
        result_no_sid = self.session_manager.save_final_hypothesis(None, {"title": "Hypo"})
        self.assertIsNone(result_no_sid)
        result_empty_sid = self.session_manager.save_final_hypothesis("", {"title": "Hypo"})
        self.assertIsNone(result_empty_sid)

        result_no_hypo = self.session_manager.save_final_hypothesis("sid", None)
        self.assertIsNone(result_no_hypo)
        result_empty_hypo = self.session_manager.save_final_hypothesis("sid", {})
        self.assertIsNone(result_empty_hypo)

        result_wrong_type_hypo = self.session_manager.save_final_hypothesis("sid", "not a dict")
        self.assertIsNone(result_wrong_type_hypo)

if __name__ == '__main__':
    unittest.main()
