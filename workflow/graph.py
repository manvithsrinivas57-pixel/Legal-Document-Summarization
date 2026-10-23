"""LangGraph workflow definition for Legal Document Summarization."""

import datetime
from typing import Literal
from langgraph.graph import StateGraph, START, END

from workflow.state import LegalWorkflowState
from agents.pdf_extractor import PDFExtractorAgent, PDFExtractionError
from agents.document_analyzer import DocumentAnalyzerAgent
from agents.legal_reasoner import LegalReasonerAgent
from agents.bart_summarizer import BARTSummarizerAgent
from agents.validator import ValidationAgent
import config


import hashlib


def _record_audit_step(
    state: LegalWorkflowState,
    stage_name: str,
    model_id: str,
    status: str,
    latency: float = 0.0,
    details: dict | None = None,
) -> list[dict]:
    """Helper to append an audit trail record to state."""
    trail = list(state.get("audit_trail", []))
    event = {
        "event_id": f"evt-{len(trail)+1}",
        "timestamp_iso": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "document_id": state.get("document_id") or "doc-init",
        "source_filename": state.get("source_filename", "document.pdf"),
        "stage_name": stage_name,
        "model_identifier": model_id,
        "status": status,
        "latency_seconds": latency,
        "details": details or {},
    }
    trail.append(event)
    return trail


# -------------------------------- Node Functions --------------------------------


def extract_node(state: LegalWorkflowState) -> dict:
    """Node 1: Extract and clean raw legal text from uploaded PDF or raw input."""
    extractor = PDFExtractorAgent()

    # Determine unique document identifier
    if state.get("pdf_bytes"):
        doc_id = f"pdf-{hashlib.sha256(state['pdf_bytes']).hexdigest()[:12]}"
    else:
        doc_id = f"txt-{hashlib.sha256(state.get('raw_text', '').encode('utf-8')).hexdigest()[:12]}"

    temp_state = dict(state)
    temp_state["document_id"] = doc_id

    try:
        if state.get("pdf_bytes"):
            res = extractor.extract_from_bytes(
                state["pdf_bytes"], filename=state.get("source_filename", "document.pdf")
            )
        else:
            res = extractor.extract_from_text(
                state.get("raw_text", ""), source_name=state.get("source_filename", "manual_input.txt")
            )

        meta = res["metadata"]
        audit = _record_audit_step(
            temp_state,
            stage_name="1. PDF & Text Ingestion",
            model_id="PyPDF v6.x (Rule-based Normalizer)",
            status="SUCCESS",
            latency=round(meta.get("extraction_time_ms", 0) / 1000.0, 3),
            details={
                "num_pages": meta.get("num_pages"),
                "word_count": meta.get("word_count"),
                "char_count": meta.get("char_count"),
                "is_scanned": meta.get("is_scanned", False),
            },
        )
        return {
            "document_id": doc_id,
            "raw_text": res["text"],
            "metadata": meta,
            "audit_trail": audit,
            "current_step": "extract_node",
            "overall_status": "RUNNING",
        }
    except PDFExtractionError as exc:
        audit = _record_audit_step(
            temp_state,
            stage_name="1. PDF & Text Ingestion",
            model_id="PyPDF v6.x",
            status="FAILED",
            details={"error": str(exc)},
        )
        return {
            "document_id": doc_id,
            "errors": list(state.get("errors", [])) + [str(exc)],
            "audit_trail": audit,
            "overall_status": "FAILED",
            "explanation": f"Text extraction failed: {str(exc)}",
            "current_step": "extract_node",
        }


def document_analysis_node(state: LegalWorkflowState) -> dict:
    """Node 2: Zero-shot structural extraction using Gemini."""
    model_name = state.get("gemini_model_name", config.DEFAULT_GEMINI_MODEL)
    analyzer = DocumentAnalyzerAgent(
        api_key=state.get("gemini_api_key"),
        model_name=model_name,
    )
    res = analyzer.analyze(state["raw_text"])

    status = res["status"]
    err = res.get("error")
    audit = _record_audit_step(
        state,
        stage_name="2. Document Structure Analysis",
        model_id=res["model_identifier"],
        status=status,
        latency=res["latency_seconds"],
        details={
            "case_title": res["data"].get("case_title"),
            "court": res["data"].get("court_name"),
            "error": err,
        },
    )
    errors = list(state.get("errors", []))
    if err and status != "SUCCESS":
        errors.append(f"Document Analysis ({res['model_identifier']}): {err}")

    # Track working model and service health to coordinate with subsequent nodes
    active_model = res["model_identifier"] if status == "SUCCESS" else model_name
    is_503_unavail = bool(err and status != "SUCCESS" and ("503" in err or "UNAVAILABLE" in err))

    return {
        "analysis": res["data"],
        "analysis_error": err if status != "SUCCESS" else None,
        "errors": errors,
        "audit_trail": audit,
        "current_step": "document_analysis_node",
        "gemini_model_name": active_model,
        "gemini_service_unavailable": is_503_unavail,
    }


def legal_reasoning_node(state: LegalWorkflowState) -> dict:
    """Node 3: Zero-shot legal doctrine & ratio decidendi reasoning using Gemini."""
    model_name = state.get("gemini_model_name", config.DEFAULT_GEMINI_MODEL)
    service_unavail = bool(state.get("gemini_service_unavailable", False))

    # Avoid duplicate retry storm: if Document Analysis already encountered persistent 503,
    # tell LegalReasoner to avoid repeating the full 3-retry backoff storm
    reasoner = LegalReasonerAgent(
        api_key=state.get("gemini_api_key"),
        model_name=model_name,
        avoid_retry_storm=service_unavail,
    )
    res = reasoner.reason(
        state["raw_text"],
        prior_analysis=state.get("analysis"),
        avoid_retry_storm=service_unavail,
    )

    status = res["status"]
    err = res.get("error")
    audit = _record_audit_step(
        state,
        stage_name="3. Legal Reasoning & Doctrine",
        model_id=res["model_identifier"],
        status=status,
        latency=res["latency_seconds"],
        details={
            "disposition": res["data"].get("court_holding_and_disposition"),
            "questions_count": len(res["data"].get("questions_of_law", [])),
            "error": err,
        },
    )
    errors = list(state.get("errors", []))
    if err and status != "SUCCESS":
        errors.append(f"Legal Reasoning ({res['model_identifier']}): {err}")

    active_model = res["model_identifier"] if status == "SUCCESS" else model_name

    return {
        "reasoning": res["data"],
        "reasoning_error": err if status != "SUCCESS" else None,
        "errors": errors,
        "audit_trail": audit,
        "current_step": "legal_reasoning_node",
        "gemini_model_name": active_model,
    }


def summarization_node(state: LegalWorkflowState) -> dict:
    """Node 4: Neural abstractive summarization using fine-tuned BART checkpoint.

    Strictly halts if checkpoint is missing; never fakes or silently substitutes Gemini.
    """
    mode = state.get("model_mode", "fine_tuned")
    checkpoint_path = state.get("checkpoint_path", str(config.DEFAULT_CHECKPOINT_PATH))

    summarizer = BARTSummarizerAgent(checkpoint_path=checkpoint_path, mode=mode)
    res = summarizer.summarize(state["raw_text"])

    status = res["status"]
    resolved_chk = str(summarizer.checkpoint_path)
    audit = _record_audit_step(
        state,
        stage_name="4. Abstractive Summarization",
        model_id=res["model_identifier"],
        status=status,
        latency=res["latency_seconds"],
        details={
            "mode": mode,
            "checkpoint_path": resolved_chk,
            "is_fine_tuned": res.get("is_fine_tuned", False),
            "summary_words": res.get("summary_word_count", 0),
        },
    )

    if status == "CHECKPOINT_MISSING":
        return {
            "summary": None,
            "summary_model_id": res["model_identifier"],
            "summary_latency": res["latency_seconds"],
            "audit_trail": audit,
            "overall_status": "CHECKPOINT_MISSING",
            "explanation": res["explanation"],
            "current_step": "summarization_node",
        }
    elif status == "DEPENDENCIES_MISSING":
        return {
            "summary": None,
            "summary_model_id": res["model_identifier"],
            "summary_latency": res["latency_seconds"],
            "audit_trail": audit,
            "overall_status": "FAILED",
            "explanation": res["explanation"],
            "current_step": "summarization_node",
        }
    elif status == "SUCCESS":
        return {
            "summary": res["summary"],
            "summary_model_id": res["model_identifier"],
            "summary_latency": res["latency_seconds"],
            "audit_trail": audit,
            "current_step": "summarization_node",
        }
    else:
        return {
            "summary": None,
            "summary_model_id": res["model_identifier"],
            "summary_latency": res["latency_seconds"],
            "audit_trail": audit,
            "overall_status": "FAILED",
            "errors": list(state.get("errors", [])) + [res.get("error", "Unknown error")],
            "explanation": res.get("explanation"),
            "current_step": "summarization_node",
        }


def validation_node(state: LegalWorkflowState) -> dict:
    """Node 5: Quality, coverage, consistency, and hallucination validation."""
    summary_text = state.get("summary")

    if not summary_text:
        # If no summary was produced (e.g. checkpoint missing), log audit and record skipped
        audit = _record_audit_step(
            state,
            stage_name="5. Summary Quality & Grounding Validation",
            model_id="Rule & Entity Grounding Validator",
            status="SKIPPED",
            details={"reason": "No summary produced by upstream summarizer (Checkpoints or Dependencies missing)."},
        )
        return {
            "validation": None,
            "audit_trail": audit,
            "current_step": "validation_node",
        }

    validator = ValidationAgent(
        api_key=state.get("gemini_api_key"),
        model_name=state.get("gemini_model_name", config.DEFAULT_GEMINI_MODEL),
    )

    res = validator.validate(
        source_text=state["raw_text"],
        summary=summary_text,
        prior_analysis=state.get("analysis"),
        prior_reasoning=state.get("reasoning"),
    )

    val_data = res["data"]
    audit = _record_audit_step(
        state,
        stage_name="5. Summary Quality & Grounding Validation",
        model_id="Rule & Entity Grounding Validator",
        status=res["status"],
        latency=res["latency_seconds"],
        details={
            "overall_status": val_data.get("overall_status"),
            "coverage_score": val_data.get("coverage_score"),
            "consistency_score": val_data.get("consistency_score"),
            "unsupported_claims_count": val_data.get("unsupported_claims_count"),
        },
    )

    overall_status = "COMPLETED"
    if state.get("analysis_error") or state.get("reasoning_error"):
        overall_status = "PARTIAL_SUCCESS"

    return {
        "validation": val_data,
        "audit_trail": audit,
        "overall_status": overall_status,
        "current_step": "validation_node",
    }


def error_handler_node(state: LegalWorkflowState) -> dict:
    """Terminal node handling catastrophic errors."""
    audit = _record_audit_step(
        state,
        stage_name="Workflow Error Handler",
        model_id="System",
        status="HALTED",
        details={"errors": state.get("errors", [])},
    )
    return {
        "audit_trail": audit,
        "overall_status": "FAILED",
        "current_step": "error_handler_node",
    }


# -------------------------------- Routing & Edges --------------------------------


def check_extraction_success(state: LegalWorkflowState) -> Literal["document_analysis", "error_handler"]:
    if state.get("errors"):
        return "error_handler"
    return "document_analysis"


def build_legal_workflow_graph() -> StateGraph:
    """Construct and compile the full LangGraph legal summarization workflow."""
    builder = StateGraph(LegalWorkflowState)

    # Register nodes
    builder.add_node("extract_text", extract_node)
    builder.add_node("document_analysis", document_analysis_node)
    builder.add_node("legal_reasoning", legal_reasoning_node)
    builder.add_node("summarize_bart", summarization_node)
    builder.add_node("validate_summary", validation_node)
    builder.add_node("error_handler", error_handler_node)

    # Register edges
    builder.add_edge(START, "extract_text")
    builder.add_conditional_edges(
        "extract_text",
        check_extraction_success,
        {
            "document_analysis": "document_analysis",
            "error_handler": "error_handler",
        },
    )
    builder.add_edge("document_analysis", "legal_reasoning")
    builder.add_edge("legal_reasoning", "summarize_bart")
    builder.add_edge("summarize_bart", "validate_summary")
    builder.add_edge("validate_summary", END)
    builder.add_edge("error_handler", END)

    return builder.compile()
