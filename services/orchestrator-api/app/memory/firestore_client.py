# app/memory/firestore_client.py
from google.cloud import firestore
from google.auth import default
import logging

_db = None

def get_db():
    global _db
    if _db is None:
        creds, project = default()
        logging.error(
            f"[FIRESTORE DEBUG] resolved_project={project}, creds_type={creds.__class__.__name__}"
        )
        _db = firestore.Client(project=project)
    return _db
