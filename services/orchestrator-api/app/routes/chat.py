# app/routes/chat.py

from fastapi import APIRouter, Request
import uuid

from app.memory.chat_memory import ChatMemoryStore


router = APIRouter()

# Firestore-backed chat memory (singleton per process)
memory = ChatMemoryStore(tenant_id="default")


@router.post("/chat")
async def chat(req: Request, payload: dict):
    """
    Chat endpoint with deterministic Firestore-backed memory.
    """

    # 1. Identify user (already handled elsewhere in your stack)
    user_id = getattr(req.state, "user_id", "anonymous")


    # 2. Conversation + request identity
    conversation_id = payload.get("conversation_id")
    request_id = payload.get("request_id") or f"req-{uuid.uuid4()}"

    # 3. Get or create conversation
    conversation_id = memory.get_or_create_conversation(
        user_id=user_id,
        conversation_id=conversation_id,
    )

    # 4. Rehydrate chat history (deterministic)
    history = memory.rehydrate(
        user_id=user_id,
        conversation_id=conversation_id,
    )

    # 5. Persist user message
    user_text = payload["message"]
    user_seq = memory.append_message(
        user_id=user_id,
        conversation_id=conversation_id,
        role="user",
        content=user_text,
        request_id=f"{request_id}:user",
    )

    # 6. Run LOCKED pipeline (unchanged)
    # Phase 3 stub — pipeline wired in Phase 4
    result = {
        "assistant_text": f"(Phase 3 stub) I received: {user_text}",
        "evidence_pack": {},
        "llm": {},
        "artifacts": []
    }

    # 7. Persist assistant message
    assistant_seq = memory.append_message(
        user_id=user_id,
        conversation_id=conversation_id,
        role="assistant",
        content=result["assistant_text"],
        request_id=f"{request_id}:assistant",
        pointers={
            "pipeline": {
                "evidence_pack": result.get("evidence_pack", {})
            },
            "llm": result.get("llm", {}),
        },
    )

    # 8. Attach artifact pointers (if any)
    if result.get("artifacts"):
        memory.attach_artifacts(
            user_id=user_id,
            conversation_id=conversation_id,
            message_seq=assistant_seq,
            artifacts=result["artifacts"],
        )

    # 9. Return response
    return {
        "conversation_id": conversation_id,
        "user_message_seq": user_seq,
        "assistant_message_seq": assistant_seq,
        "assistant": result["assistant_text"],
        "artifacts": result.get("artifacts", []),
    }
