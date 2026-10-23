"""Legal Reasoning Agent using Google Gemini for Zero-Shot Ratio Decidendi and Precedent Reasoning."""

import json
import re
import time
from typing import Any
from pydantic import BaseModel, Field


import config
from agents.gemini_utils import execute_gemini_with_retry, format_user_friendly_gemini_error


class LegalReasoningOutput(BaseModel):
    """Schema representing structured zero-shot legal reasoning and case disposition."""
    questions_of_law: list[str] = Field(
        default_factory=list, description="Core legal questions or issues framed for determination"
    )
    ratio_decidendi: str = Field(
        default="Not stated in the document", description="The binding legal principle or rationale forming the basis of the judgment"
    )
    obiter_dicta: str = Field(
        default="Not stated in the document", description="Judicial observations made in passing, not strictly binding as precedent"
    )
    petitioner_arguments: list[str] = Field(
        default_factory=list, description="Primary arguments submitted by the petitioner/appellant"
    )
    respondent_arguments: list[str] = Field(
        default_factory=list, description="Primary arguments submitted by the respondent/defendant"
    )
    statutes_discussed: list[str] = Field(
        default_factory=list, description="Statutory provisions and constitutional articles analyzed"
    )
    court_holding_and_disposition: str = Field(
        default="Not stated in the document", description="Final decision and operative order (e.g. Appeal Allowed, Dismissed, Decreed)"
    )
    key_precedents_analyzed: list[dict[str, str]] = Field(
        default_factory=list,
        description="List of cited precedents with case_citation, treatment, and relevance",
    )


class LegalReasonerAgent:
    """Agent using Gemini to extract legal doctrine, ratio decidendi, and judicial disposition."""

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

    def _build_prompt(self, legal_text: str, prior_analysis: dict[str, Any] | None = None) -> str:
        truncated = legal_text[:14000]
        context_str = ""
        if prior_analysis and prior_analysis.get("case_title") != "Not stated in the document":
            context_str = f"""
Prior Structural Context from this judgment:
- Case Title: {prior_analysis.get('case_title', 'Not stated')}
- Court: {prior_analysis.get('court_name', 'Not stated')}
- Legal Claims: {', '.join(prior_analysis.get('legal_claims', []))}
- Statutes: {', '.join(prior_analysis.get('statutes_and_sections', []))}
"""

        return f"""You are a specialized legal reasoning and jurisprudence assistant for Indian court judgments.
Analyze the following judgment text and extract the rigorous legal doctrine and judicial reasoning strictly from this specific document.

IMPORTANT RULES:
1. Derive all answers exclusively from the text below.
2. Clearly distinguish between:
   (a) The submissions/arguments of the petitioner/appellant,
   (b) The submissions/arguments of the respondent,
   (c) The court's own ratio decidendi and binding legal holdings.
3. If obiter dicta, precedents, or specific arguments are not mentioned in the text, return "Not stated in the document" (or [] for arrays). Never invent precedents or cite decisions from other cases.
{context_str}

Text:
\"\"\"{truncated}\"\"\"

Provide your response in strictly valid JSON format with the following keys:
{{
  "questions_of_law": ["Question 1", "Question 2"],
  "petitioner_arguments": ["Argument 1 of petitioner/appellant"],
  "respondent_arguments": ["Argument 1 of respondent/state"],
  "statutes_discussed": ["Statute / Article / Section actually interpreted"],
  "ratio_decidendi": "string (clear articulation of the legal rule or principle established by the court)",
  "obiter_dicta": "string (notable judicial commentary or observations, or 'Not stated in the document')",
  "court_holding_and_disposition": "string (e.g. Appeal Allowed / Dismissed / Disposed, with specific operative relief)",
  "key_precedents_analyzed": [
    {{"case_citation": "Case Name", "treatment": "Followed / Distinguished / Overruled / Cited", "relevance": "Brief note on why cited"}}
  ]
}}

Return ONLY valid raw JSON without markdown code fences or conversational text.
"""

    def reason(
        self,
        legal_text: str,
        prior_analysis: dict[str, Any] | None = None,
        avoid_retry_storm: bool | None = None,
    ) -> dict[str, Any]:
        """Perform zero-shot legal reasoning on the judgment."""
        start_time = time.time()

        if not legal_text or not legal_text.strip():
            raise ValueError("Legal text cannot be empty.")

        if not self.api_key:
            return {
                "status": "API_KEY_MISSING",
                "model_identifier": self.model_name,
                "latency_seconds": 0.0,
                "data": LegalReasoningOutput(
                    ratio_decidendi="Configure GEMINI_API_KEY in .env to perform live Gemini legal reasoning.",
                    court_holding_and_disposition="API Key Not Configured",
                ).model_dump(),
                "error": "Google Gemini API key is missing. Set GEMINI_API_KEY in .env file.",
            }

        successful_model = self.model_name
        retries_taken = 0
        avoid_storm = self.avoid_retry_storm if avoid_retry_storm is None else avoid_retry_storm

        try:
            from google import genai

            client = genai.Client(api_key=self.api_key)
            prompt = self._build_prompt(legal_text, prior_analysis)

            raw_response, successful_model, retries_taken = execute_gemini_with_retry(
                client=client,
                primary_model=self.model_name,
                contents=prompt,
                max_retries=self.max_retries,
                initial_delay=self.initial_delay,
                fallback_models=config.FALLBACK_GEMINI_MODELS,
                avoid_retry_storm=avoid_storm,
            )

            cleaned = re.sub(r"^```(json)?", "", raw_response.strip(), flags=re.MULTILINE)
            cleaned = re.sub(r"```$", "", cleaned.strip(), flags=re.MULTILINE).strip()

            json_str = cleaned
            json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)

            try:
                parsed_dict = json.loads(json_str)
                validated = LegalReasoningOutput(**parsed_dict)
            except Exception as parse_err:
                latency = round(time.time() - start_time, 2)
                return {
                    "status": "ERROR",
                    "model_identifier": successful_model,
                    "latency_seconds": latency,
                    "data": LegalReasoningOutput().model_dump(),
                    "error": f"JSON parsing failed on Gemini reasoning response ({parse_err}).",
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
                "data": LegalReasoningOutput().model_dump(),
                "error": friendly_err,
            }
