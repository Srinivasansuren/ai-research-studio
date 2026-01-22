import hashlib
import json
from typing import List


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def compute_request_hash(
    prompt_version: str,
    evidence_checksums_in_order: List[str],
    model: str,
    temperature: float,
    top_p: float,
    max_tokens: int,
) -> str:
    payload = {
        "prompt_version": prompt_version,
        "evidence_checksums": evidence_checksums_in_order,
        "model": model,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
    }

    canon = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return "sha256:" + sha256_hex(canon)
