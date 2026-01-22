from pydantic import BaseModel, Field, HttpUrl
from typing import List, Literal, Optional
from datetime import datetime

class EvidenceItem(BaseModel):
    source_url: HttpUrl
    snapshot_gcs_path: str
    fetched_at: str
    checksum: str
    cleaned_text: str

class PerplexitySynthesisRequestV1(BaseModel):
    schema_version: Literal["perplexity_synth_request.v1"]
    tenant_id: str
    job_id: str
    conversation_id: str
    pipeline_version: str
    prompt_version: str
    evidence: List[EvidenceItem]

class SynthFinding(BaseModel):
    finding_id: str
    finding: str
    supporting_evidence_ids: List[str]
    counterpoints: List[str] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"]
    notes: str = ""

class Citation(BaseModel):
    evidence_id: str
    source_url: str
    checksum: str
    fetched_at: str

class ConfidenceNotes(BaseModel):
    coverage_gaps: List[str] = Field(default_factory=list)
    evidence_quality_flags: List[str] = Field(default_factory=list)
    reasoning_limits: List[str] = Field(default_factory=list)

class PerplexityMetadata(BaseModel):
    model: str
    temperature: float
    top_p: float
    max_tokens: int
    request_hash: str
    provider_request_id: Optional[str] = None
    latency_ms: Optional[int] = None

class NormalizedEvidencePackV1(BaseModel):
    schema_version: Literal["normalized_evidence_pack.v1"]

    job_id: str
    tenant_id: str
    conversation_id: str
    pipeline_version: str
    prompt_version: str
    created_at: str

    evidence_sources: List[dict]
    synthesized_findings: List[SynthFinding]
    citations: List[Citation]
    confidence_notes: ConfidenceNotes
    perplexity_metadata: PerplexityMetadata
