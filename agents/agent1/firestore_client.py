# Imports the Google Cloud client library
from google.cloud import firestore

# TODO: Set the project ID.
# project_id = "your-project-id"

# Instantiates a client
try:
    db = firestore.Client()
    # If you need to specify project_id:
    # db = firestore.Client(project=project_id)
    print("Firestore client initialized successfully.")

    # Example: Add data
    # doc_ref = db.collection(u'users').document(u'alovelace')
    # doc_ref.set({
    #     u'first': u'Ada',
    #     u'last': u'Lovelace',
    #     u'born': 1815
    # })
    # print("Data added to Firestore.")

except Exception as e:
    print(f"Error initializing Firestore client or interacting with Firestore: {e}")
