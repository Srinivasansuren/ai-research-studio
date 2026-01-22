# app/pipeline/contracts.py
from typing import Dict, Any


class FetchRequestV1:
    VERSION = "v1"

    def __init__(
        self,
        *,
        url: str,
        request_id: str,
        fetch_timestamp: str,
        rank: int,
        serp_query_id: str,
        options: Dict[str, Any] | None = None,
    ):
        self.url = url
        self.request_id = request_id
        self.fetch_timestamp = fetch_timestamp
        self.rank = rank
        self.serp_query_id = serp_query_id
        self.options = options or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.VERSION,
            "url": self.url,
            "request_id": self.request_id,
            "fetch_timestamp": self.fetch_timestamp,
            "rank": self.rank,
            "serp_query_id": self.serp_query_id,
            "options": self.options,
        }
