"""PDF text extraction and cleaning agent using PyPDF."""

import io
import re
import time
from pathlib import Path
from typing import Any
import pypdf


class PDFExtractionError(Exception):
    """Custom exception raised when PDF parsing or extraction fails."""
    pass


class PDFExtractorAgent:
    """Agent responsible for ingesting legal PDFs or raw text and extracting clean legal text."""

    def __init__(self, remove_headers_footers: bool = True):
        self.remove_headers_footers = remove_headers_footers

    def clean_legal_text(self, text: str) -> str:
        """Normalize whitespace, remove line break artifacts, and strip page footer/header patterns."""
        if not text:
            return ""

        # Normalize line endings and non-breaking spaces
        text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\xa0", " ").replace("\x0c", "\n")

        # Normalize common unicode punctuation
        text = text.replace("“", "\"").replace("”", "\"").replace("‘", "'").replace("’", "'")
        text = text.replace("—", " - ").replace("–", " - ")

        if self.remove_headers_footers:
            # Remove recurring page number footers e.g. "Page 1 of 12", "--- Page 1 ---", "- 1 -", "Page No. 4"
            text = re.sub(r"(?i)\bpage(\s+no\.?)?\s+\d+(\s+of\s+\d+)?\b", " ", text)
            text = re.sub(r"^\s*[-—–]\s*\d+\s*[-—–]\s*$", "", text, flags=re.MULTILINE)
            # Remove court watermarks/digital signature lines often found in Indian High Court PDFs
            text = re.sub(r"(?i)digitally signed by:?.*?(?=\n|$)", " ", text)

        # Remove redundant horizontal rules, asterisks, or underscores
        text = re.sub(r"[_—–\-\*=]{4,}", " ", text)

        # Merge multiple consecutive whitespace and newlines while keeping paragraph breaks
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
        return text.strip()

    def extract_from_bytes(self, pdf_bytes: bytes, filename: str = "document.pdf") -> dict[str, Any]:
        """Extract legal text from in-memory PDF bytes."""
        start_time = time.time()
        if not pdf_bytes:
            raise PDFExtractionError("PDF file is empty (0 bytes received).")

        try:
            stream = io.BytesIO(pdf_bytes)
            reader = pypdf.PdfReader(stream)
            num_pages = len(reader.pages)

            if num_pages == 0:
                raise PDFExtractionError("PDF document contains 0 pages.")

            page_texts: list[str] = []
            for page_idx, page in enumerate(reader.pages):
                try:
                    extracted = page.extract_text() or ""
                except Exception:
                    extracted = ""
                page_texts.append(extracted)

            combined_raw = "\n\n".join(page_texts)
            cleaned_text = self.clean_legal_text(combined_raw)

            if not cleaned_text.strip():
                raise PDFExtractionError(
                    f"No extractable text found in PDF ({num_pages} page(s) analyzed). "
                    "The document appears to be a scanned image-only PDF, encrypted, or lacks a readable text stream. "
                    "Optical Character Recognition (OCR) is required to process scanned judgment PDFs."
                )

            words = cleaned_text.split()
            elapsed_ms = round((time.time() - start_time) * 1000, 2)

            return {
                "text": cleaned_text,
                "metadata": {
                    "source_name": filename,
                    "num_pages": num_pages,
                    "word_count": len(words),
                    "char_count": len(cleaned_text),
                    "extraction_time_ms": elapsed_ms,
                    "is_scanned": False,
                    "pages_detail": [
                        {"page_number": idx + 1, "char_count": len(pt)}
                        for idx, pt in enumerate(page_texts)
                    ],
                },
                "status": "SUCCESS",
            }

        except PDFExtractionError:
            raise
        except Exception as exc:
            raise PDFExtractionError(f"Failed to process PDF: {str(exc)}") from exc

    def extract_from_file(self, file_path: str | Path) -> dict[str, Any]:
        """Extract text from a file on disk."""
        path = Path(file_path)
        if not path.exists():
            raise PDFExtractionError(f"File not found at path: {path}")

        with open(path, "rb") as f:
            data = f.read()
        return self.extract_from_bytes(data, filename=path.name)

    def extract_from_text(self, raw_text: str, source_name: str = "manual_input.txt") -> dict[str, Any]:
        """Wrap and clean raw text entered manually."""
        start_time = time.time()
        cleaned_text = self.clean_legal_text(raw_text)

        if not cleaned_text.strip():
            raise PDFExtractionError("Provided legal text is empty.")

        words = cleaned_text.split()
        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "text": cleaned_text,
            "metadata": {
                "source_name": source_name,
                "num_pages": 1,
                "word_count": len(words),
                "char_count": len(cleaned_text),
                "extraction_time_ms": elapsed_ms,
                "pages_detail": [{"page_number": 1, "char_count": len(cleaned_text)}],
            },
            "status": "SUCCESS",
        }
