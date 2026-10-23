"""Unit tests for ValidationAgent checking coverage, consistency, and unsupported claims."""

from agents.validator import ValidationAgent


def test_validation_passes_on_grounded_summary(
    sample_judgment_text: str, mock_document_analysis: dict, mock_legal_reasoning: dict
):
    """Test that a faithful, grounded summary passes validation."""
    agent = ValidationAgent()
    grounded_summary = (
        "In Bharat Infrastructure Limited v. State of Maharashtra, the Supreme Court of India "
        "considered Civil Appeal No. 4582 of 2021 regarding a highway construction contract terminated "
        "without a mandatory 30-day cure notice under Clause 14.2. The Court held under Article 14 and "
        "Article 226 that public authorities must follow procedural fairness. The appeal was allowed and "
        "the termination order was quashed."
    )

    result = agent.validate(
        source_text=sample_judgment_text,
        summary=grounded_summary,
        prior_analysis=mock_document_analysis,
        prior_reasoning=mock_legal_reasoning,
    )

    assert result["status"] == "SUCCESS"
    val = result["data"]
    assert val["overall_status"] in ["PASSED", "WARNING"]
    assert val["coverage_score"] >= 0.50
    assert val["consistency_score"] >= 0.70
    assert val["unsupported_claims_count"] == 0
    assert len(val["unsupported_claims"]) == 0


def test_detects_unsupported_dates_and_sections(sample_judgment_text: str):
    """Test that hallucinated dates, sections, and values are flagged."""
    agent = ValidationAgent()
    hallucinated_summary = (
        "In 2035, the Court invoked Section 498A and Article 370 to award Rs. 9999999 to the respondent. "
        "The judgment was delivered in 1845."
    )

    unsupported = agent.check_unsupported_claims(sample_judgment_text, hallucinated_summary)

    # Years 2035 and 1845 do not appear in source text
    unsupported_values = {u["value"].lower() for u in unsupported}
    assert "2035" in unsupported_values or "1845" in unsupported_values
    # Section 498A does not appear in the source judgment
    assert any("498a" in u["value"].lower() for u in unsupported)


def test_coverage_calculation(mock_document_analysis: dict, mock_legal_reasoning: dict):
    """Test coverage scoring when key elements are present vs absent."""
    agent = ValidationAgent()

    full_summary = (
        "Bharat Infrastructure Limited challenged termination of concession in Supreme Court of India. "
        "The appeal was allowed holding that state arbitrariness violates Article 14 and cure notices "
        "are mandatory under Article 226."
    )
    score_full, covered_full, missing_full = agent.calculate_coverage(
        full_summary, mock_document_analysis, mock_legal_reasoning
    )
    assert score_full >= 0.5
    assert len(covered_full) > len(missing_full)

    scant_summary = "A case was decided."
    score_scant, covered_scant, missing_scant = agent.calculate_coverage(
        scant_summary, mock_document_analysis, mock_legal_reasoning
    )
    assert score_scant < 0.3
    assert len(missing_scant) > len(covered_scant)


def test_consistency_calculation(sample_judgment_text: str):
    """Test consistency scoring for source-derived tokens vs foreign text."""
    agent = ValidationAgent()

    # Highly grounded snippet
    grounded = "The appellant was declared the successful bidder and a Concession Agreement was executed."
    score_grounded = agent.calculate_consistency(sample_judgment_text, grounded)
    assert score_grounded >= 0.80

    # Completely alien text
    alien = "Quantum thermodynamics and interstellar photon entanglement dictate galactic orbits."
    score_alien = agent.calculate_consistency(sample_judgment_text, alien)
    assert score_alien <= 0.20


def test_empty_summary_fails():
    """Test that an empty summary triggers validation failure."""
    agent = ValidationAgent()
    result = agent.validate(source_text="Some text", summary="")
    assert result["status"] == "FAILED"
    assert result["data"]["overall_status"] == "FAILED"


def test_compound_statutory_provisions_correctly_classified(sample_judgment_text: str):
    """Regression test: 'Articles 14 and 16' parses both provisions; absent Article 16 is flagged as Statute/Provision, not Number 16."""
    agent = ValidationAgent()
    # sample_judgment_text mentions Article 14 and Article 226, but NOT Article 16
    summary = "The Supreme Court considered Articles 14 and 16 alongside Section 71."

    unsupported = agent.check_unsupported_claims(sample_judgment_text, summary)

    # Article 16 must be flagged as a Statute / Provision, NEVER as Number / Value
    types = [u["type"] for u in unsupported]
    values = [u["value"].lower() for u in unsupported]

    assert "Number / Value" not in types or not any("16" == u["value"] for u in unsupported if u["type"] == "Number / Value")
    assert any("article 16" in v for v in values)
    assert any(u["type"] == "Statute / Provision" and "16" in u["value"] for u in unsupported)


def test_paragraph_citations_not_flagged_as_numbers(sample_judgment_text: str):
    """Regression test: internal judgment paragraph citations [Paras 7 and 8], Para 11 are not flagged as generic measurement numbers."""
    agent = ValidationAgent()
    summary = (
        "The High Court examined the Concession Agreement under Clause 14.2. "
        "The Court agreed with the findings [Paras 7 and 8] and confirmed the order in Para 11."
    )

    unsupported = agent.check_unsupported_claims(sample_judgment_text, summary)

    # Paragraph markers 7, 8, 11 should not be flagged as arbitrary numbers
    flagged_numbers = [u["value"] for u in unsupported if u["type"] == "Number / Value"]
    assert "7" not in flagged_numbers
    assert "8" not in flagged_numbers
    assert "11" not in flagged_numbers


def test_unsupported_standalone_number_flagged_with_word_boundary(sample_judgment_text: str):
    """Regression test: genuinely unsupported numbers are accurately flagged using strict word boundaries."""
    agent = ValidationAgent()
    # sample_judgment_text has 18 months, 36 months, but NOT 99 months
    summary = "The concession agreement required completion within 99 months."

    unsupported = agent.check_unsupported_claims(sample_judgment_text, summary)

    flagged = [u for u in unsupported if u["type"] == "Number / Value" and u["value"] == "99"]
    assert len(flagged) == 1
    assert "Numerical claim '99'" in flagged[0]["risk"]


def test_five_pillar_coverage_evaluation(mock_document_analysis: dict, mock_legal_reasoning: dict):
    """Regression test: coverage evaluates all 5 pillars: Issue, Parties, Outcome, Ratio, and Statutes."""
    agent = ValidationAgent()

    complete_summary = (
        "In Bharat Infrastructure Limited v. State of Maharashtra, the Supreme Court of India "
        "framed the question of law regarding the validity of contract termination without a cure notice. "
        "Under Article 14 and Article 226, the Court established the ratio decidendi that public authorities "
        "must afford procedural fairness. The appeal was allowed and the termination order was quashed."
    )

    score, covered, missing = agent.calculate_coverage(
        complete_summary, mock_document_analysis, mock_legal_reasoning
    )

    # All 5 pillars should be recognized
    assert score == 1.0
    assert len(covered) == 5
    assert len(missing) == 0
    assert "Legal Issue / Dispute Framing" in covered
    assert "Parties & Procedural Context" in covered
    assert "Court Decision & Operative Outcome" in covered
    assert "Legal Reasoning & Ratio Decidendi" in covered
    assert "Statutory Framework & Cited Law" in covered
