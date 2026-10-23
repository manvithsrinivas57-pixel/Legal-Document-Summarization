"""State definitions for the LangGraph legal summarization workflow."""

from typing import Any, TypedDict


class LegalWorkflowState(TypedDict):
    """Explicit state representation carried across all LangGraph workflow nodes."""

    # Ingestion & Raw Content
    raw_text: str
    source_filename: str
    document_id: str | None
    pdf_bytes: bytes | None
    metadata: dict[str, Any]

    # Model Configuration & Parameters
    gemini_api_key: str | None
    gemini_model_name: str
    gemini_service_unavailable: bool | None
    model_mode: str  # "fine_tuned" or "pretrained_base"
    checkpoint_path: str
    checkpoint_available: bool

    # Zero-Shot Analytical Stages
    analysis: dict[str, Any] | None
    analysis_error: str | None
    reasoning: dict[str, Any] | None
    reasoning_error: str | None

    # Final Neural Summarization
    summary: str | None
    summary_model_id: str | None
    summary_latency: float

    # Quality & Faithfulness Validation
    validation: dict[str, Any] | None

    # Operational & Provenance Metadata
    audit_trail: list[dict[str, Any]]
    errors: list[str]
    current_step: str
    overall_status: str  # "READY", "RUNNING", "COMPLETED", "PARTIAL_SUCCESS", "CHECKPOINT_MISSING", "FAILED"
    explanation: str | None
