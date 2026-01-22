from __future__ import annotations

def build_fetch_request_message(
    *,
    tenant_id: str,
    job_id: str,
    url_id: str,
    url: str,
) -> dict:
    """
    IMPORTANT:
    Edit THIS function once to match your existing fetcher-worker expected payload.
    Keep the rest of the pipeline-runner unchanged.

    Safe defaults below:
    - includes url
    - includes tenant/job/url_id for traceability
    """
    return {
        "tenant_id": tenant_id,
        "job_id": job_id,
        "url_id": url_id,
        "url": url,
    }
