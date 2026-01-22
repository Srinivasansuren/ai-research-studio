from __future__ import annotations

import base64
import json
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Request, Depends
from google.cloud import firestore, storage

from app.config import Settings, get_settings
from app.logging import get_logger
from app.state.firestore import get_db
from app.state.dedupe import claim_idempotency
from app.state.jobs import (
    mark_evidence_written,
    is_job_evidence_complete,
    job_ref,
)
from app.pubsub.publisher import PubSubPublisher

router = APIRouter()
log = get_logger("pipeline-runner.evidence")


def _decode_pubsub_envelope(request_json: dict) -> tuple[str, dict]:
    msg = (request_json or {}).get("message") or {}
    message_id = msg.get("messageId") or msg.get("message_id") or "unknown"
    data_b64 = msg.get("data")
    if not data_b64:
        raise HTTPException(status_code=400, detail="Missing Pub/Sub data")

    raw = base64.b64decode(data_b64).decode("utf-8")
    payload = json.loads(raw)
    return message_id, payload


def _parse_job_from_object(object_name: str) -> tuple[str | None, str | None, str | None]:
    parts = object_name.split("/")
    if len(parts) < 6:
        return None, None, None

    try:
        t_idx = parts.index("tenants")
        j_idx = parts.index("jobs")
        e_idx = parts.index("evidence")
        tenant_id = parts[t_idx + 1]
        job_id = parts[j_idx + 1]
        url_id = parts[e_idx + 1]
        return tenant_id, job_id, url_id
    except (ValueError, IndexError):
        return None, None, None


def _load_gcs_text(bucket: storage.Bucket, obj: str) -> str:
    return bucket.blob(obj).download_as_text(encoding="utf-8")


def _load_gcs_json(bucket: storage.Bucket, obj: str) -> Dict[str, Any]:
    return json.loads(bucket.blob(obj).download_as_text(encoding="utf-8"))


@router.post("/pubsub/push/evidence")
async def pubsub_evidence(
    request: Request,
    settings: Settings = Depends(get_settings),
):
    body = await request.json()
    message_id, payload = _decode_pubsub_envelope(body)

    event_type = payload.get("event_type")
    if event_type != "EVIDENCE_OBJECT_WRITTEN":
        return {"ok": True, "ignored": True, "event_type": event_type}

    p = payload.get("payload") or {}
    bucket_name = p.get("bucket")
    obj = p.get("object")
    if not bucket_name or not obj:
        raise HTTPException(status_code=400, detail="bucket/object required")

    tenant_id, job_id, url_id = _parse_job_from_object(obj)
    if not tenant_id or not job_id or not url_id:
        return {"ok": True, "ignored": True, "reason": "unparseable_object_name"}

    db = get_db(settings.project_id, settings.firestore_database)

    if not claim_idempotency(db, tenant_id, job_id, f"evidence:{message_id}"):
        return {"ok": True, "deduped": True}

    txn = db.transaction()
    res = mark_evidence_written(
        txn,
        db,
        tenant_id,
        job_id,
        url_id,
        raw_object=obj,
    )

    if not res.get("job_exists"):
        return {"ok": True, "ignored": True, "reason": "job_missing"}

    snap = job_ref(db, tenant_id, job_id).get()
    job_doc = snap.to_dict() or {}

    if not is_job_evidence_complete(job_doc):
        return {"ok": True, "job_id": job_id, "url_id": url_id}

    # ---------------------------
    # PHASE VI — SYNTHESIS TRIGGER
    # ---------------------------

    evidence_items = job_doc.get("evidence", {}).get("items", {})
    urls_list = job_doc.get("urls", {}).get("list", [])

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    ordered_evidence = []

    for u in urls_list:
        url_id = u["url_id"]
        ev = evidence_items.get(url_id)
        if not ev:
            continue

        raw_object = ev["raw_object"]
        prefix = raw_object.rsplit("/", 1)[0] + "/"

        meta = _load_gcs_json(bucket, prefix + "meta.json")
        clean_text = _load_gcs_text(bucket, prefix + "clean.txt")

        ordered_evidence.append({
            "source_url": ev["url"],
            "snapshot_gcs_path": f"gs://{bucket_name}/{prefix}",
            "fetched_at": meta["fetched_at"],
            "checksum": meta["hash_raw"],
            "cleaned_text": clean_text,
        })

    publisher = PubSubPublisher(settings.project_id)
    publisher.publish_json(
        topic_name=settings.perplexity_synth_topic,
        payload={
            "schema_version": "perplexity_synth_request.v1",
            "tenant_id": tenant_id,
            "job_id": job_id,
            "conversation_id": job_doc.get("conversation_id"),
            "pipeline_version": job_doc.get("pipeline_version"),
            "prompt_version": settings.perplexity_prompt_version,
            "evidence": ordered_evidence,
        },
    )

    job_ref(db, tenant_id, job_id).update(
        {
            "updated_at": firestore.SERVER_TIMESTAMP,
            "status": "EVIDENCE_READY",
        }
    )

    log.info("Phase VI triggered", extra={"tenant_id": tenant_id, "job_id": job_id})

    return {"ok": True, "job_id": job_id, "phase": "PHASE_VI"}
