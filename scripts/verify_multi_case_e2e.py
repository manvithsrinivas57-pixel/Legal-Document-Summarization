"""Verification script executing the end-to-end workflow across multiple legally distinct judgment PDFs."""

import sys
from pathlib import Path
import json

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

import config
from workflow.graph import build_legal_workflow_graph
from workflow.state import LegalWorkflowState

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample_data"
chk_path = str(config.get_active_checkpoint_path())
gemini_key = config.get_gemini_api_key()

test_cases = [
    {
        "name": "Case 1: Commercial / Writ Appeal (Supreme Court of India)",
        "pdf_path": SAMPLE_DIR / "sample_civil_appeal.pdf",
    },
    {
        "name": "Case 2: Service Law / Retiral Recovery (Punjab & Haryana High Court)",
        "pdf_path": SAMPLE_DIR / "sample_service_writ.pdf",
    },
    {
        "name": "Case 3: Criminal Appeal / Acquittal (Supreme Court of India)",
        "pdf_path": SAMPLE_DIR / "sample_criminal_appeal.pdf",
    },
    {
        "name": "Case 4: Scanned Image-Only PDF (Testing OCR Requirement Handling)",
        "pdf_path": SAMPLE_DIR / "sample_scanned_image_only.pdf",
    },
]

app = build_legal_workflow_graph()

print("=" * 80)
print("EVALUATING MULTI-CASE PIPELINE ACROSS DISTINCT JUDGMENTS")
print("=" * 80)

for case_info in test_cases:
    pdf_p = case_info["pdf_path"]
    print(f"\n>>> EXECUTING: {case_info['name']}")
    print(f"File: {pdf_p.name} ({pdf_p.stat().st_size} bytes)")

    with open(pdf_p, "rb") as f:
        pdf_bytes = f.read()

    init_state: LegalWorkflowState = {
        "raw_text": "",
        "source_filename": pdf_p.name,
        "document_id": None,
        "pdf_bytes": pdf_bytes,
        "metadata": {},
        "gemini_api_key": gemini_key,
        "gemini_model_name": config.DEFAULT_GEMINI_MODEL,
        "model_mode": "fine_tuned",
        "checkpoint_path": chk_path,
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

    res = app.invoke(init_state)

    status = res.get("overall_status")
    print(f"Overall Status: {status}")
    print(f"Document ID: {res.get('document_id')}")

    if status == "FAILED" and "scanned" in res.get("explanation", "").lower():
        print(f"Handled Gracefully: {res.get('explanation')}")
        continue

    # Document Extraction
    meta = res.get("metadata", {})
    print(f"Extraction -> Pages: {meta.get('num_pages')}, Words: {meta.get('word_count')}, Chars: {meta.get('char_count')}")

    # Gemini Legal Analysis
    ana = res.get("analysis") or {}
    print(f"Case Title: {ana.get('case_title')}")
    print(f"Court: {ana.get('court_name')}")
    print(f"Citation: {ana.get('case_number')}")
    print(f"Date: {ana.get('decision_date')}")
    print(f"Parties: {ana.get('petitioner')} vs {ana.get('respondent')}")
    print(f"Statutes Cited: {ana.get('statutes_and_sections')}")

    # Gemini Legal Reasoning
    reas = res.get("reasoning") or {}
    print(f"Questions of Law ({len(reas.get('questions_of_law', []))}): {reas.get('questions_of_law')[:2]}")
    print(f"Ratio Decidendi: {reas.get('ratio_decidendi')[:120]}...")
    print(f"Holding: {reas.get('court_holding_and_disposition')}")

    # BART Summarization
    summary = res.get("summary") or ""
    print(f"Summary Words: {len(summary.split())} (Model: {res.get('summary_model_id')})")
    print(f"Summary Excerpt: {summary[:150]}...")

    # Validation
    val = res.get("validation") or {}
    print(f"Validation Grade: {val.get('overall_status')}, Coverage: {val.get('coverage_score')}, Consistency: {val.get('consistency_score')}")
    print(f"Unsupported Claims ({val.get('unsupported_claims_count', 0)}): {val.get('unsupported_claims')}")

print("\n" + "=" * 80)
print("MULTI-CASE VERIFICATION RUN COMPLETE")
print("=" * 80)
