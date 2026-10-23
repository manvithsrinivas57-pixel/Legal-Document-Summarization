"""End-to-end verification script on the user's uploaded judgment PDF."""

import glob
import sys
import os
import json
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")
import config
from workflow.graph import build_legal_workflow_graph
from workflow.state import LegalWorkflowState

matches = glob.glob(r"C:\Users\sujat.MANVITH\OneDrive\**\*Janki*.PDF", recursive=True)
if not matches:
    print("Error: Janki judgment PDF not found!")
    sys.exit(1)

pdf_path = matches[0]
with open(pdf_path, "rb") as f:
    pdf_bytes = f.read()

app = build_legal_workflow_graph()
initial_state: LegalWorkflowState = {
    "raw_text": "",
    "source_filename": os.path.basename(pdf_path),
    "pdf_bytes": pdf_bytes,
    "metadata": {},
    "gemini_api_key": config.get_gemini_api_key(),
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

print("=== EXECUTING END-TO-END WORKFLOW ON JANKI PDF ===")
final_state = app.invoke(initial_state)

print("\n1. EXTRACTION:")
print("Source word count:", final_state["metadata"].get("word_count"))
print("Number of pages:", final_state["metadata"].get("num_pages"))

print("\n2. GEMINI LEGAL ANALYSIS:")
print("Status analysis_error:", final_state.get("analysis_error"))
print("Case title:", final_state["analysis"].get("case_title"))
print("Court name:", final_state["analysis"].get("court_name"))
print("Case citation:", final_state["analysis"].get("case_number"))
print("Decision date:", final_state["analysis"].get("decision_date"))
print("Petitioner:", final_state["analysis"].get("petitioner"))
print("Respondent:", final_state["analysis"].get("respondent"))
print("Statutes cited:", final_state["analysis"].get("statutes_and_sections"))

print("\n3. GEMINI LEGAL REASONING:")
print("Status reasoning_error:", final_state.get("reasoning_error"))
print("Questions of law count:", len(final_state["reasoning"].get("questions_of_law", [])))
for q in final_state["reasoning"].get("questions_of_law", []):
    print("  - Question:", q)
print("Ratio decidendi:", final_state["reasoning"].get("ratio_decidendi"))
print("Court holding:", final_state["reasoning"].get("court_holding_and_disposition"))

print("\n4. BART SUMMARIZATION:")
print("Summary model id:", final_state.get("summary_model_id"))
summary = final_state.get("summary", "")
print("Summary word count:", len(summary.split()))
print("Summary text:\n", summary)

print("\n5. VALIDATION REPORT:")
val = final_state.get("validation")
print("Overall status:", val.get("overall_status"))
print("Coverage score:", val.get("coverage_score"))
print("Covered elements:", val.get("covered_elements"))
print("Missing elements:", val.get("missing_elements"))
print("Consistency score:", val.get("consistency_score"))
print("Unsupported claims count:", val.get("unsupported_claims_count"))
print("Unsupported claims:", val.get("unsupported_claims"))

print("\n6. AUDIT TRAIL:")
for step in final_state.get("audit_trail", []):
    stage = step.get("stage_name")
    status = step.get("status")
    model = step.get("model_identifier")
    lat = step.get("latency_seconds")
    det = step.get("details")
    print(f"[{stage}] -> Status: {status}, Model: {model}, Latency: {lat}s, Details: {det}")
