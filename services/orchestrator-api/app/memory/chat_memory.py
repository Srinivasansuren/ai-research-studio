# app/memory/chat_memory.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from google.cloud import firestore
from .firestore_client import get_db

@dataclass(frozen=True)
class RehydrationConfig:
    last_n: int = 24
    max_chars: Optional[int] = 60000

class ChatMemoryStore:
    def __init__(self, tenant_id: str = "default"):
        self.tenant_id = tenant_id
        self.db = get_db()

    def _conv_ref(self, user_id: str, conversation_id: str):
        return (
            self.db.collection("tenants").document(self.tenant_id)
            .collection("users").document(user_id)
            .collection("conversations").document(conversation_id)
        )

    def _msgs_col(self, user_id: str, conversation_id: str):
        return self._conv_ref(user_id, conversation_id).collection("messages")

    def get_or_create_conversation(
        self,
        user_id: str,
        conversation_id: Optional[str],
        rehydration: RehydrationConfig = RehydrationConfig(),
    ) -> str:
        if conversation_id is None:
            # deterministic enough: Firestore auto id is fine; caller returns it to client
            conversation_id = self._conv_ref(user_id, "_").collection("_tmp").document().id

        conv_ref = self._conv_ref(user_id, conversation_id)
        snap = conv_ref.get()
        if snap.exists:
            return conversation_id

        conv_ref.set(
            {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "tenant_id": self.tenant_id,
                "created_at": firestore.SERVER_TIMESTAMP,
                "updated_at": firestore.SERVER_TIMESTAMP,
                "status": "active",
                "next_seq": 1,
                "last_message_seq": 0,
                "rehydration": {
                    "mode": "last_n",
                    "last_n": rehydration.last_n,
                    "max_chars": rehydration.max_chars,
                },
                "pinned_message_seqs": [],
                "latest_artifact_ids": [],
            }
        )
        return conversation_id

    def rehydrate(
        self,
        user_id: str,
        conversation_id: str,
    ) -> List[Dict[str, str]]:
        conv_ref = self._conv_ref(user_id, conversation_id)
        conv = conv_ref.get().to_dict() or {}
        rh = conv.get("rehydration", {}) or {}
        last_n = int(rh.get("last_n", 24))
        max_chars = rh.get("max_chars", 60000)
        pinned = set(conv.get("pinned_message_seqs", []) or [])

        # 1) pull last_n
        q = (
            self._msgs_col(user_id, conversation_id)
            .order_by("seq", direction=firestore.Query.DESCENDING)
            .limit(last_n)
        )
        recent = list(q.stream())
        recent_msgs = [d.to_dict() for d in reversed(recent)]  # seq asc

        # 2) fetch pinned (by seq) if outside recent window
        pinned_msgs: List[Dict[str, Any]] = []
        if pinned:
            # Firestore doesn't support IN on different field types well at scale; keep pinned small.
            for seq in sorted(pinned):
                doc_id = f"{seq:08d}"
                snap = self._msgs_col(user_id, conversation_id).document(doc_id).get()
                if snap.exists:
                    pinned_msgs.append(snap.to_dict())

        # 3) merge + dedupe
        merged: Dict[int, Dict[str, Any]] = {}
        for m in pinned_msgs + recent_msgs:
            merged[int(m["seq"])] = m
        ordered = [merged[k] for k in sorted(merged.keys())]

        # 4) apply deterministic char cap
        if max_chars is not None:
            budget = int(max_chars)
            kept: List[Dict[str, Any]] = []
            # Always keep pinned first (in order), then add from the end
            pinned_ordered = [m for m in ordered if int(m["seq"]) in pinned]
            tail = [m for m in ordered if int(m["seq"]) not in pinned]

            def msg_len(m: Dict[str, Any]) -> int:
                return len((m.get("content") or "")) + 32  # small deterministic overhead

            for m in pinned_ordered:
                l = msg_len(m)
                if l <= budget:
                    kept.append(m)
                    budget -= l

            # Add most recent tail messages until budget used
            for m in reversed(tail):
                l = msg_len(m)
                if l <= budget:
                    kept.append(m)
                    budget -= l

            ordered = sorted(kept, key=lambda x: int(x["seq"]))

        # return minimal structure for LLM input
        return [{"role": m["role"], "content": m.get("content", "")} for m in ordered]

    def append_message(
        self,
        user_id: str,
        conversation_id: str,
        role: str,
        content: str,
        request_id: str,
        pointers: Optional[Dict[str, Any]] = None,
    ) -> int:
        pointers = pointers or {}
        conv_ref = self._conv_ref(user_id, conversation_id)
        msgs_col = self._msgs_col(user_id, conversation_id)

        # Idempotency: if request_id already stored, return existing seq
        existing = list(msgs_col.where("request_id", "==", request_id).limit(1).stream())
        if existing:
            return int(existing[0].to_dict()["seq"])

        @firestore.transactional
        def _txn(txn: firestore.Transaction) -> int:
            conv_snap = conv_ref.get(transaction=txn)
            if not conv_snap.exists:
                raise ValueError("Conversation does not exist")

            conv = conv_snap.to_dict()
            next_seq = int(conv.get("next_seq", 1))
            doc_id = f"{next_seq:08d}"
            msg_ref = msgs_col.document(doc_id)

            txn.set(
                msg_ref,
                {
                    "seq": next_seq,
                    "role": role,
                    "content": content,
                    "content_type": "text/plain",
                    "created_at": firestore.SERVER_TIMESTAMP,
                    "request_id": request_id,
                    **pointers,
                },
            )
            txn.update(
                conv_ref,
                {
                    "next_seq": next_seq + 1,
                    "last_message_seq": next_seq,
                    "updated_at": firestore.SERVER_TIMESTAMP,
                },
            )
            return next_seq

        txn = self.db.transaction()
        return _txn(txn)

    def attach_artifacts(
        self,
        user_id: str,
        conversation_id: str,
        message_seq: int,
        artifacts: List[Dict[str, Any]],
    ) -> None:
        # Update message doc with artifact pointers (merge)
        msg_ref = self._msgs_col(user_id, conversation_id).document(f"{message_seq:08d}")
        msg_ref.set({"artifacts": artifacts}, merge=True)

        # Update conversation convenience list (bounded to last ~20)
        conv_ref = self._conv_ref(user_id, conversation_id)
        conv = conv_ref.get().to_dict() or {}
        latest = list(conv.get("latest_artifact_ids", []) or [])
        for a in artifacts:
            aid = a.get("artifact_id")
            if aid and aid not in latest:
                latest.append(aid)
        latest = latest[-20:]
        conv_ref.set({"latest_artifact_ids": latest, "updated_at": firestore.SERVER_TIMESTAMP}, merge=True)
