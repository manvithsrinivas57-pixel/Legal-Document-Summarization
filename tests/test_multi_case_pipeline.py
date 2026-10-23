"""Tests verifying multi-case support, scanned PDF handling, and state isolation."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import config
from agents.pdf_extractor import PDFExtractorAgent, PDFExtractionError
from agents.validator import ValidationAgent
from agents.bart_summarizer import BARTSummarizerAgent
from workflow.graph import build_legal_workflow_graph
from workflow.state import LegalWorkflowState

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample_data"


def test_scanned_pdf_raises_clear_ocr_error():
    """Verify scanned/image-only PDFs (0 characters) raise clear OCR requirement error."""
    scanned_path = SAMPLE_DIR / "sample_scanned_image_only.pdf"
    assert scanned_path.exists()

    extractor = PDFExtractorAgent()
    with pytest.raises(PDFExtractionError) as exc_info:
        extractor.extract_from_file(scanned_path)

    error_msg = str(exc_info.value).lower()
    assert "ocr" in error_msg
    assert "scanned" in error_msg


def test_multi_case_pdf_extraction_distinct_judgments():
    """Verify distinct Indian court judgments extract accurate, distinct texts and metadata."""
    extractor = PDFExtractorAgent()

    # Case 1: Supreme Court Commercial/Writ Appeal
    c1 = extractor.extract_from_file(SAMPLE_DIR / "sample_civil_appeal.pdf")
    assert c1["status"] == "SUCCESS"
    assert "BHARAT INFRASTRUCTURE" in c1["text"]
    assert "Article 226" in c1["text"]
    assert c1["metadata"]["num_pages"] == 1

    # Case 2: High Court Service Writ Petition
    c2 = extractor.extract_from_file(SAMPLE_DIR / "sample_service_writ.pdf")
    assert c2["status"] == "SUCCESS"
    assert "INDERJIT SINGH WASU" in c2["text"]
    assert "Punjab Civil Services Rules" in c2["text"]

    # Case 3: Supreme Court Criminal Appeal
    c3 = extractor.extract_from_file(SAMPLE_DIR / "sample_criminal_appeal.pdf")
    assert c3["status"] == "SUCCESS"
    assert "SATPAL SINGH" in c3["text"]
    assert "Prevention of Corruption Act" in c3["text"]

    # Ensure no textual overlap in key titles
    assert "WASU" not in c1["text"]
    assert "BHARAT INFRASTRUCTURE" not in c2["text"]
    assert "SATPAL" not in c1["text"]


def test_dynamic_bart_generation_adapts_to_short_and_long_inputs():
    """Verify BART summarizer dynamically bounds tokens to prevent repetitive loops on brief orders."""
    chk_path = config.get_active_checkpoint_path()
    summarizer = BARTSummarizerAgent(checkpoint_path=chk_path, mode="fine_tuned")

    # Short order text (80 words)
    short_order = (
        "IN THE HIGH COURT OF DELHI AT NEW DELHI. "
        "CRIMINAL MISCELLANEOUS CASE NO. 102 OF 2023. "
        "STATE VERSUS RAMESH KUMAR. "
        "ORDER: Learned APP for the State submits that investigation is complete and chargesheet has been filed. "
        "In view of the statement, the petition seeking quashing of FIR is dismissed as withdrawn with liberty to approach trial court. "
        "Pending applications stand disposed of."
    )
    words = short_order.split()
    input_word_count = len(words)
    dynamic_min = min(config.BART_MIN_SUMMARY_TOKENS, max(35, int(input_word_count * 0.35)))
    dynamic_max = min(
        config.BART_MAX_SUMMARY_TOKENS,
        max(dynamic_min + 50, min(config.BART_MAX_SUMMARY_TOKENS, int(input_word_count * 0.85)))
    )

    assert dynamic_min <= 40
    assert dynamic_max < config.BART_MAX_SUMMARY_TOKENS

    # Long judgment (2,000 words)
    long_words = ["judgment"] * 2000
    long_input_count = len(long_words)
    long_min = min(config.BART_MIN_SUMMARY_TOKENS, max(35, int(long_input_count * 0.35)))
    long_max = min(
        config.BART_MAX_SUMMARY_TOKENS,
        max(long_min + 50, min(config.BART_MAX_SUMMARY_TOKENS, int(long_input_count * 0.85)))
    )
    assert long_min == config.BART_MIN_SUMMARY_TOKENS
    assert long_max == config.BART_MAX_SUMMARY_TOKENS


def test_validator_citation_alias_resolution():
    """Verify validator resolves legal citation aliases without flagging false positives."""
    validator = ValidationAgent()

    # Source has "Article 226", summary has "Art. 226"
    source = "The petitioner approached High Court invoking extraordinary jurisdiction under Article 226 of Constitution."
    summary = "The High Court exercised jurisdiction under Art. 226 and granted relief."
    unsupported = validator.check_unsupported_claims(source, summary)
    sec_unsupported = [u for u in unsupported if u["type"] == "Statute / Provision"]
    assert len(sec_unsupported) == 0

    # Source has "Section 68", summary has "Sec. 68"
    source2 = "The requirements of Section 68 of the Evidence Act were evaluated."
    summary2 = "Court held that Sec. 68 requires examining at least one attesting witness."
    unsupported2 = validator.check_unsupported_claims(source2, summary2)
    sec_unsupported2 = [u for u in unsupported2 if u["type"] == "Statute / Provision"]
    assert len(sec_unsupported2) == 0


def test_validator_detects_unsupported_precedent():
    """Verify validator flags named precedent citations not grounded in source text."""
    validator = ValidationAgent()
    source = "The High Court dismissed the writ petition concerning recovery from pension under Service Rules."
    # Summary introduces an ungrounded case citation
    summary = "Relying on ABL International Ltd. v. Export Credit Guarantee Corp., the court held state action arbitrary."
    unsupported = validator.check_unsupported_claims(source, summary)

    prec_claims = [u for u in unsupported if u["type"] == "Precedent / Citation"]
    assert len(prec_claims) >= 1
    assert "ABL International" in prec_claims[0]["value"]


def test_multi_case_state_isolation_no_leakage():
    """Verify that sequentially running Case A and Case B does not leak data between cases."""
    app = build_legal_workflow_graph()

    with open(SAMPLE_DIR / "sample_service_writ.pdf", "rb") as f:
        bytes_a = f.read()

    with open(SAMPLE_DIR / "sample_criminal_appeal.pdf", "rb") as f:
        bytes_b = f.read()

    mock_client = MagicMock()
    mock_resp_a = MagicMock()
    mock_resp_a.text = json.dumps({
        "case_title": "Dr. Inderjit Singh Wasu v. Managing Committee",
        "court_name": "Punjab and Haryana High Court",
        "case_number": "CWP 15057 of 2004",
        "decision_date": "13/11/2004",
        "petitioner": "Dr. Inderjit Singh Wasu",
        "respondent": "Managing Committee",
        "procedural_history": "Writ petition filed challenging retiral gratuity recovery.",
        "factual_background": "Petitioner retired as Principal and recovery was ordered 10 months later.",
        "legal_claims": ["Recovery violates Punjab Civil Services Rules"],
        "statutes_and_sections": ["Punjab Civil Services Rules Rule 2.2(b)", "Article 14"],
        "document_type": "Civil Writ Petition"
    })
    mock_resp_b = MagicMock()
    mock_resp_b.text = json.dumps({
        "case_title": "State of Punjab v. Satpal Singh",
        "court_name": "Supreme Court of India",
        "case_number": "Criminal Appeal 882 of 2018",
        "decision_date": "15/04/2018",
        "petitioner": "State of Punjab",
        "respondent": "Satpal Singh",
        "procedural_history": "Criminal appeal by special leave against acquittal.",
        "factual_background": "Cashier acquitted of criminal breach of trust under PC Act.",
        "legal_claims": ["Misappropriation of government revenue"],
        "statutes_and_sections": ["IPC Section 409", "Prevention of Corruption Act Section 13"],
        "document_type": "Criminal Appeal"
    })

    with patch("google.genai.Client", return_value=mock_client):
        # Run Case A
        mock_client.models.generate_content.return_value = mock_resp_a
        state_a: LegalWorkflowState = {
            "raw_text": "",
            "source_filename": "sample_service_writ.pdf",
            "document_id": "doc-a",
            "pdf_bytes": bytes_a,
            "metadata": {},
            "gemini_api_key": "mock_key",
            "gemini_model_name": config.DEFAULT_GEMINI_MODEL,
            "model_mode": "fine_tuned",
            "checkpoint_path": str(config.get_active_checkpoint_path()),
            "checkpoint_available": True,
            "analysis": None,
            "analysis_error": None,
            "reasoning": None,
            "reasoning_error": None,
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
        res_a = app.invoke(state_a)

        # Run Case B
        mock_client.models.generate_content.return_value = mock_resp_b
        state_b: LegalWorkflowState = {
            "raw_text": "",
            "source_filename": "sample_criminal_appeal.pdf",
            "document_id": "doc-b",
            "pdf_bytes": bytes_b,
            "metadata": {},
            "gemini_api_key": "mock_key",
            "gemini_model_name": config.DEFAULT_GEMINI_MODEL,
            "model_mode": "fine_tuned",
            "checkpoint_path": str(config.get_active_checkpoint_path()),
            "checkpoint_available": True,
            "analysis": None,
            "analysis_error": None,
            "reasoning": None,
            "reasoning_error": None,
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
        res_b = app.invoke(state_b)

        # Strict Multi-Case Isolation Assertions:
        assert res_a["source_filename"] == "sample_service_writ.pdf"
        assert res_b["source_filename"] == "sample_criminal_appeal.pdf"
        assert res_a["document_id"] != res_b["document_id"]

        assert "Wasu" in res_a["analysis"]["case_title"]
        assert "Satpal" in res_b["analysis"]["case_title"]

        assert "Wasu" not in res_b["analysis"]["case_title"]
        assert "Satpal" not in res_a["analysis"]["case_title"]

        # Audit trails must reference their respective documents
        for event in res_a["audit_trail"]:
            assert event["source_filename"] == "sample_service_writ.pdf"
        for event in res_b["audit_trail"]:
            assert event["source_filename"] == "sample_criminal_appeal.pdf"
