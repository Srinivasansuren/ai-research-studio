# app/pipeline/runner.py

async def run_pipeline(*, history, user_message):
    """
    Phase 4:
    - This function wires the locked pipeline.
    - Memory is already rehydrated before this call.
    - This function must be PURE: no Firestore access.
    """

    # TODO (Phase 4+):
    # SerpAPI
    # Fetcher
    # Perplexity (search only)
    # Evidence normalization
    # Debate LLMs (web-blind)
    # Referee
    # Artifact generation

    # Temporary placeholder until full pipeline is wired
    return {
        "assistant_text": f"(Phase 4 placeholder) Received: {user_message}",
        "evidence_pack": {},
        "llm": {},
        "artifacts": [],
    }
