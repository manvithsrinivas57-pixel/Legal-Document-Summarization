"""Unit tests for PDFExtractorAgent."""

from pathlib import Path
import pytest
from agents.pdf_extractor import PDFExtractorAgent, PDFExtractionError


def test_extract_from_text(sample_judgment_text: str):
    """Test manual text extraction and metadata computation."""
    agent = PDFExtractorAgent()
    result = agent.extract_from_text(sample_judgment_text, source_name="judgment.txt")

    assert result["status"] == "SUCCESS"
    assert len(result["text"]) > 500
    assert result["metadata"]["word_count"] > 100
    assert result["metadata"]["num_pages"] == 1
    assert "BHARAT INFRASTRUCTURE LIMITED" in result["text"]


def test_extract_from_bytes(sample_pdf_bytes: bytes):
    """Test in-memory PDF extraction using PyPDF."""
    agent = PDFExtractorAgent()
    result = agent.extract_from_bytes(sample_pdf_bytes, filename="appeal.pdf")

    assert result["status"] == "SUCCESS"
    assert result["metadata"]["num_pages"] == 1
    assert result["metadata"]["char_count"] > 200
    assert "SUPREME COURT" in result["text"]


def test_extract_from_file(sample_pdf_path: Path):
    """Test extraction from disk file."""
    agent = PDFExtractorAgent()
    result = agent.extract_from_file(sample_pdf_path)

    assert result["status"] == "SUCCESS"
    assert result["metadata"]["source_name"] == sample_pdf_path.name
    assert "CIVIL APPEAL" in result["text"]


def test_clean_legal_text_normalization():
    """Test that page numbers and whitespace artifacts are cleaned."""
    agent = PDFExtractorAgent(remove_headers_footers=True)
    dirty = "Page 1 of 12\n\n\nAppellant claims relief.   \t--- Page 2 ---\n\n\nRespondent opposes."
    cleaned = agent.clean_legal_text(dirty)

    assert "Page 1 of 12" not in cleaned
    assert "--- Page 2 ---" not in cleaned
    assert "Appellant claims relief." in cleaned
    assert "Respondent opposes." in cleaned
    assert "\n\n\n" not in cleaned


def test_empty_pdf_bytes_raises_error():
    """Test error handling when 0 bytes are passed."""
    agent = PDFExtractorAgent()
    with pytest.raises(PDFExtractionError) as exc_info:
        agent.extract_from_bytes(b"")
    assert "empty" in str(exc_info.value).lower()


def test_corrupt_pdf_bytes_raises_error():
    """Test error handling for corrupt binary stream."""
    agent = PDFExtractorAgent()
    with pytest.raises(PDFExtractionError):
        agent.extract_from_bytes(b"NOT_A_VALID_PDF_STREAM_CONTENT")


def test_nonexistent_file_raises_error():
    """Test error handling when file path does not exist."""
    agent = PDFExtractorAgent()
    with pytest.raises(PDFExtractionError) as exc_info:
        agent.extract_from_file("nonexistent_path_to_file.pdf")
    assert "not found" in str(exc_info.value).lower()
