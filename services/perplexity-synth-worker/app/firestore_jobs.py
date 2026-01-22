import logging
from google.cloud import firestore

log = logging.getLogger("phase6.firestore_jobs")

STATE_EVIDENCE_READY = "EVIDENCE_READY"
STATE_SYNTH_IN_PROGRESS = "SYNTHESIS_IN_PROGRESS"
STATE_SYNTH_COMPLETE = "SYNTHESIS_COMPLETE"
STATE_SYNTH_FAILED = "SYNTHESIS_FAILED"

def job_doc_ref(db: firestore.Client, jobs_collection_template: str, tenant_id: str, job_id: str):
    col_path = jobs_collection_template.format(tenant_id=tenant_id)
    return db.document(f"{col_path}/{job_id}")

@firestore.transactional
def synth_mark_in_progress(
    txn: firestore.Transaction,
    ref,
    request_hash: str,
    prompt_version: str,
    model: str,
):
    snap = ref.get(transaction=txn)
    if not snap.exists:
        raise RuntimeError("job_missing")

    doc = snap.to_dict() or {}
    status = doc.get("status")
    synth = doc.get("synthesis") or {}
    existing_hash = synth.get("request_hash")

    if status == STATE_SYNTH_COMPLETE and existing_hash == request_hash:
        return {"idempotent": True, "already_complete": True}

    if status == STATE_SYNTH_IN_PROGRESS and existing_hash == request_hash:
        return {"idempotent": True, "already_in_progress": True}

    if status not in (STATE_EVIDENCE_READY, STATE_SYNTH_FAILED):
        raise RuntimeError(f"invalid_state:{status}")

    attempt = int(synth.get("attempt", 0)) + 1

    txn.update(ref, {
        "updated_at": firestore.SERVER_TIMESTAMP,
        "status": STATE_SYNTH_IN_PROGRESS,
        "synthesis": {
            "prompt_version": prompt_version,
            "request_hash": request_hash,
            "model": model,
            "attempt": attempt,
            "started_at": firestore.SERVER_TIMESTAMP,
        },
    })
    return {"idempotent": False, "attempt": attempt}

@firestore.transactional
def synth_mark_complete(
    txn: firestore.Transaction,
    ref,
    request_hash: str,
    pack_gcs_path: str,
    schema_version: str,
    latency_ms: int | None,
):
    snap = ref.get(transaction=txn)
    if not snap.exists:
        raise RuntimeError("job_missing")
    doc = snap.to_dict() or {}

    status = doc.get("status")
    synth = doc.get("synthesis") or {}
    existing_hash = synth.get("request_hash")

    if status == STATE_SYNTH_COMPLETE and existing_hash == request_hash:
        return {"idempotent": True}

    if status != STATE_SYNTH_IN_PROGRESS or existing_hash != request_hash:
        raise RuntimeError(f"invalid_state_or_hash:status={status}")

    synth_update = dict(synth)
    synth_update["completed_at"] = firestore.SERVER_TIMESTAMP
    if latency_ms is not None:
        synth_update["latency_ms"] = latency_ms

    txn.update(ref, {
        "updated_at": firestore.SERVER_TIMESTAMP,
        "status": STATE_SYNTH_COMPLETE,
        "synthesis": synth_update,
        "normalized_pack_gcs_path": pack_gcs_path,
        "normalized_pack_schema_version": schema_version,
        "normalized_pack_created_at": firestore.SERVER_TIMESTAMP,
    })
    return {"idempotent": False}

@firestore.transactional
def synth_mark_failed(
    txn: firestore.Transaction,
    ref,
    request_hash: str,
    error: dict,
):
    snap = ref.get(transaction=txn)
    if not snap.exists:
        raise RuntimeError("job_missing")
    doc = snap.to_dict() or {}

    status = doc.get("status")
    synth = doc.get("synthesis") or {}
    existing_hash = synth.get("request_hash")

    if status == STATE_SYNTH_FAILED and existing_hash == request_hash:
        return {"idempotent": True}

    # allow failing from IN_PROGRESS
    if status not in (STATE_SYNTH_IN_PROGRESS, STATE_EVIDENCE_READY):
        raise RuntimeError(f"invalid_state:{status}")

    synth_update = dict(synth)
    synth_update["request_hash"] = request_hash
    synth_update["failed_at"] = firestore.SERVER_TIMESTAMP
    synth_update["error"] = error

    txn.update(ref, {
        "updated_at": firestore.SERVER_TIMESTAMP,
        "status": STATE_SYNTH_FAILED,
        "synthesis": synth_update,
    })
    return {"idempotent": False}
