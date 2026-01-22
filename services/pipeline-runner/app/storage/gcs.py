from __future__ import annotations

from google.cloud import storage
from google.api_core.exceptions import PreconditionFailed


class GCSWriter:
    def __init__(self, project_id: str):
        self.client = storage.Client(project=project_id)

    def create_json_once(self, bucket: str, object_name: str, data: dict) -> bool:
        """
        Create object only if it does not exist.
        Returns True if created, False if already existed.
        """
        b = self.client.bucket(bucket)
        blob = b.blob(object_name)
        try:
            blob.upload_from_string(
                data=str(data).replace("'", '"'),
                content_type="application/json",
                if_generation_match=0,  # only create if not exists
            )
            return True
        except PreconditionFailed:
            return False
