from __future__ import annotations

from google.cloud import firestore


def get_db(project_id: str, database: str | None = None) -> firestore.Client:
    if database:
        return firestore.Client(project=project_id, database=database)
    return firestore.Client(project=project_id)
