"""Unit tests for Gemini DocumentAnalyzerAgent and LegalReasonerAgent."""

import json
from unittest.mock import MagicMock, patch
from agents.document_analyzer import DocumentAnalyzerAgent, LegalDocumentAnalysis
from agents.legal_reasoner import LegalReasonerAgent, LegalReasoningOutput


def test_document_analyzer_handles_missing_api_key(sample_judgment_text: str):
    """Test that analyzer provides graceful fallback when API key is missing."""
    agent = DocumentAnalyzerAgent(api_key=None)
    result = agent.analyze(sample_judgment_text)

    assert result["status"] == "API_KEY_MISSING"
    assert result["data"]["case_title"] == "API Key Not Configured"
    assert "GEMINI_API_KEY" in result["error"]


def test_legal_reasoner_handles_missing_api_key(sample_judgment_text: str):
    """Test that reasoner provides graceful fallback when API key is missing."""
    agent = LegalReasonerAgent(api_key=None)
    result = agent.reason(sample_judgment_text)

    assert result["status"] == "API_KEY_MISSING"
    assert result["data"]["court_holding_and_disposition"] == "API Key Not Configured"
    assert "GEMINI_API_KEY" in result["error"]


def test_document_analyzer_mock_gemini_response(sample_judgment_text: str):
    """Test analyzer parsing with a mocked Gemini client."""
    mock_payload = {
        "case_title": "State of Punjab v. Baldev Singh",
        "court_name": "Supreme Court of India",
        "case_number": "1999 (6) SCC 172",
        "decision_date": "1999",
        "petitioner": "State of Punjab",
        "respondent": "Baldev Singh",
        "procedural_history": "Reference to Constitution Bench on Section 50 of NDPS Act.",
        "factual_background": "Recovery of narcotics and mandatory compliance with search safeguards.",
        "legal_claims": ["Compliance with Section 50 of NDPS Act is mandatory"],
        "statutes_and_sections": ["Section 50 NDPS Act", "Article 21"],
        "document_type": "Criminal Appeal",
    }

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = f"```json\n{json.dumps(mock_payload)}\n```"
    mock_client.models.generate_content.return_value = mock_response

    with patch("google.genai.Client", return_value=mock_client):
        agent = DocumentAnalyzerAgent(api_key="mock_test_key_xyz")
        res = agent.analyze(sample_judgment_text)

        assert res["status"] == "SUCCESS"
        assert res["data"]["case_title"] == "State of Punjab v. Baldev Singh"
        assert "Section 50 NDPS Act" in res["data"]["statutes_and_sections"]


def test_legal_reasoner_mock_gemini_response(sample_judgment_text: str):
    """Test legal reasoner parsing with a mocked Gemini client."""
    mock_payload = {
        "questions_of_law": ["Whether compliance with Section 50 is imperative"],
        "ratio_decidendi": "Searching suspect without informing of statutory right vitiates recovery.",
        "obiter_dicta": "Individual liberty is protected under Article 21.",
        "petitioner_arguments": ["Substantial compliance suffices"],
        "respondent_arguments": ["Safeguard is mandatory"],
        "court_holding_and_disposition": "Appeals disposed of. Section 50 held mandatory.",
        "key_precedents_analyzed": [{"case_citation": "Ali Mustaffa (1995)", "treatment": "Followed"}],
    }

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps(mock_payload)
    mock_client.models.generate_content.return_value = mock_response

    with patch("google.genai.Client", return_value=mock_client):
        agent = LegalReasonerAgent(api_key="mock_test_key_xyz")
        res = agent.reason(sample_judgment_text)

        assert res["status"] == "SUCCESS"
        assert "recovery" in res["data"]["ratio_decidendi"].lower()
        assert res["data"]["court_holding_and_disposition"] == "Appeals disposed of. Section 50 held mandatory."


def test_document_analyzer_handles_empty_gemini_output(sample_judgment_text: str):
    """Regression test: empty output from Gemini returns ERROR status without crashing or guessing."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = ""
    mock_client.models.generate_content.return_value = mock_response

    with patch("google.genai.Client", return_value=mock_client):
        agent = DocumentAnalyzerAgent(api_key="mock_key")
        res = agent.analyze(sample_judgment_text)

        assert res["status"] == "ERROR"
        assert res["data"]["case_title"] == "Not stated in the document"
        assert res["error"] is not None


def test_document_analyzer_handles_invalid_json(sample_judgment_text: str):
    """Regression test: malformed non-JSON Gemini response returns ERROR with detailed error message."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "This is conversational text without valid JSON formatting or brackets."
    mock_client.models.generate_content.return_value = mock_response

    with patch("google.genai.Client", return_value=mock_client):
        agent = DocumentAnalyzerAgent(api_key="mock_key")
        res = agent.analyze(sample_judgment_text)

        assert res["status"] == "ERROR"
        assert "JSON parsing failed" in res["error"]
        assert res["data"]["case_title"] == "Not stated in the document"


def test_document_analyzer_handles_missing_fields_gracefully(sample_judgment_text: str):
    """Regression test: partial JSON with missing fields uses safe Pydantic defaults."""
    partial_payload = {
        "case_title": "Partial Case Title Only",
        "court_name": "High Court of Delhi",
    }
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps(partial_payload)
    mock_client.models.generate_content.return_value = mock_response

    with patch("google.genai.Client", return_value=mock_client):
        agent = DocumentAnalyzerAgent(api_key="mock_key")
        res = agent.analyze(sample_judgment_text)

        assert res["status"] == "SUCCESS"
        assert res["data"]["case_title"] == "Partial Case Title Only"
        assert res["data"]["court_name"] == "High Court of Delhi"
        assert res["data"]["petitioner"] == "Not stated in the document"
        assert res["data"]["statutes_and_sections"] == []


def test_legal_reasoner_handles_invalid_json(sample_judgment_text: str):
    """Regression test: malformed JSON in LegalReasoner returns ERROR without fabricated facts."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "{ broken json content: invalid syntax"
    mock_client.models.generate_content.return_value = mock_response

    with patch("google.genai.Client", return_value=mock_client):
        agent = LegalReasonerAgent(api_key="mock_key")
        res = agent.reason(sample_judgment_text)

        assert res["status"] == "ERROR"
        assert "JSON parsing failed" in res["error"]
        assert res["data"]["questions_of_law"] == []
        assert res["data"]["court_holding_and_disposition"] == "Not stated in the document"
