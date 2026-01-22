import requests
import time
import hashlib
from dataclasses import dataclass
from typing import Dict


@dataclass
class FetchResult:
    status: int
    final_url: str
    headers: Dict[str, str]
    raw_bytes: bytes
    truncated: bool
    elapsed_ms: int
    content_type: str


def fetch_url_streaming(url: str, *, max_bytes: int, timeout_ms: int) -> FetchResult:
    start = time.time()
    headers = {"User-Agent": "ai-research-studio-fetcher/1.0"}
    timeout = timeout_ms / 1000.0

    with requests.get(url, headers=headers, stream=True, timeout=(timeout, timeout)) as r:
        chunks = []
        total = 0
        truncated = False

        for chunk in r.iter_content(chunk_size=64 * 1024):
            if not chunk:
                continue
            if total + len(chunk) > max_bytes:
                remain = max_bytes - total
                if remain > 0:
                    chunks.append(chunk[:remain])
                truncated = True
                break
            chunks.append(chunk)
            total += len(chunk)

        raw = b"".join(chunks)

    return FetchResult(
        status=r.status_code,
        final_url=r.url,
        headers={k: v for k, v in r.headers.items()},
        raw_bytes=raw,
        truncated=truncated,
        elapsed_ms=int((time.time() - start) * 1000),
        content_type=r.headers.get("Content-Type", ""),
    )


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()
