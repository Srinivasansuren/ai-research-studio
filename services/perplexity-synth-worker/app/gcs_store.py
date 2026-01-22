import json
from google.cloud import storage
from typing import Tuple

def write_json_if_absent(bucket_name: str, object_name: str, payload: dict) -> Tuple[str, bool]:
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(object_name)

    if blob.exists(client=client):
        return f"gs://{bucket_name}/{object_name}", False

    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    blob.upload_from_string(data, content_type="application/json")
    return f"gs://{bucket_name}/{object_name}", True
