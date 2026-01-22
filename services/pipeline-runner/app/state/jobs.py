from __future__ import annotations

import hashlib
from google.cloud import firestore


def job_ref(db: firestore.Client, tenant_id: str, job_id: str):
    return db.collection("tenants").document(tenant_id).collection("jobs").document(job_id)


def stable_hash(obj: dict) -> str:
    # deterministic hash for pipeline spec
    raw = repr(sorted(obj.items())).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@firestore.transactional
def ensure_job_initialized(
    transaction: firestore.Transaction,
    db: firestore.Client,
    tenant_id: str,
    job_id: str,
    conversation_id: str,
    user_prompt: str,
    pipeline_version: str,
    serpapi_spec: dict,
) -> dict:
    ref = job_ref(db, tenant_id, job_id)
    snap = ref.get(transaction=transaction)

    spec_hash = stable_hash({
        "pipeline_version": pipeline_version,
        "serpapi": serpapi_spec,
    })

    if snap.exists:
        data = snap.to_dict() or {}
        # If already initialized with same spec, keep it.
        return data

    doc = {
        "v": 1,
        "tenant_id": tenant_id,
        "job_id": job_id,
        "conversation_id": conversation_id,
        "created_at": firestore.SERVER_TIMESTAMP,
        "updated_at": firestore.SERVER_TIMESTAMP,
        "status": "RUNNING",
        "pipeline_version": pipeline_version,
        "pipeline_spec_hash": spec_hash,
        "input": {
            "user_prompt": user_prompt,
            "serpapi": serpapi_spec,
        },
        "urls": {"expected": 0, "discovered": 0, "list": []},
        "evidence": {"expected": 0, "received": 0, "items": {}},
        "artifacts": {"final_manifest_object": None, "art_ids": []},
        "error": {"code": None, "message": None, "step": None, "last_failure_at": None},
    }
    transaction.set(ref, doc)
    return doc


@firestore.transactional
def set_urls_and_mark_fetch_requested(
    transaction: firestore.Transaction,
    db: firestore.Client,
    tenant_id: str,
    job_id: str,
    urls: list[str],
):
    ref = job_ref(db, tenant_id, job_id)
    snap = ref.get(transaction=transaction)
    if not snap.exists:
        raise RuntimeError("Job not initialized")

    data = snap.to_dict() or {}
    existing = (data.get("urls") or {}).get("list") or []
    if existing:
        # already set; do not overwrite (idempotent)
        return data

    url_items = []
    evidence_items = {}
    for idx, u in enumerate(urls, start=1):
        url_id = f"URL_{idx:03d}"
        ev_id = f"EVD_{idx:03d}"
        url_items.append({"url": u, "rank": idx, "source": "serpapi", "url_id": url_id})
        evidence_items[url_id] = {
            "evidence_id": ev_id,
            "url": u,
            "raw_object": None,
            "clean_object": None,
            "status": "REQUESTED",
        }

    transaction.update(ref, {
        "updated_at": firestore.SERVER_TIMESTAMP,
        "status": "WAITING_EVIDENCE",
        "urls": {"expected": len(urls), "discovered": len(urls), "list": url_items},
        "evidence": {"expected": len(urls), "received": 0, "items": evidence_items},
    })
    return data


@firestore.transactional
def mark_evidence_written(
    transaction: firestore.Transaction,
    db: firestore.Client,
    tenant_id: str,
    job_id: str,
    url_id: str,
    raw_object: str,
):
    ref = job_ref(db, tenant_id, job_id)
    snap = ref.get(transaction=transaction)
    if not snap.exists:
        return {"job_exists": False}

    data = snap.to_dict() or {}
    evidence = data.get("evidence") or {}
    items = evidence.get("items") or {}
    item = items.get(url_id)

    if not item:
        # Unknown URL id; ignore safely
        return {"job_exists": True, "updated": False, "ready": False}

    if item.get("status") == "WRITTEN":
        return {"job_exists": True, "updated": False, "ready": False}

    # update nested field paths
    transaction.update(ref, {
        "updated_at": firestore.SERVER_TIMESTAMP,
        f"evidence.items.{url_id}.raw_object": raw_object,
        f"evidence.items.{url_id}.status": "WRITTEN",
        "evidence.received": firestore.Increment(1),
    })

    # We can’t reliably read the incremented value inside the same transaction without re-read.
    # Runner will re-read after commit if it needs to decide completion.
    return {"job_exists": True, "updated": True}


def is_job_evidence_complete(job_doc: dict) -> bool:
    evidence = job_doc.get("evidence") or {}
    return (evidence.get("received") or 0) >= (evidence.get("expected") or 0)
