"""Document Analysis Agent using Google Gemini for Zero-Shot Legal Structure Extraction."""

import json
import re
import time
from typing import Any
from pydantic import BaseModel, Field


import config
from agents.gemini_utils import execute_gemini_with_retry, format_user_friendly_gemini_error


class LegalDocumentAnalysis(BaseModel):
    """Schema representing structured zero-shot legal document analysis."""
    case_title: str = Field(default="Not stated in the document", description="Full case title or parties name")
    court_name: str = Field(default="Not stated in the document", description="Court or tribunal and jurisdiction")
    case_number: str = Field(default="Not stated in the document", description="Case number, appeal number, or citation")
    decision_date: str = Field(default="Not stated in the document", description="Date or year of delivery")
    petitioner: str = Field(default="Not stated in the document", description="Petitioner or appellant")
    respondent: str = Field(default="Not stated in the document", description="Respondent or defendant")
    procedural_history: str = Field(
        default="Not stated in the document", description="Chronological procedural path leading to this decision"
    )
    factual_background: str = Field(
        default="Not stated in the document", description="Core factual matrix and background of the case"
    )
    legal_claims: list[str] = Field(
        default_factory=list, description="Primary legal claims or grounds raised"
    )
    statutes_and_sections: list[str] = Field(
        default_factory=list, description="Relevant statutory acts, sections, or constitutional articles cited"
    )
    document_type: str = Field(
        default="Judgment", description="Judgment, Order, Writ Petition, or Appellate Decision"
    )


class DocumentAnalyzerAgent:
    """Agent using Gemini to extract zero-shot legal structure and procedural facts."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        max_retries: int = 3,
        initial_delay: float = 1.5,
        avoid_retry_storm: bool = False,
    ):
        self.api_key = api_key
        self.model_name = model_name or config.DEFAULT_GEMINI_MODEL
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.avoid_retry_storm = avoid_retry_storm

    def _build_prompt(self, legal_text: str) -> str:
        truncated = legal_text[:12000]  # Stay safely within prompt context
        return f"""You are a specialized legal document analysis assistant for Indian court judgments.
Analyze the following judgment or case text and extract structured procedural and factual information strictly derived from this document.

IMPORTANT RULES:
1. Extract information ONLY from the provided text below.
2. If any field or detail is not stated or uncertain in the judgment, set its value to "Not stated in the document" (or [] for arrays).
3. Do NOT assume, extrapolate, or invent case titles, courts, citations, dates, or parties.
4. Distinguish between the petitioner/appellant and respondent.

Text:
\"\"\"{truncated}\"\"\"

Provide your response in strictly valid JSON format with the following keys:
{{
  "case_title": "string (e.g. Appellant v. Respondent or 'Not stated in the document')",
  "court_name": "string (Court name and jurisdiction or 'Not stated in the document')",
  "case_number": "string (Citation or Case/Appeal number or 'Not stated in the document')",
  "decision_date": "string (Date of decision or 'Not stated in the document')",
  "petitioner": "string (Petitioner / Appellant name or 'Not stated in the document')",
  "respondent": "string (Respondent / Defendant name or 'Not stated in the document')",
  "procedural_history": "string (Summary of prior proceedings leading to this court or 'Not stated in the document')",
  "factual_background": "string (Core factual dispute or 'Not stated in the document')",
  "legal_claims": ["claim 1", "claim 2"],
  "statutes_and_sections": ["Act Name Section X", "Constitution Article Y"],
  "document_type": "string (e.g. Civil Appeal, Criminal Appeal, Writ Petition, Review, Order)"
}}

Return ONLY valid raw JSON without markdown code fences or conversational text.
"""

    def analyze(self, legal_text: str, avoid_retry_storm: bool | None = None) -> dict[str, Any]:
        """Execute document analysis on the legal text."""
        start_time = time.time()

        if not legal_text or not legal_text.strip():
            raise ValueError("Legal document text cannot be empty.")

        if not self.api_key:
            # Informative fallback when no key is set
            return {
                "status": "API_KEY_MISSING",
                "model_identifier": self.model_name,
                "latency_seconds": 0.0,
                "data": LegalDocumentAnalysis(
                    case_title="API Key Not Configured",
                    factual_background="Configure GEMINI_API_KEY in .env to perform live Gemini document analysis.",
                ).model_dump(),
                "error": "Google Gemini API key is missing. Set GEMINI_API_KEY in .env file.",
            }

        successful_model = self.model_name
        retries_taken = 0
        avoid_storm = self.avoid_retry_storm if avoid_retry_storm is None else avoid_retry_storm

        try:
            from google import genai

            client = genai.Client(api_key=self.api_key)
            prompt = self._build_prompt(legal_text)

            raw_response, successful_model, retries_taken = execute_gemini_with_retry(
                client=client,
                primary_model=self.model_name,
                contents=prompt,
                max_retries=self.max_retries,
                initial_delay=self.initial_delay,
                fallback_models=config.FALLBACK_GEMINI_MODELS,
                avoid_retry_storm=avoid_storm,
            )

            # Clean code fences and locate outermost JSON object
            cleaned = re.sub(r"^```(json)?", "", raw_response.strip(), flags=re.MULTILINE)
            cleaned = re.sub(r"```$", "", cleaned.strip(), flags=re.MULTILINE).strip()

            json_str = cleaned
            json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)

            try:
                parsed_dict = json.loads(json_str)
                validated = LegalDocumentAnalysis(**parsed_dict)
            except Exception as parse_err:
                latency = round(time.time() - start_time, 2)
                return {
                    "status": "ERROR",
                    "model_identifier": successful_model,
                    "latency_seconds": latency,
                    "data": LegalDocumentAnalysis().model_dump(),
                    "error": f"JSON parsing failed on Gemini response ({parse_err}).",
                }

            latency = round(time.time() - start_time, 2)
            return {
                "status": "SUCCESS",
                "model_identifier": successful_model,
                "latency_seconds": latency,
                "data": validated.model_dump(),
                "error": None,
            }

        except Exception as exc:
            latency = round(time.time() - start_time, 2)
            friendly_err = format_user_friendly_gemini_error(
                exc, retries_attempted=retries_taken, model_id=self.model_name
            )
            return {
                "status": "ERROR",
                "model_identifier": successful_model,
                "latency_seconds": latency,
                "data": LegalDocumentAnalysis().model_dump(),
                "error": friendly_err,
            }
