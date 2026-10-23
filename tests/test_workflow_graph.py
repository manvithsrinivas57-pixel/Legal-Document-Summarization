"""Unit tests for LangGraph workflow execution, state transitions, and audit trail."""

from workflow.graph import build_legal_workflow_graph
from workflow.state import LegalWorkflowState


def test_workflow_execution_with_missing_checkpoint(sample_judgment_text: str):
    """Test full LangGraph execution when fine-tuned checkpoint is missing.

    Strictly verifies that workflow stops gracefully at summarization node,
    records audit trail, and explains missing checkpoint without crashing.
    """
    app = build_legal_workflow_graph()

    initial_state: LegalWorkflowState = {
        "raw_text": sample_judgment_text,
        "source_filename": "sample_judgment.txt",
        "pdf_bytes": None,
        "metadata": {},
        "gemini_api_key": None,  # Test in local dry-run mode
        "gemini_model_name": "gemini-2.5-flash",
        "model_mode": "fine_tuned",
        "checkpoint_path": "models/checkpoints/non_existent_test_checkpoint",
        "checkpoint_available": False,
        "analysis": None,
        "reasoning": None,
        "summary": None,
        "summary_model_id": None,
        "summary_latency": 0.0,
        "validation": None,
        "audit_trail": [],
        "errors": [],
        "current_step": "init",
        "overall_status": "READY",
        "explanation": None,
    }

    final_state = app.invoke(initial_state)

    # Verify overall state
    assert final_state["overall_status"] == "CHECKPOINT_MISSING"
    assert final_state["summary"] is None
    assert final_state["explanation"] is not None
    assert "RESEARCH INTEGRITY NOTICE" in final_state["explanation"]

    # Verify audit trail
    audit_trail = final_state["audit_trail"]
    assert len(audit_trail) >= 4  # extraction, analysis, reasoning, summarization, validation skipped

    stages = [evt["stage_name"] for evt in audit_trail]
    assert any("PDF & Text Ingestion" in s for s in stages)
    assert any("Document Structure Analysis" in s for s in stages)
    assert any("Legal Reasoning" in s for s in stages)
    assert any("Abstractive Summarization" in s for s in stages)

    # Check summarization audit status
    sum_evt = next(e for e in audit_trail if "Abstractive Summarization" in e["stage_name"])
    assert sum_evt["status"] == "CHECKPOINT_MISSING"


def test_workflow_execution_with_pdf_bytes(sample_pdf_bytes: bytes):
    """Test LangGraph extraction stage with real PDF bytes."""
    app = build_legal_workflow_graph()

    initial_state: LegalWorkflowState = {
        "raw_text": "",
        "source_filename": "sample_appeal.pdf",
        "pdf_bytes": sample_pdf_bytes,
        "metadata": {},
        "gemini_api_key": None,
        "gemini_model_name": "gemini-2.5-flash",
        "model_mode": "fine_tuned",
        "checkpoint_path": "models/checkpoints/non_existent",
        "checkpoint_available": False,
        "analysis": None,
        "reasoning": None,
        "summary": None,
        "summary_model_id": None,
        "summary_latency": 0.0,
        "validation": None,
        "audit_trail": [],
        "errors": [],
        "current_step": "init",
        "overall_status": "READY",
        "explanation": None,
    }

    final_state = app.invoke(initial_state)

    assert len(final_state["raw_text"]) > 200
    assert final_state["metadata"]["num_pages"] == 1
    assert "SUPREME COURT" in final_state["raw_text"]


def test_workflow_handles_empty_input_gracefully():
    """Test that empty input is routed through error handler node."""
    app = build_legal_workflow_graph()

    initial_state: LegalWorkflowState = {
        "raw_text": "   ",
        "source_filename": "empty.txt",
        "pdf_bytes": None,
        "metadata": {},
        "gemini_api_key": None,
        "gemini_model_name": "gemini-2.5-flash",
        "model_mode": "fine_tuned",
        "checkpoint_path": "models/checkpoints/non_existent",
        "checkpoint_available": False,
        "analysis": None,
        "reasoning": None,
        "summary": None,
        "summary_model_id": None,
        "summary_latency": 0.0,
        "validation": None,
        "audit_trail": [],
        "errors": [],
        "current_step": "init",
        "overall_status": "READY",
        "explanation": None,
    }

    final_state = app.invoke(initial_state)

    assert final_state["overall_status"] == "FAILED"
    assert len(final_state["errors"]) > 0
    assert any("empty" in err.lower() for err in final_state["errors"])
