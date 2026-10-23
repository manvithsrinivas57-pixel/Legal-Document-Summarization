"""Summary Validation Agent for Coverage, Consistency, and Hallucination / Unsupported Claims."""

import re
import time
from typing import Any
from pydantic import BaseModel, Field


class ValidationReport(BaseModel):
    """Detailed summary validation report checking coverage, consistency, and unsupported claims."""
    overall_status: str = Field(
        default="PASSED", description="Validation status: PASSED, WARNING, or FAILED"
    )
    coverage_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Proportion of key legal elements covered in summary"
    )
    covered_elements: list[str] = Field(
        default_factory=list, description="Legal entities and elements present in summary"
    )
    missing_elements: list[str] = Field(
        default_factory=list, description="Critical legal elements absent from summary"
    )
    consistency_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Faithfulness and consistency with source text"
    )
    unsupported_claims: list[dict[str, str]] = Field(
        default_factory=list,
        description="Specific numbers, dates, sections, or entities in summary not found in source",
    )
    unsupported_claims_count: int = Field(default=0)
    recommendations: list[str] = Field(
        default_factory=list, description="Actionable recommendations to improve summary quality"
    )


import config


class ValidationAgent:
    """Agent that performs rigorous quality, faithfulness, and ground-truth validation on legal summaries."""

    def __init__(self, api_key: str | None = None, model_name: str | None = None):
        self.api_key = api_key
        self.model_name = model_name or config.DEFAULT_GEMINI_MODEL

    def _extract_specific_entities(self, text: str) -> dict[str, Any]:
        """Extract explicit verifiable tokens: numbers, dates, statutory sections, paragraph citations, precedents."""
        # Find 4-digit years e.g. 1998, 2024
        years = set(re.findall(r"\b(19\d{2}|20\d{2})\b", text))

        # 1. Statutory Sections & Constitutional Articles
        sections = set()
        section_numbers_consumed = set()

        # Match compound patterns: e.g. "Articles 14 and 16", "Sections 68, 71 and 114", "Section 63(c)", "Rule 2.2(b)"
        prefix_pattern = (
            r"(?i)\b(sections?|sec\.|s\.|articles?|art\.|clauses?|cl\.|orders?|rules?|o\.|r\.)\s+"
            r"(\d+(?:\.\d+)?[a-z]?(?:\([a-z0-9]+\))*(?:\s*(?:,|and|or|to|&)\s*\d+(?:\.\d+)?[a-z]?(?:\([a-z0-9]+\))*)*)"
        )
        for match in re.finditer(prefix_pattern, text):
            prefix_raw = match.group(1).lower()
            if prefix_raw.startswith("art"):
                canon_prefix = "article"
            elif prefix_raw.startswith("sec") or prefix_raw == "s.":
                canon_prefix = "section"
            elif prefix_raw.startswith("cl"):
                canon_prefix = "clause"
            elif prefix_raw.startswith("order") or prefix_raw == "o.":
                canon_prefix = "order"
            elif prefix_raw.startswith("rule") or prefix_raw == "r.":
                canon_prefix = "rule"
            else:
                canon_prefix = prefix_raw

            content = match.group(2)
            sub_tokens = re.findall(r"\b\d+(?:\.\d+)?[a-z]?(?:\([a-z0-9]+\))*|\b\d+\b", content)
            for tok in sub_tokens:
                sections.add(f"{canon_prefix} {tok.lower()}")
                base_digits = re.findall(r"\b\d+\b", tok)
                section_numbers_consumed.update(base_digits)

        # Isolated simple sections fallback
        simple_pattern = r"(?i)\b(section|sec\.|s\.|article|art\.|clause|cl\.|rule|order)\s+(\d+(?:\.\d+)?[a-z]?(?:\([a-z0-9]+\))?)"
        for match in re.finditer(simple_pattern, text):
            p = (
                "article"
                if match.group(1).lower().startswith("art")
                else ("section" if (match.group(1).lower().startswith("sec") or match.group(1).lower() == "s.")
                      else ("clause" if match.group(1).lower().startswith("cl") else match.group(1).lower()))
            )
            tok = match.group(2).lower()
            sections.add(f"{p} {tok}")
            section_numbers_consumed.update(re.findall(r"\b\d+\b", tok))

        # 2. Document Paragraph references: e.g. [Paras 7 and 8], [Para 9], Para 11, [para 10]
        paragraph_numbers_consumed = set()
        para_pattern = r"(?i)\b(?:paras?|paragraphs?)\s+(\d+[a-z]?(?:\s*(?:,|and|or|to|&)\s*\d+[a-z]?)*)"
        for match in re.finditer(para_pattern, text):
            content = match.group(1)
            para_digits = re.findall(r"\b\d+\b", content)
            paragraph_numbers_consumed.update(para_digits)

        # 3. Statutory acts e.g. Evidence Act, Succession Act, IPC, CrPC, CPC, Constitution
        acts = set(
            re.findall(
                r"(?i)\b(?:Evidence Act|Succession Act|IPC|CrPC|CPC|Negotiable Instruments Act|"
                r"Constitution(?: of India)?|Arbitration Act|Forest \(Conservation\) Act|"
                r"Army Act|Consumer Protection Act|Punjab Civil Services Rules)\b",
                text,
            )
        )

        # 4. Precedent Case Citations (e.g. "X v. Y", "X vs. Y", "AIR 1991 SC 2010", "(2004) 3 SCC 553")
        precedent_patterns = [
            r"(?i)\b([A-Z][a-zA-Z\.\s&]+(?:Ltd\.|Limited|Corp\.)?\s+(?:v\.|vs\.|versus)\s+[A-Z][a-zA-Z\.\s&]+(?:\([^\)]+\))?)",
            r"(?i)\b\d{4}\s*\(\d+\)\s*SCC\s*\d+\b",
            r"(?i)\bAIR\s*\d{4}\s*SC\s*\d+\b",
        ]
        precedents = set()
        for pat in precedent_patterns:
            for m in re.finditer(pat, text):
                cand = m.group(0).strip()
                if len(cand) > 6 and "court" not in cand.lower():
                    precedents.add(cand)

        # 5. Standalone numerical claims: amounts, percentages, quantities, spans
        raw_numbers = set(re.findall(r"\b\d+(?:,\d+)*(?:\.\d+)?\b", text))
        pure_numbers = set()
        for n in raw_numbers:
            if len(n) <= 1:
                continue
            if n in years:
                continue
            if n in section_numbers_consumed:
                continue
            if n in paragraph_numbers_consumed:
                continue
            pure_numbers.add(n)

        return {
            "years": years,
            "sections": sections,
            "acts": {a.lower() for a in acts},
            "precedents": precedents,
            "numbers": pure_numbers,
            "section_numbers": section_numbers_consumed,
            "paragraph_numbers": paragraph_numbers_consumed,
        }

    def check_unsupported_claims(self, source_text: str, summary: str) -> list[dict[str, str]]:
        """Detect dates, sections, numbers, and precedents in the summary that do not exist in the source text."""
        source_entities = self._extract_specific_entities(source_text)
        summary_entities = self._extract_specific_entities(summary)

        unsupported: list[dict[str, str]] = []

        # 1. Check years
        for yr in sorted(summary_entities["years"]):
            if yr not in source_entities["years"] and not re.search(rf"\b{re.escape(yr)}\b", source_text):
                unsupported.append({
                    "type": "Year / Date",
                    "value": yr,
                    "risk": f"Year '{yr}' mentioned in summary does not appear in original case text.",
                })

        # 2. Check statutory sections / constitutional provisions with citation alias resolution
        for sec in sorted(summary_entities["sections"]):
            sec_lower = sec.lower()
            if sec_lower in source_entities["sections"]:
                continue

            sec_parts = sec_lower.split(maxsplit=1)
            if len(sec_parts) == 2:
                p_name, p_num = sec_parts
                # Alias expansion: e.g. "article" matches "art.", "article"
                # "section" matches "sec.", "section", "s."
                if p_name == "article":
                    alias_pat = r"(?:articles?|art\.?)"
                elif p_name == "section":
                    alias_pat = r"(?:sections?|sec\.?|s\.)"
                elif p_name == "clause":
                    alias_pat = r"(?:clauses?|cl\.?)"
                elif p_name == "rule":
                    alias_pat = r"(?:rules?|r\.?)"
                elif p_name == "order":
                    alias_pat = r"(?:orders?|o\.?)"
                else:
                    alias_pat = re.escape(p_name)

                # Strip sub-parentheses for base match: e.g. "63(c)" -> base "63"
                base_digit = re.search(r"^\d+(?:\.\d+)?", p_num)
                num_pat = re.escape(p_num)
                if base_digit:
                    base_str = base_digit.group(0)
                    pattern = rf"(?i)\b{alias_pat}\s*[\w\s,\(\)]*?\b{base_str}\b"
                else:
                    pattern = rf"(?i)\b{alias_pat}\s*[\w\s,\(\)]*?\b{num_pat}\b"

                if re.search(pattern, source_text):
                    continue

            unsupported.append({
                "type": "Statute / Provision",
                "value": sec.title(),
                "risk": f"Statutory provision '{sec.title()}' in summary is absent from source document.",
            })

        # 3. Check precedent case citations
        for prec in sorted(summary_entities["precedents"]):
            # Extract key identifying words (exclude common words like State, Union, India, v., vs.)
            prec_words = [
                w.lower() for w in re.findall(r"\b[A-Za-z]{4,}\b", prec)
                if w.lower() not in ["versus", "state", "union", "india", "court", "limited", "corporation"]
            ]
            if prec_words:
                matches_in_source = sum(1 for w in prec_words if re.search(rf"\b{re.escape(w)}\b", source_text, re.IGNORECASE))
                if matches_in_source >= 1:
                    continue
            elif prec in source_text:
                continue

            unsupported.append({
                "type": "Precedent / Citation",
                "value": prec,
                "risk": f"Precedent or citation '{prec}' in summary does not appear in source document.",
            })

        # 4. Check standalone numerical claims (percentages, amounts, durations, quantities)
        for num in sorted(summary_entities["numbers"]):
            if num in source_entities["numbers"]:
                continue
            if re.search(rf"\b{re.escape(num)}\b", source_text):
                continue
            unsupported.append({
                "type": "Number / Value",
                "value": num,
                "risk": f"Numerical claim '{num}' in summary does not match any numbers in source.",
            })

        return unsupported

    def calculate_coverage(
        self,
        summary: str,
        prior_analysis: dict[str, Any] | None = None,
        prior_reasoning: dict[str, Any] | None = None,
    ) -> tuple[float, list[str], list[str]]:
        """Evaluate summary coverage across the 5 foundational legal pillars:
        1. Legal Issue / Framing
        2. Parties & Procedural Context
        3. Court Decision & Operative Outcome
        4. Legal Reasoning & Ratio Decidendi
        5. Statutory Framework & Cited Law
        """
        summary_lower = summary.lower()
        candidates: dict[str, bool] = {}

        # Pillar 1: Legal Issue / Substantive Dispute
        issue_covered = False
        if prior_reasoning and prior_reasoning.get("questions_of_law"):
            for q in prior_reasoning["questions_of_law"]:
                q_toks = [t.lower() for t in re.findall(r"\b[A-Za-z]{4,}\b", q)]
                if q_toks and sum(1 for t in q_toks if t in summary_lower) >= 2:
                    issue_covered = True
                    break
        if not issue_covered and prior_analysis and prior_analysis.get("legal_claims"):
            for cl in prior_analysis["legal_claims"]:
                cl_toks = [t.lower() for t in re.findall(r"\b[A-Za-z]{4,}\b", cl)]
                if cl_toks and sum(1 for t in cl_toks if t in summary_lower) >= 2:
                    issue_covered = True
                    break
        if not issue_covered:
            issue_covered = bool(
                re.search(
                    r"(?i)\b(issue|question of law|whether|validity|dispute|failure to prove|challenge|execution of|termination|breach|maintainability)\b",
                    summary,
                )
            )
        candidates["Legal Issue / Dispute Framing"] = issue_covered

        # Pillar 2: Parties & Case Context
        parties_covered = False
        if prior_analysis:
            title = prior_analysis.get("case_title", "")
            if title and title not in ["Unknown Case", "Not stated in the document", "API Key Not Configured"]:
                title_toks = [t.lower() for t in re.findall(r"\b[A-Za-z]{4,}\b", title)]
                name_toks = [t for t in title_toks if t not in ["versus", "state", "union", "india", "court"]]
                if any(t in summary_lower for t in name_toks[:4]):
                    parties_covered = True
            pet = prior_analysis.get("petitioner", "")
            if not parties_covered and pet and pet not in ["Not Specified", "Not stated in the document", "API Key Not Configured"]:
                pet_toks = [t.lower() for t in re.findall(r"\b[A-Za-z]{4,}\b", pet)]
                if any(t in summary_lower for t in pet_toks[:3]):
                    parties_covered = True
        if not parties_covered:
            parties_covered = bool(
                re.search(
                    r"(?i)\b(appellant|petitioner|respondent|plaintiff|defendant|testator|attesting witness|propounder|executor|contractor|employer|authority)\b",
                    summary,
                )
            )
        candidates["Parties & Procedural Context"] = parties_covered

        # Pillar 3: Court Decision & Operative Outcome
        outcome_covered = False
        if prior_reasoning:
            holding = prior_reasoning.get("court_holding_and_disposition", "")
            if holding and holding not in ["Not Specified", "Not stated in the document", "API Key Not Configured"]:
                h_toks = [t.lower() for t in re.findall(r"\b[A-Za-z]{4,}\b", holding)]
                if any(t in summary_lower for t in h_toks[:5]):
                    outcome_covered = True
        if not outcome_covered:
            outcome_covered = bool(
                re.search(
                    r"(?i)\b(allowed|dismissed|quashed|set aside|decreed|affirmed|reversed|held that|ordered|disposed of|relief|verdict)\b",
                    summary,
                )
            )
        candidates["Court Decision & Operative Outcome"] = outcome_covered

        # Pillar 4: Legal Reasoning & Ratio Decidendi
        reasoning_covered = False
        if prior_reasoning:
            ratio = prior_reasoning.get("ratio_decidendi", "")
            if ratio and ratio not in ["Not Specified", "Not stated in the document", "Configure GEMINI_API_KEY in .env to perform live Gemini legal reasoning."]:
                ratio_tokens = [t.lower() for t in re.findall(r"\b[A-Za-z]{5,}\b", ratio)]
                overlap = sum(1 for tok in ratio_tokens if tok in summary_lower)
                if overlap >= 2 or (overlap / max(len(ratio_tokens), 1)) >= 0.12:
                    reasoning_covered = True
        if not reasoning_covered:
            reasoning_covered = bool(
                re.search(
                    r"(?i)\b(ratio decidendi|reasoning|principle|mandatory requirement|scope and effect|on the grounds that|held that|sine qua non|pre-condition)\b",
                    summary,
                )
            )
        candidates["Legal Reasoning & Ratio Decidendi"] = reasoning_covered

        # Pillar 5: Statutory Framework & Cited Law
        statute_covered = False
        if prior_analysis and prior_analysis.get("statutes_and_sections"):
            for st in prior_analysis["statutes_and_sections"]:
                st_toks = [t.lower() for t in re.findall(r"\b[A-Za-z0-9]{3,}\b", st)]
                if st_toks and any(t in summary_lower for t in st_toks if t not in ["act", "the", "and"]):
                    statute_covered = True
                    break
        if not statute_covered:
            statute_covered = bool(
                re.search(
                    r"(?i)\b(section|article|act|code|constitution|statute|clause|provision)\b",
                    summary,
                )
            )
        candidates["Statutory Framework & Cited Law"] = statute_covered

        covered = [name for name, present in candidates.items() if present]
        missing = [name for name, present in candidates.items() if not present]
        score = round(len(covered) / max(len(candidates), 1), 2)

        return score, covered, missing

    def calculate_consistency(self, source_text: str, summary: str) -> float:
        """Compute lexical overlap and sentence-level grounding score."""
        if not summary.strip() or not source_text.strip():
            return 0.0

        source_words = set(re.findall(r"\b[a-zA-Z]{4,}\b", source_text.lower()))
        summary_words = re.findall(r"\b[a-zA-Z]{4,}\b", summary.lower())

        if not summary_words:
            return 0.0

        grounded_count = sum(1 for w in summary_words if w in source_words)
        ratio = grounded_count / len(summary_words)
        # Scaled non-trivial consistency
        return round(min(max(ratio, 0.0), 1.0), 2)

    def validate(
        self,
        source_text: str,
        summary: str,
        prior_analysis: dict[str, Any] | None = None,
        prior_reasoning: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run full validation suite on candidate legal summary."""
        start_time = time.time()

        if not summary or not summary.strip():
            return {
                "status": "FAILED",
                "latency_seconds": 0.0,
                "data": ValidationReport(
                    overall_status="FAILED",
                    recommendations=["Summary is completely empty. Execution halted."],
                ).model_dump(),
                "error": "Summary text is empty.",
            }

        unsupported = self.check_unsupported_claims(source_text, summary)
        coverage_score, covered, missing = self.calculate_coverage(
            summary, prior_analysis, prior_reasoning
        )
        consistency_score = self.calculate_consistency(source_text, summary)

        recommendations: list[str] = []
        if unsupported:
            recommendations.append(
                f"Flagged {len(unsupported)} potentially unsupported claim(s) or hallucinated entities. Review highlighted items against source text."
            )
        if missing:
            recommendations.append(
                f"Summary omits key legal elements: {', '.join(missing)}. Consider expanding coverage to include these points."
            )
        if consistency_score < 0.70:
            recommendations.append(
                f"Lexical consistency ({int(consistency_score*100)}%) is below desired 70% threshold. Verify summary factual alignment."
            )

        # Determine overall validation grade
        if len(unsupported) > 2 or coverage_score < 0.35:
            overall_status = "FAILED"
        elif unsupported or missing or consistency_score < 0.75:
            overall_status = "WARNING"
        else:
            overall_status = "PASSED"
            recommendations.append("Summary demonstrates sound legal coverage, high factual grounding, and no unsupported claims detected.")

        report = ValidationReport(
            overall_status=overall_status,
            coverage_score=coverage_score,
            covered_elements=covered,
            missing_elements=missing,
            consistency_score=consistency_score,
            unsupported_claims=unsupported,
            unsupported_claims_count=len(unsupported),
            recommendations=recommendations,
        )

        latency = round(time.time() - start_time, 2)
        return {
            "status": "SUCCESS",
            "latency_seconds": latency,
            "data": report.model_dump(),
            "error": None,
        }
