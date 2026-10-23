"""Pytest fixtures for Legal Document Summarization test suite."""

import sys
from pathlib import Path
import pytest

TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
SAMPLE_DATA_DIR = PROJECT_ROOT / "sample_data"


@pytest.fixture(autouse=True)
def reset_gemini_coordinator():
    """Ensure clean service coordinator state for every test."""
    from agents.gemini_utils import reset_gemini_service_coordinator
    reset_gemini_service_coordinator()
    yield
    reset_gemini_service_coordinator()


@pytest.fixture
def sample_judgment_text() -> str:
    """Load the sample Indian legal judgment text."""
    path = SAMPLE_DATA_DIR / "sample_indian_judgment.txt"
    return path.read_text(encoding="utf-8")


@pytest.fixture
def sample_pdf_path() -> Path:
    """Return path to generated sample PDF."""
    return SAMPLE_DATA_DIR / "sample_civil_appeal.pdf"


@pytest.fixture
def sample_pdf_bytes(sample_pdf_path: Path) -> bytes:
    """Read binary bytes of sample PDF."""
    return sample_pdf_path.read_bytes()


@pytest.fixture
def mock_document_analysis() -> dict:
    """Sample structured document analysis output."""
    return {
        "case_title": "M/S. Bharat Infrastructure Limited v. State of Maharashtra & Anr.",
        "court_name": "Supreme Court of India",
        "case_number": "Civil Appeal No. 4582 of 2021",
        "decision_date": "2021",
        "petitioner": "M/S. Bharat Infrastructure Limited",
        "respondent": "State of Maharashtra & Anr.",
        "procedural_history": "Appeal from Bombay High Court dismissal of writ petition.",
        "factual_background": "Highway bypass construction concession terminated without 30-day cure notice.",
        "legal_claims": ["Violation of Article 14 fairness", "Arbitrary contractual termination"],
        "statutes_and_sections": ["Article 226", "Article 14", "Forest Conservation Act 1980"],
        "document_type": "Civil Appeal",
    }


@pytest.fixture
def mock_legal_reasoning() -> dict:
    """Sample structured legal reasoning output."""
    return {
        "questions_of_law": [
            "Maintainability of Article 226 writ in contractual disputes against State",
            "Mandatory nature of contractual 30-day cure notice under Article 14",
        ],
        "ratio_decidendi": (
            "Public authorities discharging commercial contracts remain bound by Article 14 fairness; "
            "failure to issue mandatory prerequisite cure notice vitiates termination."
        ),
        "obiter_dicta": "Disputes of complex engineering claims are generally subject to arbitration.",
        "petitioner_arguments": ["State failed to provide unencumbered ROW", "Lack of mandatory cure notice"],
        "respondent_arguments": ["Contractual remedy lies in arbitration", "Disputed questions of fact"],
        "court_holding_and_disposition": "Appeal Allowed. Termination quashed.",
        "key_precedents_analyzed": [
            {"case_citation": "ABL International Ltd. (2004) 3 SCC 553", "treatment": "Followed"}
        ],
    }
