from __future__ import annotations

from google.cloud import firestore


def dedupe_ref(db: firestore.Client, tenant_id: str, job_id: str, idempotency_key: str):
    return (
        db.collection("tenants").document(tenant_id)
        .collection("jobs").document(job_id)
        .collection("dedupe").document(idempotency_key)
    )


def claim_idempotency(db: firestore.Client, tenant_id: str, job_id: str, idempotency_key: str) -> bool:
    """
    Transactionally create a dedupe marker.
    Returns True if claimed (first time), False if already processed.
    """
    ref = dedupe_ref(db, tenant_id, job_id, idempotency_key)

    @firestore.transactional
    def _tx(transaction: firestore.Transaction) -> bool:
        snap = ref.get(transaction=transaction)
        if snap.exists:
            return False
        transaction.set(ref, {"created_at": firestore.SERVER_TIMESTAMP})
        return True

    txn = db.transaction()
    return _tx(txn)
