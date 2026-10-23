"""Tests for Gemini HTTP 503 UNAVAILABLE retry logic, backoff, and graceful academic error handling."""

import json
from unittest.mock import MagicMock, patch, call
import pytest
import config

from agents.gemini_utils import (
    is_transient_gemini_error,
    format_user_friendly_gemini_error,
    execute_gemini_with_retry,
    get_supported_gemini_models,
    verify_gemini_model_id,
    reset_gemini_service_coordinator,
    get_gemini_service_coordinator,
)
from agents.document_analyzer import DocumentAnalyzerAgent, LegalDocumentAnalysis
from agents.legal_reasoner import LegalReasonerAgent, LegalReasoningOutput
from workflow.graph import build_legal_workflow_graph
from workflow.state import LegalWorkflowState


class MockCustomAPIError(Exception):
    """Custom exception simulating Google GenAI API errors with status or code attributes."""
    def __init__(self, message: str, code: int | None = None, status: str | None = None):
        super().__init__(message)
        self.code = code
        self.status = status


def test_is_transient_gemini_error_detects_503_and_transient_failures():
    """Verify transient error detection on 503, 429, UNAVAILABLE, and network drops."""
    assert is_transient_gemini_error(MockCustomAPIError("Service Unavailable", code=503))
    assert is_transient_gemini_error(MockCustomAPIError("Unavailable", status="UNAVAILABLE"))
    assert is_transient_gemini_error(MockCustomAPIError("Rate quota reached", code=429))
    assert is_transient_gemini_error(Exception("503 UNAVAILABLE: The model is overloaded. Please try again later."))
    assert is_transient_gemini_error(Exception("The service is experiencing high demand. Please try again shortly."))
    assert is_transient_gemini_error(ConnectionResetError("Connection reset by peer"))
    assert is_transient_gemini_error(TimeoutError("Client request timed out"))


def test_is_transient_gemini_error_ignores_non_transient_errors():
    """Non-transient errors (400, 401, 404) should not be treated as retryable transient errors."""
    assert not is_transient_gemini_error(MockCustomAPIError("Bad Request", code=400))
    assert not is_transient_gemini_error(MockCustomAPIError("Model not found", code=404))
    assert not is_transient_gemini_error(Exception("404 NOT_FOUND: models/gemini-1.5-flash not found"))
    assert not is_transient_gemini_error(Exception("API_KEY_INVALID: User API key is not valid"))


def test_format_user_friendly_gemini_error_503_contains_no_raw_dump():
    """User-friendly 503 message must explain high demand and reiterate academic integrity."""
    raw_error = Exception(
        "{'error': {'code': 503, 'message': 'The service is temporarily unavailable due to high demand.', 'status': 'UNAVAILABLE'}}"
    )
    formatted = format_user_friendly_gemini_error(raw_error, retries_attempted=3)
    assert "HTTP 503 UNAVAILABLE" in formatted
    assert "after 3 retries with exponential backoff" in formatted
    assert "legal analysis is not fabricated" in formatted
    assert "{'error'" not in formatted


def test_format_user_friendly_gemini_error_429_contains_clear_guidance():
    """User-friendly 429 message should guide the user about rate quotas."""
    raw_error = Exception("429 RESOURCE_EXHAUSTED: quota exceeded for api key")
    formatted = format_user_friendly_gemini_error(raw_error, retries_attempted=2)
    assert "HTTP 429 RESOURCE_EXHAUSTED" in formatted
    assert "Free-tier rate limits may apply" in formatted


def test_execute_gemini_with_retry_succeeds_on_first_try():
    """Client succeeds on attempt 0 with 0 retries taken."""
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = '{"case_title": "State of Punjab v. Baldev Singh"}'
    mock_client.models.generate_content.return_value = mock_resp

    text, model, retries = execute_gemini_with_retry(
        client=mock_client,
        primary_model="gemini-3.8-flash",
        contents="Analyze this case",
        max_retries=3,
        initial_delay=0.01,
    )

    assert text == mock_resp.text
    assert model == "gemini-3.8-flash"
    assert retries == 0
    assert mock_client.models.generate_content.call_count == 1


def test_execute_gemini_with_retry_recovers_after_temporary_503():
    """Client recovers after temporary 503 on 1st attempt, succeeding on 2nd attempt."""
    mock_client = MagicMock()
    err_503 = Exception("503 UNAVAILABLE: The model is overloaded. Please try again.")
    mock_resp = MagicMock()
    mock_resp.text = '{"ratio_decidendi": "Compliance with Section 50 NDPS Act is mandatory."}'

    # First call fails with 503, second succeeds
    mock_client.models.generate_content.side_effect = [err_503, mock_resp]

    with patch("time.sleep") as mock_sleep:
        text, model, retries = execute_gemini_with_retry(
            client=mock_client,
            primary_model="gemini-3.8-flash",
            contents="Analyze this case",
            max_retries=3,
            initial_delay=0.5,
            backoff_factor=2.0,
        )

    assert text == mock_resp.text
    assert model == "gemini-3.8-flash"
    assert retries == 1
    assert mock_client.models.generate_content.call_count == 2
    mock_sleep.assert_called_once_with(0.5)


def test_execute_gemini_with_retry_exhausts_retries_on_persistent_503():
    """Client retries up to max_retries and raises exception upon exhaustion."""
    mock_client = MagicMock()
    err_503 = Exception("503 UNAVAILABLE: Service unavailable.")
    mock_client.models.generate_content.side_effect = err_503

    with patch("time.sleep") as mock_sleep:
        with pytest.raises(Exception) as exc_info:
            execute_gemini_with_retry(
                client=mock_client,
                primary_model="gemini-3.8-flash",
                contents="Analyze text",
                max_retries=3,
                initial_delay=0.1,
                backoff_factor=2.0,
                fallback_models=[],
            )

    assert "503 UNAVAILABLE" in str(exc_info.value)
    # Initial attempt + 3 retries = 4 calls total
    assert mock_client.models.generate_content.call_count == 4
    assert mock_sleep.call_count == 3


def test_execute_gemini_with_retry_non_transient_error_does_not_retry():
    """Non-transient error like 400 Bad Request should fail immediately without retrying."""
    mock_client = MagicMock()
    err_400 = MockCustomAPIError("Invalid argument provided to Gemini API", code=400)
    mock_client.models.generate_content.side_effect = err_400

    with patch("time.sleep") as mock_sleep:
        with pytest.raises(Exception) as exc_info:
            execute_gemini_with_retry(
                client=mock_client,
                primary_model="gemini-3.8-flash",
                contents="Analyze text",
                max_retries=3,
                initial_delay=0.1,
            )

    assert mock_client.models.generate_content.call_count == 1
    mock_sleep.assert_not_called()


def test_document_analyzer_agent_retry_and_academic_integrity():
    """DocumentAnalyzerAgent retries on 503; if exhausted, returns clean defaults without fabricating facts."""
    agent = DocumentAnalyzerAgent(api_key="mock-key", model_name="gemini-3.8-flash", max_retries=2, initial_delay=0.01)

    mock_client = MagicMock()
    err_503 = Exception("503 UNAVAILABLE: The service is currently overloaded.")
    mock_client.models.generate_content.side_effect = err_503

    with patch("google.genai.Client", return_value=mock_client):
        with patch("time.sleep"):
            res = agent.analyze("The appellant filed a civil appeal under Section 96 of CPC.")

    assert res["status"] == "ERROR"
    assert "HTTP 503 UNAVAILABLE" in res["error"]
    assert "legal analysis is not fabricated" in res["error"]
    # Check academic integrity: defaults are not hallucinated
    assert res["data"]["case_title"] == "Not stated in the document"
    assert res["data"]["court_name"] == "Not stated in the document"
    assert res["data"]["factual_background"] == "Not stated in the document"


def test_legal_reasoner_agent_retry_and_academic_integrity():
    """LegalReasonerAgent retries on 503; if exhausted, returns clean defaults without fabricating holdings."""
    agent = LegalReasonerAgent(api_key="mock-key", model_name="gemini-3.8-flash", max_retries=2, initial_delay=0.01)

    mock_client = MagicMock()
    err_503 = Exception("503 UNAVAILABLE: Model unavailable.")
    mock_client.models.generate_content.side_effect = err_503

    with patch("google.genai.Client", return_value=mock_client):
        with patch("time.sleep"):
            res = agent.reason("Judgment text regarding Section 63 of Indian Succession Act.")

    assert res["status"] == "ERROR"
    assert "HTTP 503 UNAVAILABLE" in res["error"]
    assert res["data"]["ratio_decidendi"] == "Not stated in the document"
    assert res["data"]["court_holding_and_disposition"] == "Not stated in the document"


def test_agents_handle_failures_independently():
    """Ensure DocumentAnalyzerAgent failure does not prevent LegalReasonerAgent from running."""
    doc_agent = DocumentAnalyzerAgent(api_key="mock-key", model_name="gemini-3.8-flash", max_retries=1, initial_delay=0.01)
    reason_agent = LegalReasonerAgent(api_key="mock-key", model_name="gemini-3.8-flash", max_retries=1, initial_delay=0.01)

    # Document analyzer encounters persistent 503
    mock_client_fail = MagicMock()
    mock_client_fail.models.generate_content.side_effect = Exception("503 UNAVAILABLE: Overloaded")

    with patch("google.genai.Client", return_value=mock_client_fail):
        with patch("time.sleep"):
            doc_res = doc_agent.analyze("Some court text")

    assert doc_res["status"] == "ERROR"

    # Legal reasoner succeeds despite prior analyzer failure
    mock_client_success = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = json.dumps({
        "questions_of_law": ["Whether execution of Will was proved in accordance with Section 68 of Evidence Act."],
        "ratio_decidendi": "One attesting witness must be examined.",
        "court_holding_and_disposition": "Appeal Dismissed.",
    })
    mock_client_success.models.generate_content.return_value = mock_resp

    with patch("google.genai.Client", return_value=mock_client_success):
        reason_res = reason_agent.reason("Some court text", prior_analysis=doc_res["data"])

    assert reason_res["status"] == "SUCCESS"
    assert reason_res["data"]["ratio_decidendi"] == "One attesting witness must be examined."


def test_workflow_marks_partial_success_when_gemini_fails_and_bart_succeeds(sample_judgment_text, tmp_path):
    """Workflow must truthfully mark overall_status as PARTIAL_SUCCESS when BART succeeds but Gemini fails."""
    # Create dummy checkpoint directory with expected metadata so BART summarizer succeeds in test mode
    chk_dir = tmp_path / "mock_chk"
    chk_dir.mkdir()
    (chk_dir / "config.json").write_text('{"_name_or_path": "facebook/bart-base"}')
    (chk_dir / "training_metadata.json").write_text(json.dumps({
        "dataset": "CivilSum",
        "final_metrics": {"eval_rouge2": 0.22},
    }))

    app = build_legal_workflow_graph()

    initial_state: LegalWorkflowState = {
        "raw_text": sample_judgment_text,
        "source_filename": "janki_bhoir.txt",
        "document_id": None,
        "pdf_bytes": None,
        "metadata": {},
        "gemini_api_key": "mock-test-key",
        "gemini_model_name": "gemini-3.8-flash",
        "model_mode": "fine_tuned",
        "checkpoint_path": str(chk_dir),
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

    # Simulate Gemini 503 error on analysis and reasoning nodes
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("503 UNAVAILABLE: Overloaded")

    # Simulate BART summarizer success
    mock_summary_res = {
        "status": "SUCCESS",
        "model_identifier": "Mock-Fine-Tuned-BART",
        "latency_seconds": 1.2,
        "summary": "The Supreme Court dismissed the appeal holding that execution of will requires proper attestation.",
        "summary_word_count": 16,
        "is_fine_tuned": True,
        "checkpoint_path": str(chk_dir),
    }

    with patch("google.genai.Client", return_value=mock_client):
        with patch("time.sleep"):
            with patch("agents.bart_summarizer.BARTSummarizerAgent.summarize", return_value=mock_summary_res):
                final_state = app.invoke(initial_state)

    # Academic integrity: BART summary exists, but because Gemini failed, overall_status is PARTIAL_SUCCESS
    assert final_state["summary"] is not None
    assert final_state["overall_status"] == "PARTIAL_SUCCESS"
    assert final_state["analysis_error"] is not None
    assert "HTTP 503 UNAVAILABLE" in final_state["analysis_error"]


def test_execute_gemini_with_retry_recovers_on_second_retry_backoff():
    """Verify exponential backoff calculation across multiple retries before succeeding."""
    mock_client = MagicMock()
    err_503 = Exception("503 UNAVAILABLE: The model is experiencing high demand.")
    mock_resp = MagicMock()
    mock_resp.text = '{"case_title": "State v. Respondent"}'

    # Fails twice with 503, succeeds on 3rd attempt (attempt index 2)
    mock_client.models.generate_content.side_effect = [err_503, err_503, mock_resp]

    with patch("time.sleep") as mock_sleep:
        text, model, retries = execute_gemini_with_retry(
            client=mock_client,
            primary_model="gemini-3.8-flash",
            contents="Analyze text",
            max_retries=3,
            initial_delay=1.0,
            backoff_factor=2.0,
        )

    assert text == mock_resp.text
    assert retries == 2
    assert mock_client.models.generate_content.call_count == 3
    # First sleep: 1.0 * (2.0^0) = 1.0; Second sleep: 1.0 * (2.0^1) = 2.0
    assert mock_sleep.call_count == 2
    mock_sleep.assert_has_calls([call(1.0), call(2.0)])


def test_execute_gemini_with_retry_switches_to_fallback_model_on_503():
    """Verify that when primary model exhausts retries with 503, working fallback model is utilized."""
    mock_client = MagicMock()
    err_503 = Exception("503 UNAVAILABLE: Model overloaded.")
    mock_resp = MagicMock()
    mock_resp.text = '{"case_title": "Fallback Success Case"}'

    def mock_generate(model, contents):
        if model == "gemini-3.8-flash":
            raise err_503
        elif model == "gemini-flash-lite-latest":
            return mock_resp
        raise Exception("Unexpected model called")

    mock_client.models.generate_content.side_effect = mock_generate

    with patch("time.sleep"):
        text, model, retries = execute_gemini_with_retry(
            client=mock_client,
            primary_model="gemini-3.8-flash",
            contents="Analyze text",
            max_retries=3,
            initial_delay=0.01,
            fallback_models=["gemini-flash-lite-latest", "gemini-3.5-flash-lite"],
        )

    assert text == mock_resp.text
    assert model == "gemini-flash-lite-latest"
    # Primary attempted 4 times (0 + 3 retries), then fallback attempted once
    assert mock_client.models.generate_content.call_count == 5


def test_invalid_model_id_fails_immediately_without_retrying():
    """Invalid model IDs (HTTP 404 NOT_FOUND) should fail immediately with 0 retries and 0 sleep."""
    mock_client = MagicMock()
    err_404 = MockCustomAPIError("404 NOT_FOUND: Model models/non-existent-model not found", code=404)
    mock_client.models.generate_content.side_effect = err_404

    with patch("time.sleep") as mock_sleep:
        with pytest.raises(Exception) as exc_info:
            execute_gemini_with_retry(
                client=mock_client,
                primary_model="non-existent-model",
                contents="Analyze text",
                max_retries=3,
                initial_delay=1.0,
            )

    assert "404" in str(exc_info.value)
    # Non-transient: strictly only 1 call attempted, zero retries, zero sleep
    assert mock_client.models.generate_content.call_count == 1
    mock_sleep.assert_not_called()


def test_verify_gemini_model_id_utility():
    """Verify that verify_gemini_model_id accurately verifies active vs invalid models."""
    mock_client = MagicMock()
    mock_model = MagicMock()
    mock_model.supported_actions = ["generateContent"]
    mock_client.models.get.return_value = mock_model

    # Valid model returns True
    assert verify_gemini_model_id(mock_client, "gemini-3.8-flash") is True
    assert verify_gemini_model_id(mock_client, "models/gemini-3.8-flash") is True

    # Missing generateContent action returns False
    mock_model_tts = MagicMock()
    mock_model_tts.supported_actions = ["generateSpeech"]
    mock_client.models.get.return_value = mock_model_tts
    assert verify_gemini_model_id(mock_client, "gemini-tts-model") is False

    # Invalid model raising 404 returns False
    mock_client.models.get.side_effect = Exception("404 NOT_FOUND: Model not found")
    assert verify_gemini_model_id(mock_client, "completely-bogus-model") is False
    assert verify_gemini_model_id(mock_client, "") is False


def test_get_supported_gemini_models_filtering():
    """Verify that get_supported_gemini_models filters out deprecated, TTS, and non-text models."""
    # When no key is given or offline, returns official verified list
    models = get_supported_gemini_models(api_key=None, force_refresh=True)
    assert "gemini-3.8-flash" in models
    assert "gemini-flash-lite-latest" in models
    # Deprecated 2.5 models must not be present
    assert not any("gemini-2.5" in m for m in models)


def test_format_user_friendly_gemini_error_invalid_model_404():
    """Verify that 404 invalid model error formats a clear, non-confusing user message."""
    raw_error = Exception("404 NOT_FOUND: Model models/gemini-old-model is not found")
    formatted = format_user_friendly_gemini_error(raw_error, model_id="gemini-old-model")
    assert "HTTP 404 NOT_FOUND" in formatted
    assert "gemini-old-model" in formatted
    assert "legal analysis is not fabricated" in formatted
    assert "{'error'" not in formatted


def test_avoid_duplicate_retry_storms_between_analyzer_and_reasoner():
    """Document Analysis 503 failure prevents Jurisprudential Reasoning from triggering a duplicate retry storm."""
    doc_agent = DocumentAnalyzerAgent(api_key="mock-key", model_name="gemini-3.8-flash", max_retries=2, initial_delay=0.1)
    reason_agent = LegalReasonerAgent(api_key="mock-key", model_name="gemini-3.8-flash", max_retries=2, initial_delay=0.1)

    mock_client = MagicMock()
    err_503 = Exception("503 UNAVAILABLE: High demand.")
    mock_client.models.generate_content.side_effect = err_503

    with patch("google.genai.Client", return_value=mock_client):
        with patch("time.sleep") as mock_sleep:
            # Stage 1: Document Analyzer exhausts retries (initial + 2 retries = 3 calls) plus distinct fallbacks
            doc_res = doc_agent.analyze("Some court judgment text")
            assert doc_res["status"] == "ERROR"
            expected_stage1_calls = 3 + len([m for m in config.FALLBACK_GEMINI_MODELS if m != "gemini-3.8-flash"])
            assert mock_client.models.generate_content.call_count == expected_stage1_calls
            assert mock_sleep.call_count == 2

            mock_client.models.generate_content.reset_mock()
            mock_sleep.reset_mock()

            # Stage 2: Legal Reasoner runs with avoid_retry_storm=True (as set by LangGraph workflow on 503)
            reason_res = reason_agent.reason("Some court judgment text", avoid_retry_storm=True)
            assert reason_res["status"] == "ERROR"
            # Crucial assertion: Must NOT repeat the 2 retries + backoff sleep!
            # Only 1 probe attempt is made, with 0 sleeps, preventing duplicate storm.
            assert mock_client.models.generate_content.call_count == 1
            assert mock_sleep.call_count == 0


def test_avoid_simultaneous_retry_storms_concurrent_threads():
    """Simultaneous calls from concurrent threads are coordinated to prevent concurrent retry storms."""
    import threading

    mock_client = MagicMock()
    err_503 = Exception("503 UNAVAILABLE: Spikes in demand.")
    mock_client.models.generate_content.side_effect = err_503

    results = []

    def run_call():
        with patch("time.sleep"):
            try:
                execute_gemini_with_retry(
                    client=mock_client,
                    primary_model="gemini-3.8-flash",
                    contents="Concurrent probe",
                    max_retries=1,
                    initial_delay=0.01,
                    fallback_models=[],
                )
            except Exception as e:
                results.append(e)

    t1 = threading.Thread(target=run_call)
    t2 = threading.Thread(target=run_call)

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Both threads cleanly catch the 503 without crashing or deadlocking
    assert len(results) == 2
    for r in results:
        assert "503 UNAVAILABLE" in str(r)


def test_workflow_handles_invalid_model_id_truthfully(sample_judgment_text, tmp_path):
    """Workflow truthfully records 404 for invalid model IDs without inventing legal facts."""
    chk_dir = tmp_path / "mock_chk"
    chk_dir.mkdir()
    (chk_dir / "config.json").write_text('{"_name_or_path": "facebook/bart-base"}')
    (chk_dir / "training_metadata.json").write_text(json.dumps({
        "dataset": "CivilSum",
        "final_metrics": {"eval_rouge2": 0.22},
    }))

    app = build_legal_workflow_graph()

    initial_state: LegalWorkflowState = {
        "raw_text": sample_judgment_text,
        "source_filename": "sample.txt",
        "document_id": None,
        "pdf_bytes": None,
        "metadata": {},
        "gemini_api_key": "mock-key",
        "gemini_model_name": "gemini-invalid-model-999",
        "gemini_service_unavailable": False,
        "model_mode": "fine_tuned",
        "checkpoint_path": str(chk_dir),
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

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = MockCustomAPIError("404 NOT_FOUND", code=404)

    mock_summary_res = {
        "status": "SUCCESS",
        "model_identifier": "Mock-Fine-Tuned-BART",
        "latency_seconds": 1.0,
        "summary": "Summary text generated successfully.",
        "summary_word_count": 4,
        "is_fine_tuned": True,
        "checkpoint_path": str(chk_dir),
    }

    with patch("google.genai.Client", return_value=mock_client):
        with patch("agents.bart_summarizer.BARTSummarizerAgent.summarize", return_value=mock_summary_res):
            final_state = app.invoke(initial_state)

    assert final_state["overall_status"] == "PARTIAL_SUCCESS"
    assert "HTTP 404 NOT_FOUND" in final_state["analysis_error"]
    assert final_state["analysis"]["case_title"] == "Not stated in the document"
