import json
from typing import Dict, Any
from google.cloud import storage


class GcsEvidenceWriter:
    def __init__(self, bucket_name: str):
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)

    @staticmethod
    def build_prefix(fetch_timestamp: str, request_id: str) -> str:
        y, m, d, h = fetch_timestamp[:4], fetch_timestamp[5:7], fetch_timestamp[8:10], fetch_timestamp[11:13]
        return f"evidence/v1/fetch/{y}/{m}/{d}/{h}/{request_id}/"

    def exists(self, obj: str) -> bool:
        return self.bucket.blob(obj).exists()

    def write_bytes(self, name: str, data: bytes, content_type: str):
        self.bucket.blob(name).upload_from_string(data, content_type=content_type)

    def write_text(self, name: str, text: str):
        self.write_bytes(name, text.encode("utf-8"), "text/plain; charset=utf-8")

    def write_json(self, name: str, obj: Dict[str, Any]):
        self.write_bytes(name, json.dumps(obj, indent=2).encode("utf-8"), "application/json")
