from __future__ import annotations

import base64
import json
import asyncio
import logging

from fastapi import APIRouter, HTTPException, Request, Depends

from app.config import Settings, get_settings
from app.logging import get_logger
from app.state.firestore import get_db
from app.state.dedupe import claim_idempotency
from app.state.jobs import (
    ensure_job_initialized,
    set_urls_and_mark_fetch_requested,
)
from app.external.serpapi import SerpApiClient
from app.pubsub.publisher import PubSubPublisher
from app.contracts.fetcher_contract import build_fetch_request_message

router = APIRouter()
log = get_logger("pipeline-runner.jobs")

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def _decode_pubsub_envelope(request_json: dict) -> tuple[str, dict]:
    msg = (request_json or {}).get("message") or {}
    message_id = msg.get("messageId") or msg.get("message_id") or "unknown"
    data_b64 = msg.get("data")

    if not data_b64:
        raise HTTPException(status_code=400, detail="Missing Pub/Sub data")

    raw = base64.b64decode(data_b64).decode("utf-8")
    payload = json.loads(raw)
    return message_id, payload


# -------------------------------------------------------------------
# Background worker (NON-BLOCKING, SAFE)
# -------------------------------------------------------------------

async def _process_job_async(
    *,
    settings: Settings,
    tenant_id: str,
    job_id: str,
    conversation_id: str,
    user_prompt: str,
    serp: dict,
):
    try:
        log.info(
            "JOB_START async begin",
            extra={"tenant_id": tenant_id, "job_id": job_id},
        )

        db = get_db(settings.project_id, settings.firestore_database)

        query = serp.get("query") or user_prompt
        top_n = int(serp.get("top_n") or settings.serpapi_top_n)
        top_n = min(top_n, settings.max_urls_hard_cap)

        serpapi_spec = {
            "query": query,
            "top_n": top_n,
            "engine": settings.serpapi_engine,
            "gl": settings.serpapi_gl,
            "hl": settings.serpapi_hl,
        }

        # Initialize job (transaction)
        txn = db.transaction()
        ensure_job_initialized(
            transaction=txn,
            db=db,
            tenant_id=tenant_id,
            job_id=job_id,
            conversation_id=conversation_id,
            user_prompt=user_prompt,
            pipeline_version=settings.runner_pipeline_version,
            serpapi_spec=serpapi_spec,
        )

        # Discover URLs (BLOCKING IO → off request thread)
        serp_client = SerpApiClient(
            api_key=settings.serpapi_api_key,
            engine=settings.serpapi_engine,
            gl=settings.serpapi_gl,
            hl=settings.serpapi_hl,
        )
        urls = serp_client.search_top_urls(query=query, top_n=top_n)

        log.info(
            "SERP URLs discovered",
            extra={"job_id": job_id, "url_count": len(urls)},
        )

        # Persist URLs
        txn2 = db.transaction()
        set_urls_and_mark_fetch_requested(txn2, db, tenant_id, job_id, urls)

        # Fan-out fetch requests
        publisher = PubSubPublisher(settings.project_id)
        for i, u in enumerate(urls, start=1):
            url_id = f"URL_{i:03d}"
            publisher.publish_json(
                topic_name=settings.fetch_requests_topic,
                payload=build_fetch_request_message(
                    tenant_id=tenant_id,
                    job_id=job_id,
                    url_id=url_id,
                    url=u,
                ),
                attributes={
                    "tenant_id": tenant_id,
                    "job_id": job_id,
                    "url_id": url_id,
                },
            )

        log.info(
            "JOB_START async complete",
            extra={"tenant_id": tenant_id, "job_id": job_id, "urls": len(urls)},
        )

    except Exception as e:
        # CRITICAL: never let background task crash silently
        log.exception(
            "JOB_START async FAILED",
            extra={
                "tenant_id": tenant_id,
                "job_id": job_id,
                "error": str(e),
            },
        )


# -------------------------------------------------------------------
# Pub/Sub endpoint (EARLY ACK — ZERO TIMEOUT RISK)
# -------------------------------------------------------------------

@router.post("/pubsub/push")
@router.post("/pubsub/push/jobs")
async def pubsub_jobs(
    request: Request,
    settings: Settings = Depends(get_settings),
):
    body = await request.json()
    message_id, payload = _decode_pubsub_envelope(body)

    log.info(
        "Pub/Sub push received",
        extra={"message_id": message_id},
    )

    event_type = payload.get("event_type")
    if event_type != "JOB_START":
        log.info("Ignoring non JOB_START event", extra={"event_type": event_type})
        return {"ok": True, "ignored": True}

    tenant_id = payload.get("tenant_id")
    job_id = payload.get("job_id")
    if not tenant_id or not job_id:
        raise HTTPException(status_code=400, detail="tenant_id and job_id required")

    # Idempotency check — FAST
    db = get_db(settings.project_id, settings.firestore_database)
    if not claim_idempotency(db, tenant_id, job_id, f"jobs:{message_id}"):
        log.info(
            "Duplicate Pub/Sub message ignored",
            extra={"tenant_id": tenant_id, "job_id": job_id},
        )
        return {"ok": True, "deduped": True}

    p = payload.get("payload") or {}

    # 🚀 EARLY ACK — Cloud Run returns immediately
    asyncio.create_task(
        _process_job_async(
            settings=settings,
            tenant_id=tenant_id,
            job_id=job_id,
            conversation_id=p.get("conversation_id") or "",
            user_prompt=p.get("user_prompt") or "",
            serp=p.get("serpapi") or {},
        )
    )

    log.info(
        "JOB_START accepted (early ack)",
        extra={"tenant_id": tenant_id, "job_id": job_id},
    )

    return {"ok": True, "job_id": job_id}
