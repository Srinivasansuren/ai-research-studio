import json
import time
import requests
from typing import Any, Dict, List

PERPLEXITY_URL = "https://api.perplexity.ai/chat/completions"

def build_messages(prompt_version: str, evidence_blocks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    system = (
        "You are a synthesis engine.\n"
        "HARD RULES:\n"
        "- You MUST use ONLY the evidence provided in the user message.\n"
        "- You MUST NOT browse the web, request new sources, or rely on external knowledge.\n"
        "- If evidence is insufficient, output \"INSUFFICIENT EVIDENCE\" and list missing items.\n"
        "- Every claim must cite evidence IDs (E1..En).\n"
        "- Output MUST be valid JSON only. No prose.\n"
    )

    user = {
        "prompt_version": prompt_version,
        "task": {
            "output_schema": {
                "synthesized_findings": [
                    {
                        "finding_id": "F1",
                        "finding": "string",
                        "supporting_evidence_ids": ["E1"],
                        "counterpoints": ["string"],
                        "confidence": "low|medium|high",
                        "notes": "string"
                    }
                ],
                "confidence_notes": {
                    "coverage_gaps": ["string"],
                    "evidence_quality_flags": ["string"],
                    "reasoning_limits": ["string"]
                }
            }
        },
        "evidence": evidence_blocks
    }

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
    ]

def call_perplexity(api_key: str, model: str, messages: List[Dict[str, str]], timeout_s: int) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "temperature": 0,
        "top_p": 1,
        "max_tokens": 2048,
        "messages": messages,
        "search": False,  # 🔒 HARD GUARANTEE: no browsing
    }

    t0 = time.time()
    resp = requests.post(PERPLEXITY_URL, headers=headers, json=body, timeout=timeout_s)
    latency_ms = int((time.time() - t0) * 1000)

    try:
        data = resp.json()
    except Exception:
        data = {"_non_json": True, "body": resp.text}

    return {
        "status_code": resp.status_code,
        "data": data,
        "text": resp.text,
        "latency_ms": latency_ms,
    }

def is_retryable_http(code: int) -> bool:
    return code in (408, 429, 500, 502, 503, 504)
