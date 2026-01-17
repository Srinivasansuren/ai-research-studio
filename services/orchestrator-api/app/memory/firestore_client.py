# app/memory/firestore_client.py
from google.cloud import firestore

_db = None

def get_db():
    global _db
    if _db is None:
        _db = firestore.Client(project="ai-research-studio")
    return _db
