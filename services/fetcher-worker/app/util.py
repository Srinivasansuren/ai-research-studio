import base64
import json
import datetime as dt
from typing import Dict, Any


def utc_now_iso_z() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def decode_pubsub_data(data_b64: str) -> Dict[str, Any]:
    raw = base64.b64decode(data_b64).decode("utf-8")
    return json.loads(raw)
