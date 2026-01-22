from __future__ import annotations

import base64
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from google.cloud import firestore

from app.config import get_settings
from app.contracts import (
    PerplexitySynthesisRequestV1,
    NormalizedEvidencePackV1,
    SynthFinding,
    Citation,
    ConfidenceNotes,
    PerplexityMetadata,
)
from app.firestore_jobs import (
    job_doc_ref,
    synth_mark_in_progress,
    synth_mark_complete,
    synth_mark_failed,
    STATE_SYNTH_COMPLETE,
)
from app.gcs_store import write_json_if_absent
from app.perplexity import build_messages, call_perplexity, is_retryable_http
from app.util import compute_request_hash

router = APIRouter()
log = logging.getLogger("phase6.pubsub_synth")


def _utc_now_iso_z() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _decode_pubsub_envelope(body: dict) -> tuple[str, dict]:
    """
    Returns (message_id, payload_dict)
    """
    msg = (body or {}).get("message") or {}
    message_id = msg.get("messageId") or msg.get("message_id") or "unknown"
    data_b64 = msg.get("data")
    if not data_b64:
        raise HTTPException(status_code=400, detail="Missing Pub/Sub data")

    raw = base64.b64decode(data_b64).decode("utf-8")
    return message_id, json.loads(raw)


@router.post("/pubsub/push/synth")
async def pubsub_push_synth(request: Request):
    # 🔑 LAZY SETTINGS LOAD (Cloud Run safe)
    cfg = get_settings()

    body = await request.json()
    message_id, payload = _decode_pubsub_envelope(body)

    req = PerplexitySynthesisRequestV1(**payload)

    if not req.evidence:
        raise HTTPException(status_code=400, detail="Evidence list is empty")
    if len(req.evidence) > cfg.max_evidence_items:
        raise HTTPException(status_code=400, detail="Evidence list too large")

    for e in req.evidence:
        if len(e.cleaned_text) > cfg.max_cleaned_text_chars:
            raise HTTPException(status_code=400, detail="cleaned_text too large")

    evidence_checksums = [e.checksum for e in req.evidence]
    request_hash = compute_request_hash(
        prompt_version=req.prompt_version,
        evidence_checksums_in_order=evidence_checksums,
        model=cfg.perplexity_model,
        temperature=0,
        top_p=1,
        max_tokens=2048,
    )

    db = firestore.Client(project=cfg.project_id, database=cfg.firestore_database)
    ref = job_doc_ref(db, cfg.jobs_collection_template, req.tenant_id, req.job_id)

    txn = db.transaction()
    start = synth_mark_in_progress(
        txn, ref, request_hash, req.prompt_version, cfg.perplexity_model
    )

    if start.get("already_complete"):
        log.info(
            "Synthesis already complete (idempotent)",
            extra={
                "tenant_id": req.tenant_id,
                "job_id": req.job_id,
                "message_id": message_id,
            },
        )
        return {"ok": True, "idempotent": True, "status": STATE_SYNTH_COMPLETE}

    # Build evidence blocks with stable E1..En IDs
    evidence_blocks = []
    evidence_sources = []
    citations = []

    for idx, e in enumerate(req.evidence, start=1):
        eid = f"E{idx}"
        evidence_blocks.append(
            {
                "evidence_id": eid,
                "source_url": str(e.source_url),
                "fetched_at": e.fetched_at,
                "checksum": e.checksum,
                "cleaned_text": e.cleaned_text,
            }
        )
        evidence_sources.append(
            {
                "evidence_id": eid,
                "source_url": str(e.source_url),
                "snapshot_gcs_path": e.snapshot_gcs_path,
                "fetched_at": e.fetched_at,
                "checksum": e.checksum,
            }
        )
        citations.append(
            Citation(
                evidence_id=eid,
                source_url=str(e.source_url),
                checksum=e.checksum,
                fetched_at=e.fetched_at,
            )
        )

    messages = build_messages(req.prompt_version, evidence_blocks)

    # Call Perplexity
    try:
        resp = call_perplexity(
            cfg.perplexity_api_key,
            cfg.perplexity_model,
            messages,
            cfg.perplexity_timeout_s,
        )
    except Exception as ex:
        err = {
            "class": "PERPLEXITY_CALL_FAILED",
            "code": "EXCEPTION",
            "retryable": True,
            "message": f"{type(ex).__name__}: {str(ex)}",
        }
        txn_fail = db.transaction()
        synth_mark_failed(txn_fail, ref, request_hash, err)
        raise HTTPException(status_code=500, detail="retryable_perplexity_exception")

    status = resp["status_code"]
    latency_ms = resp.get("latency_ms")

    if status != 200:
        err = {
            "class": "PERPLEXITY_HTTP_ERROR",
            "code": status,
            "retryable": is_retryable_http(status),
            "message": (resp.get("text") or "")[:2000],
        }
        txn_fail = db.transaction()
        synth_mark_failed(txn_fail, ref, request_hash, err)

        if is_retryable_http(status):
            raise HTTPException(status_code=500, detail="retryable_perplexity_error")
        return {"ok": True, "failed": True, "retryable": False}

    data = resp["data"]
    provider_request_id = data.get("id")

    try:
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
    except Exception as ex:
        err = {
            "class": "PERPLEXITY_BAD_RESPONSE",
            "code": "BAD_JSON",
            "retryable": False,
            "message": f"{type(ex).__name__}: {str(ex)}",
        }
        txn_fail = db.transaction()
        synth_mark_failed(txn_fail, ref, request_hash, err)
        return {"ok": True, "failed": True, "reason": "bad_json"}

    findings = [
        SynthFinding(
            finding_id=f.get("finding_id") or f"F{i}",
            finding=f.get("finding", ""),
            supporting_evidence_ids=f.get("supporting_evidence_ids", []) or [],
            counterpoints=f.get("counterpoints", []) or [],
            confidence=f.get("confidence", "low"),
            notes=f.get("notes", "") or "",
        )
        for i, f in enumerate(parsed.get("synthesized_findings", []), start=1)
    ]

    cn = parsed.get("confidence_notes") or {}
    confidence_notes = ConfidenceNotes(
        coverage_gaps=cn.get("coverage_gaps", []) or [],
        evidence_quality_flags=cn.get("evidence_quality_flags", []) or [],
        reasoning_limits=cn.get("reasoning_limits", []) or [],
    )

    created_at = _utc_now_iso_z()

    pack = NormalizedEvidencePackV1(
        schema_version="normalized_evidence_pack.v1",
        job_id=req.job_id,
        tenant_id=req.tenant_id,
        conversation_id=req.conversation_id,
        pipeline_version=req.pipeline_version,
        prompt_version=req.prompt_version,
        created_at=created_at,
        evidence_sources=evidence_sources,
        synthesized_findings=findings,
        citations=citations,
        confidence_notes=confidence_notes,
        perplexity_metadata=PerplexityMetadata(
            model=cfg.perplexity_model,
            temperature=0,
            top_p=1,
            max_tokens=2048,
            request_hash=request_hash,
            provider_request_id=provider_request_id,
            latency_ms=latency_ms,
        ),
    )

    object_name = cfg.pack_object_template.format(
        tenant_id=req.tenant_id, job_id=req.job_id
    )
    pack_dict = pack.model_dump(mode="json")
    pack_gcs_path, _ = write_json_if_absent(
        cfg.evidence_bucket, object_name, pack_dict
    )

    txn_done = db.transaction()
    synth_mark_complete(
        txn_done,
        ref,
        request_hash,
        pack_gcs_path,
        pack.schema_version,
        latency_ms,
    )

    log.info(
        "Synthesis complete",
        extra={
            "tenant_id": req.tenant_id,
            "job_id": req.job_id,
            "message_id": message_id,
            "pack": pack_gcs_path,
        },
    )

    return {"ok": True, "pack": pack_gcs_path}
