from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class FetchOptions:
    force_refetch: bool
    max_bytes: int
    timeout_ms: int


@dataclass(frozen=True)
class FetchRequest:
    v: int
    request_id: str
    serp_query_id: str
    rank: int
    url: str
    fetch_timestamp: str
    tenant_id: str
    trace: Dict[str, Any]
    options: FetchOptions

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "FetchRequest":
        opts = d.get("options", {})
        return FetchRequest(
            v=int(d["v"]),
            request_id=d["request_id"],
            serp_query_id=d.get("serp_query_id", "SERP-UNSET"),
            rank=int(d.get("rank", 0)),
            url=d["url"],
            fetch_timestamp=d["fetch_timestamp"],
            tenant_id=d.get("tenant_id", "T-UNSET"),
            trace=d.get("trace", {}),
            options=FetchOptions(
                force_refetch=bool(opts.get("force_refetch", False)),
                max_bytes=int(opts.get("max_bytes", 5_242_880)),
                timeout_ms=int(opts.get("timeout_ms", 20_000)),
            ),
        )
