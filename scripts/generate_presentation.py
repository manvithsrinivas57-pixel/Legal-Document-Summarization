#!/usr/bin/env python3
"""
generate_presentation.py
Generates a professional 12-slide PowerPoint presentation (.pptx) for:
'Legal Document Summarization: A Zero-Shot Modular Agentic Workflow Approach'

Features:
- 16:9 Widescreen (13.333 x 7.5 inches)
- Professional dark navy, teal, and cyan palette
- Authentic project metrics, hardware specs, and dataset provenance
- Real screenshots embedded from screenshots/
- Comprehensive verbatim speaker notes on every slide
- Saves to presentation/legal_document_summarization_presentation.pptx
"""

import os
import sys
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# -----------------------------------------------------------------------------
# CONSTANTS & COLOR PALETTE
# -----------------------------------------------------------------------------
SLIDE_WIDTH = Inches(13.333)
SLIDE_HEIGHT = Inches(7.5)

# Modern Dark Navy & Cyan/Teal Palette
BG_DARK = RGBColor(11, 19, 43)          # #0B132B Deep Midnight Navy
CARD_BG = RGBColor(22, 33, 62)          # #16213E Dark Slate Blue Card
CARD_BORDER = RGBColor(46, 64, 102)     # #2E4066 Card Border Stroke
HEADER_BG = RGBColor(15, 23, 42)        # #0F172A Very Dark Slate
CARD_ACCENT_BG = RGBColor(18, 40, 70)   # #122846 Highlight Card Fill

ACCENT_CYAN = RGBColor(56, 189, 248)    # #38BDF8 Sky Cyan
ACCENT_TEAL = RGBColor(45, 212, 191)    # #2DD4BF Bright Teal
ACCENT_GOLD = RGBColor(245, 158, 11)    # #F59E0B Amber / Warning
ACCENT_EMERALD = RGBColor(16, 185, 129) # #10B981 Success Emerald
ACCENT_PURPLE = RGBColor(168, 85, 247)  # #A855F7 Purple Accent

TEXT_WHITE = RGBColor(248, 250, 252)    # #F8FAFC Pure Crisp White
TEXT_LIGHT = RGBColor(226, 232, 240)    # #E2E8F0 Off-White Light Gray
TEXT_MUTED = RGBColor(148, 163, 184)    # #94A3B8 Slate 400 Muted Text

BASE_DIR = Path(__file__).resolve().parent.parent
SCREENSHOTS_DIR = BASE_DIR / "screenshots"
OUTPUT_DIR = BASE_DIR / "presentation"
OUTPUT_FILE = OUTPUT_DIR / "legal_document_summarization_presentation.pptx"


# -----------------------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------------------
def create_base_slide(prs, category: str, title: str, subtitle: str, slide_num: int):
    """Creates a slide with consistent dark background, header hierarchy, and footer."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout

    # Base dark background
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_WIDTH, SLIDE_HEIGHT)
    bg.fill.solid()
    bg.fill.fore_color.rgb = BG_DARK
    bg.line.fill.background()

    # Top glowing decorative rule
    rule = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_WIDTH, Inches(0.08))
    rule.fill.solid()
    rule.fill.fore_color.rgb = ACCENT_CYAN
    rule.line.fill.background()

    # Slide Header Text Box
    header_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.733), Inches(1.3))
    tf = header_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    # Paragraph 1: Category Tag
    p_cat = tf.paragraphs[0]
    p_cat.text = category.upper()
    p_cat.font.name = "Segoe UI"
    p_cat.font.size = Pt(10)
    p_cat.font.bold = True
    p_cat.font.color.rgb = ACCENT_CYAN
    p_cat.space_after = Pt(2)

    # Paragraph 2: Slide Title
    p_title = tf.add_paragraph()
    p_title.text = title
    p_title.font.name = "Segoe UI"
    p_title.font.size = Pt(22)
    p_title.font.bold = True
    p_title.font.color.rgb = TEXT_WHITE
    p_title.space_after = Pt(2)

    # Paragraph 3: Subtitle
    if subtitle:
        p_sub = tf.add_paragraph()
        p_sub.text = subtitle
        p_sub.font.name = "Segoe UI"
        p_sub.font.size = Pt(11)
        p_sub.font.color.rgb = TEXT_MUTED

    # Footer elements
    footer_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.0), Inches(11.733), Inches(0.35))
    ftf = footer_box.text_frame
    ftf.word_wrap = True
    ftf.margin_left = ftf.margin_top = ftf.margin_right = ftf.margin_bottom = 0
    fp = ftf.paragraphs[0]
    fp.text = "Legal Document Summarization: A Zero-Shot Modular Agentic Workflow Approach"
    fp.font.name = "Segoe UI"
    fp.font.size = Pt(9)
    fp.font.color.rgb = RGBColor(100, 116, 139)

    # Slide Number
    num_box = slide.shapes.add_textbox(Inches(11.5), Inches(7.0), Inches(1.0), Inches(0.35))
    ntf = num_box.text_frame
    ntf.margin_left = ntf.margin_top = ntf.margin_right = ntf.margin_bottom = 0
    np = ntf.paragraphs[0]
    np.text = f"{slide_num:02d} / 12"
    np.alignment = PP_ALIGN.RIGHT
    np.font.name = "Segoe UI"
    np.font.size = Pt(9)
    np.font.bold = True
    np.font.color.rgb = ACCENT_TEAL

    return slide


def add_card(slide, left, top, width, height, bg_color=CARD_BG, border_color=CARD_BORDER, border_width=1.5):
    """Draws a rounded rectangular surface card with border styling."""
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_color
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = Pt(border_width)
    else:
        shape.line.fill.background()
    return shape


def add_metric_card(slide, left, top, width, height, value_text, label_text, subtext="", accent_color=ACCENT_CYAN):
    """Creates a prominent metric/KPI card with bold number and label."""
    card = add_card(slide, left, top, width, height, bg_color=CARD_BG, border_color=CARD_BORDER)
    
    # Accent mini bar on top of the card
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left + Inches(0.15), top + Inches(0.15), width - Inches(0.3), Inches(0.04))
    bar.fill.solid()
    bar.fill.fore_color.rgb = accent_color
    bar.line.fill.background()

    tf = card.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = Inches(0.2)
    tf.margin_right = Inches(0.2)
    tf.margin_top = Inches(0.1)

    p_val = tf.paragraphs[0]
    p_val.text = value_text
    p_val.font.name = "Segoe UI"
    p_val.font.size = Pt(28)
    p_val.font.bold = True
    p_val.font.color.rgb = accent_color
    p_val.alignment = PP_ALIGN.CENTER

    p_lbl = tf.add_paragraph()
    p_lbl.text = label_text
    p_lbl.font.name = "Segoe UI"
    p_lbl.font.size = Pt(11)
    p_lbl.font.bold = True
    p_lbl.font.color.rgb = TEXT_WHITE
    p_lbl.alignment = PP_ALIGN.CENTER

    if subtext:
        p_sub = tf.add_paragraph()
        p_sub.text = subtext
        p_sub.font.name = "Segoe UI"
        p_sub.font.size = Pt(9)
        p_sub.font.color.rgb = TEXT_MUTED
        p_sub.alignment = PP_ALIGN.CENTER

    return card


def add_badge(slide, left, top, width, height, text, bg_color, text_color=TEXT_WHITE):
    """Draws a compact pill badge with centered label."""
    badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    badge.fill.solid()
    badge.fill.fore_color.rgb = bg_color
    badge.line.fill.background()
    tf = badge.text_frame
    tf.word_wrap = False
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = text
    p.font.name = "Segoe UI"
    p.font.size = Pt(9)
    p.font.bold = True
    p.font.color.rgb = text_color
    p.alignment = PP_ALIGN.CENTER
    return badge


def set_speaker_notes(slide, notes_text: str):
    """Sets clean verbatim speaker notes for the slide."""
    slide.notes_slide.notes_text_frame.text = notes_text.strip()


# -----------------------------------------------------------------------------
# SLIDE BUILDERS (12 SLIDES)
# -----------------------------------------------------------------------------

def build_slide_01_title(prs):
    """Slide 1: Title Slide."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    # Deep Navy background
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_WIDTH, SLIDE_HEIGHT)
    bg.fill.solid()
    bg.fill.fore_color.rgb = BG_DARK
    bg.line.fill.background()

    # Top accent cyan glow bar
    rule = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_WIDTH, Inches(0.12))
    rule.fill.solid()
    rule.fill.fore_color.rgb = ACCENT_CYAN
    rule.line.fill.background()

    # Main Hero Container Card
    hero = add_card(slide, Inches(1.0), Inches(1.1), Inches(11.333), Inches(5.3), bg_color=CARD_BG, border_color=CARD_BORDER, border_width=2.0)

    # Hero Card Inner Glow Rule
    inner_rule = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.5), Inches(1.5), Inches(10.333), Inches(0.04))
    inner_rule.fill.solid()
    inner_rule.fill.fore_color.rgb = ACCENT_TEAL
    inner_rule.line.fill.background()

    # Title & Subtitle Text Box
    tbox = slide.shapes.add_textbox(Inches(1.5), Inches(1.8), Inches(10.333), Inches(2.6))
    tf = tbox.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    p_badge = tf.paragraphs[0]
    p_badge.text = "ACADEMIC CAPSTONE DEFENSE  |  LEGAL NLP & AGENTIC AI"
    p_badge.font.name = "Segoe UI"
    p_badge.font.size = Pt(11)
    p_badge.font.bold = True
    p_badge.font.color.rgb = ACCENT_CYAN
    p_badge.space_after = Pt(12)

    p_title = tf.add_paragraph()
    p_title.text = "Legal Document Summarization:\nA Zero-Shot Modular Agentic Workflow Approach"
    p_title.font.name = "Segoe UI"
    p_title.font.size = Pt(30)
    p_title.font.bold = True
    p_title.font.color.rgb = TEXT_WHITE
    p_title.space_after = Pt(12)

    p_sub = tf.add_paragraph()
    p_sub.text = "Fusing Supervised Neural Abstractive Transformers (BART) with Orchestrated Agentic LLM Reasoning (Gemini & LangGraph) on Indian Supreme Court & High Court Judgments"
    p_sub.font.name = "Segoe UI"
    p_sub.font.size = Pt(13)
    p_sub.font.color.rgb = TEXT_LIGHT

    # 4 Pillar Badges
    badges = [
        ("CivilSum Benchmark (SIGIR '24)", ACCENT_TEAL),
        ("BART Fine-Tuned (RTX 4060 GPU)", ACCENT_CYAN),
        ("LangGraph Multi-Agent DAG", ACCENT_PURPLE),
        ("Deterministic Grounding Auditor", ACCENT_EMERALD)
    ]
    bx = Inches(1.5)
    by = Inches(4.7)
    for text, color in badges:
        add_badge(slide, bx, by, Inches(2.4), Inches(0.36), text, bg_color=RGBColor(15, 23, 42), text_color=color)
        bx += Inches(2.55)

    # Footer Metadata Card
    fcard = add_card(slide, Inches(1.5), Inches(5.3), Inches(10.333), Inches(0.85), bg_color=RGBColor(15, 23, 42), border_color=CARD_BORDER, border_width=1.0)
    ftf = fcard.text_frame
    ftf.vertical_anchor = MSO_ANCHOR.MIDDLE
    ftf.word_wrap = True
    ftf.margin_left = Inches(0.3)
    ftf.margin_right = Inches(0.3)
    fp = ftf.paragraphs[0]
    fp.text = "Project Architecture: 5-Stage Agentic Pipeline  •  Execution Checkpoint: models/checkpoints/civilsum_bart (225 Steps, Val Loss 2.306)  •  Automated Test Suite: 60/60 Tests Passing (100%)"
    fp.font.name = "Segoe UI"
    fp.font.size = Pt(10)
    fp.font.color.rgb = TEXT_MUTED

    set_speaker_notes(slide, """
Good morning, respected members of the committee, faculty, and colleagues.

Today, I am proud to present our project: "Legal Document Summarization: A Zero-Shot Modular Agentic Workflow Approach."

This project addresses one of the most critical frontiers in Natural Language Processing: automated summarization of judicial decisions. Modern legal judgments in common-law systems—particularly the Supreme Court of India and High Courts—frequently span 20 to 50 pages of dense, archaic prose and procedural transcripts.

While monolithic Large Language Models often suffer from catastrophic hallucinations, omission of binding judicial holding, or sequence length truncations, our architecture introduces a hybrid, verified assembly line. We combine locally fine-tuned sequence-to-sequence transformers—specifically facebook/bart-base trained on the SIGIR 2024 CivilSum benchmark—with zero-shot agentic reasoning powered by Google Gemini, all orchestrated through a stateful LangGraph Directed Acyclic Graph.

Over the next 11 slides, I will walk you through the structural challenges of legal text, our tail-aware algorithm, model training convergence on our local RTX 4060 GPU, empirical ROUGE results, our 60-test verification suite, and live application workflows.
""")


def build_slide_02_problem(prs):
    """Slide 2: Problem Statement."""
    slide = create_base_slide(
        prs,
        category="DOMAIN CHALLENGES  |  THE CRISIS OF LEGAL TEXT COMPLEXITY",
        title="Why Legal Summarization Breaks Standard NLP",
        subtitle="Indian judicial decisions introduce unique topological and factual hazards that cause monolithic LLMs to fail.",
        slide_num=2
    )

    card_width = Inches(3.64)
    card_height = Inches(4.8)
    card_y = Inches(1.9)

    # Card 1: Length & Structure
    c1 = add_card(slide, Inches(0.8), card_y, card_width, card_height)
    tf1 = c1.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_right = tf1.margin_top = Inches(0.25)

    add_badge(slide, Inches(1.05), card_y + Inches(0.25), Inches(1.8), Inches(0.3), "CHALLENGE 1", ACCENT_CYAN, RGBColor(10, 17, 40))
    p1 = tf1.paragraphs[0]
    p1.text = "\n\nExtreme Document Length & Structural Noise"
    p1.font.name = "Segoe UI"
    p1.font.size = Pt(15)
    p1.font.bold = True
    p1.font.color.rgb = TEXT_WHITE
    p1.space_after = Pt(10)

    bullets1 = [
        "20 to 50+ Pages per Judgment: Indian rulings aggregate trial transcripts, witness depositions, and procedural appeals.",
        "Archaic Lexicon: Heavy usage of Latin maxims (ratio decidendi, obiter dicta, res judicata) and cross-statutory citations.",
        "Context Window Choke: Standard neural attention windows (512–1,024 tokens) truncate over 80% of substantive judgments.",
        "Monolithic Failure: Blind truncation discards critical legal nuances before analysis even begins."
    ]
    for b in bullets1:
        p = tf1.add_paragraph()
        p.text = f"•  {b}"
        p.font.name = "Segoe UI"
        p.font.size = Pt(10)
        p.font.color.rgb = TEXT_LIGHT
        p.space_after = Pt(8)

    # Card 2: Severe Tail Bias
    c2 = add_card(slide, Inches(4.84), card_y, card_width, card_height, bg_color=CARD_ACCENT_BG, border_color=ACCENT_TEAL, border_width=2.0)
    tf2 = c2.text_frame
    tf2.word_wrap = True
    tf2.margin_left = tf2.margin_right = tf2.margin_top = Inches(0.25)

    add_badge(slide, Inches(5.09), card_y + Inches(0.25), Inches(2.2), Inches(0.3), "THE CORE HAZARD", ACCENT_TEAL, RGBColor(10, 17, 40))
    p2 = tf2.paragraphs[0]
    p2.text = "\n\nSevere 'Tail Bias' (Non-Linear Topology)"
    p2.font.name = "Segoe UI"
    p2.font.size = Pt(15)
    p2.font.bold = True
    p2.font.color.rgb = ACCENT_TEAL
    p2.space_after = Pt(10)

    bullets2 = [
        "The Lead-Bias Inversion: News articles place key facts in paragraph 1 (lead bias). Indian court judgments exhibit extreme tail bias.",
        "Opening 70%: Formal captions, procedural trial court history, arguments of petitioner and respondent.",
        "Final 30% (The Tail): Contains the judge's actual reasoning (Ratio Decidendi) and the operative verdict.",
        "The Truncation Catastrophe: Standard front-truncation captures the procedural lawsuit while deleting the actual ruling ('Appeal Dismissed')!"
    ]
    for b in bullets2:
        p = tf2.add_paragraph()
        p.text = f"•  {b}"
        p.font.name = "Segoe UI"
        p.font.size = Pt(10)
        p.font.color.rgb = TEXT_LIGHT
        p.space_after = Pt(8)

    # Card 3: Inversion & Hallucination
    c3 = add_card(slide, Inches(8.88), card_y, card_width, card_height)
    tf3 = c3.text_frame
    tf3.word_wrap = True
    tf3.margin_left = tf3.margin_right = tf3.margin_top = Inches(0.25)

    add_badge(slide, Inches(9.13), card_y + Inches(0.25), Inches(1.8), Inches(0.3), "LEGAL INTEGRITY", ACCENT_GOLD, RGBColor(10, 17, 40))
    p3 = tf3.paragraphs[0]
    p3.text = "\n\nInversion Risk & Statutory Hallucination"
    p3.font.name = "Segoe UI"
    p3.font.size = Pt(15)
    p3.font.bold = True
    p3.font.color.rgb = TEXT_WHITE
    p3.space_after = Pt(10)

    bullets3 = [
        "Zero Error Tolerance: In news summarization, 90% accuracy is satisfactory. In law, missing a single negation ('allow' vs 'dismiss') completely inverts justice.",
        "The Inversion Hazard: A summary declaring an appeal 'allowed' when the court upheld dismissal destroys legal reliance and misguides litigators.",
        "Statutory Hallucination: Generic LLMs fabricate statutory provisions (e.g., citing Section 10 instead of Section 9 of the CPC).",
        "Requirement: A deterministic validation gate that checks citations against ground truth before output."
    ]
    for b in bullets3:
        p = tf3.add_paragraph()
        p.text = f"•  {b}"
        p.font.name = "Segoe UI"
        p.font.size = Pt(10)
        p.font.color.rgb = TEXT_LIGHT
        p.space_after = Pt(8)

    set_speaker_notes(slide, """
Slide 2 outlines the fundamental problem: why off-the-shelf summarization fails on judicial judgments.

In standard NLP benchmarks like CNN/DailyMail, models benefit from what is known as 'lead bias'—the critical inverted-pyramid style of journalism where who, what, when, and where appear in the first two sentences.

Judicial decisions are the exact opposite. Indian court rulings exhibit severe 'tail bias.' The first 15 to 30 pages are spent reciting lower court appeal history, witness statements, and procedural motions. The judge's binding legal principle—the ratio decidendi—and the operative disposition—such as 'Appeal is dismissed with costs'—occur exclusively in the final paragraphs.

If an engineer applies standard front-truncation, the model consumes the entire 1,024-token budget on introductory procedural arguments and completely omits the actual court ruling!

Furthermore, the legal domain carries an unacceptable 'inversion hazard.' If an AI model flips a negation or confuses an argument for a ruling, it can falsely summarize that an appeal was allowed when it was dismissed. Moreover, unconstrained LLMs frequently hallucinate adjacent statutory sections. These hazards motivated our modular architecture.
""")


def build_slide_03_objectives(prs):
    """Slide 3: Objectives and Scope."""
    slide = create_base_slide(
        prs,
        category="SYSTEM DESIGN  |  ARCHITECTURAL SCOPE & BOUNDARIES",
        title="Project Objectives & Architectural Scope",
        subtitle="Decomposing legal summarization into a verified multi-agent assembly line with strict verification gates.",
        slide_num=3
    )

    card_width = Inches(5.67)
    card_height = Inches(4.8)
    card_y = Inches(1.9)

    # Left Card: Objectives
    c_left = add_card(slide, Inches(0.8), card_y, card_width, card_height)
    tfl = c_left.text_frame
    tfl.word_wrap = True
    tfl.margin_left = tfl.margin_right = tfl.margin_top = Inches(0.3)

    add_badge(slide, Inches(1.1), card_y + Inches(0.3), Inches(2.2), Inches(0.32), "CORE OBJECTIVES", ACCENT_CYAN, RGBColor(10, 17, 40))
    pl = tfl.paragraphs[0]
    pl.text = "\n\nKey Research & Engineering Goals"
    pl.font.name = "Segoe UI"
    pl.font.size = Pt(16)
    pl.font.bold = True
    pl.font.color.rgb = TEXT_WHITE
    pl.space_after = Pt(12)

    objs = [
        ("Modular Agentic Pipeline", "Deconstruct summarization into 5 isolated nodes (Extraction, Metadata Analysis, Legal Reasoning, Abstractive Summary, and Grounding Validation) orchestrated via LangGraph."),
        ("Overcoming Tail Bias", "Engineer an 800-word 30/70 lead/tail dynamic trimming heuristic to guarantee capture of both jurisdictional context and the final operative disposition."),
        ("Hybrid Edge-Cloud Synergy", "Deploy locally fine-tuned facebook/bart-base for fast, private neural summarization, combined with cloud LLMs (Gemini) for zero-shot jurisprudential doctrine extraction."),
        ("Deterministic Fact-Checking", "Build a regex and entity-based validation auditor that scores statutory fidelity and flags conflicting dispositions before output release.")
    ]
    for title_txt, desc_txt in objs:
        p = tfl.add_paragraph()
        p.text = f"✔  {title_txt}: "
        p.font.name = "Segoe UI"
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = ACCENT_TEAL
        
        # Add normal text
        run = p.add_run()
        run.text = desc_txt
        run.font.bold = False
        run.font.color.rgb = TEXT_LIGHT
        p.space_after = Pt(10)

    # Right Card: Scope & Boundaries
    c_right = add_card(slide, Inches(6.86), card_y, card_width, card_height)
    tfr = c_right.text_frame
    tfr.word_wrap = True
    tfr.margin_left = tfr.margin_right = tfr.margin_top = Inches(0.3)

    add_badge(slide, Inches(7.16), card_y + Inches(0.3), Inches(2.4), Inches(0.32), "DOMAIN & BOUNDARIES", ACCENT_PURPLE, RGBColor(10, 17, 40))
    pr = tfr.paragraphs[0]
    pr.text = "\n\nTarget Scope & Non-Goals"
    pr.font.name = "Segoe UI"
    pr.font.size = Pt(16)
    pr.font.bold = True
    pr.font.color.rgb = TEXT_WHITE
    pr.space_after = Pt(12)

    scopes = [
        ("Jurisdiction Focus", "Trained and benchmarked exclusively on the official CivilSum dataset (Supreme Court of India and Indian High Courts civil decisions)."),
        ("Hardware Feasibility", "Engineered to train and run inference locally on consumer-grade GPU hardware (NVIDIA GeForce RTX 4060 Laptop GPU, 8GB VRAM)."),
        ("Fault-Tolerant Resilience", "Equipped with exponential backoff and storm-prevention logic against transient HTTP 503 API downtime, ensuring complete offline-capable summarization."),
        ("Transparent Auditability", "Every execution emits an immutable JSON audit log recording intermediate inputs, token latencies, and validation metrics."),
        ("Ethical Boundary", "Designed strictly as an analytical assistive co-pilot for legal researchers; explicitly not a substitute for formal judicial counsel.")
    ]
    for title_txt, desc_txt in scopes:
        p = tfr.add_paragraph()
        p.text = f"•  {title_txt}: "
        p.font.name = "Segoe UI"
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = ACCENT_CYAN
        
        run = p.add_run()
        run.text = desc_txt
        run.font.bold = False
        run.font.color.rgb = TEXT_LIGHT
        p.space_after = Pt(8)

    set_speaker_notes(slide, """
On Slide 3, we define the concrete objectives and boundary conditions of our project.

Our primary objective was to replace the standard 'black box prompt' approach with an audited, five-stage assembly line. In our pipeline, no single model is forced to perform everything. The PDF text extractor handles normalization; Gemini performs zero-shot structured metadata extraction; a second Gemini agent extracts the legal questions and ratio decidendi; our fine-tuned BART model generates the concise abstractive headnote; and finally, a deterministic validator checks citations and flags contradictions.

In terms of scope:
First, we ground our work in Indian civil jurisprudence, utilizing the peer-reviewed CivilSum dataset from SIGIR 2024.
Second, we enforced strict consumer hardware feasibility: our fine-tuned weights run on an 8GB RTX 4060 GPU without requiring enterprise clusters.
Third, we built in enterprise fault-tolerance: our system gracefully handles cloud API 503 outages without losing local functionality.
Finally, we state clearly that this tool is an assistive research workbench, not an autonomous legal entity.
""")


def build_slide_04_architecture(prs):
    """Slide 4: System Architecture Diagram."""
    slide = create_base_slide(
        prs,
        category="WORKFLOW TOPOLOGY  |  STATEFUL MULTI-AGENT DAG",
        title="End-to-End Modular Agentic Workflow",
        subtitle="Orchestrated by LangGraph with typed state contracts, validation gates, and immutable audit logging.",
        slide_num=4
    )

    # 5 Horizontal Nodes
    node_w = Inches(2.18)
    node_h = Inches(3.2)
    node_y = Inches(1.9)
    gap = Inches(0.2)
    start_x = Inches(0.8)

    stages = [
        ("STAGE 1", "PDF Extractor\nNode", "PyPDF + Regex", "• Strips headers & line noise\n• Normalizes citations\n• Validates input text integrity\n• Emits clean document stream", ACCENT_CYAN),
        ("STAGE 2", "Document Analysis\nAgent", "Gemini 2.5 Flash", "• Zero-shot JSON extraction\n• Case Title & Jurisdiction\n• Petitioner & Respondent\n• Bench & Involved Statutes", ACCENT_TEAL),
        ("STAGE 3", "Legal Reasoner\nAgent", "Gemini 2.5 Flash", "• Questions of Law identified\n• Substantive Legal Arguments\n• Ratio Decidendi extracted\n• Operative Court Disposition", ACCENT_PURPLE),
        ("STAGE 4", "Supervised Neural\nSummarizer", "Fine-Tuned BART", "• 30/70 Tail-Aware window\n• CUDA-accelerated inference\n• Beam search text generation\n• Headnote abstractive summary", ACCENT_GOLD),
        ("STAGE 5", "Validation Auditor\nAgent", "Deterministic Auditor", "• Statutory regex check\n• Factual consistency score\n• Disposition match audit\n• Anti-inversion gatekeeper", ACCENT_EMERALD)
    ]

    for i, (stg_num, stg_name, tech, details, color) in enumerate(stages):
        x = start_x + i * (node_w + gap)
        card = add_card(slide, x, node_y, node_w, node_h, bg_color=CARD_BG, border_color=color, border_width=1.8)
        
        # Mini colored bar at top of card
        top_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x + Inches(0.1), node_y + Inches(0.1), node_w - Inches(0.2), Inches(0.04))
        top_bar.fill.solid()
        top_bar.fill.fore_color.rgb = color
        top_bar.line.fill.background()

        tf = card.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = Inches(0.15)
        tf.margin_top = Inches(0.18)

        # Stage number badge
        p0 = tf.paragraphs[0]
        p0.text = stg_num
        p0.font.name = "Segoe UI"
        p0.font.size = Pt(8.5)
        p0.font.bold = True
        p0.font.color.rgb = color
        p0.space_after = Pt(2)

        p1 = tf.add_paragraph()
        p1.text = stg_name
        p1.font.name = "Segoe UI"
        p1.font.size = Pt(11)
        p1.font.bold = True
        p1.font.color.rgb = TEXT_WHITE
        p1.space_after = Pt(2)

        p2 = tf.add_paragraph()
        p2.text = f"Tech: {tech}"
        p2.font.name = "Segoe UI"
        p2.font.size = Pt(8.5)
        p2.font.bold = True
        p2.font.color.rgb = ACCENT_CYAN
        p2.space_after = Pt(6)

        p3 = tf.add_paragraph()
        p3.text = details
        p3.font.name = "Segoe UI"
        p3.font.size = Pt(8.5)
        p3.font.color.rgb = TEXT_LIGHT

    # Flow arrows between cards
    for i in range(4):
        arrow_x = start_x + (i + 1) * node_w + i * gap + Inches(0.02)
        arrow_box = slide.shapes.add_textbox(arrow_x, node_y + Inches(1.3), gap, Inches(0.5))
        atf = arrow_box.text_frame
        atf.margin_left = atf.margin_right = atf.margin_top = atf.margin_bottom = 0
        ap = atf.paragraphs[0]
        ap.text = "➔"
        ap.alignment = PP_ALIGN.CENTER
        ap.font.name = "Segoe UI"
        ap.font.size = Pt(14)
        ap.font.bold = True
        ap.font.color.rgb = ACCENT_CYAN

    # Bottom State Banner Card
    bot_card = add_card(slide, Inches(0.8), Inches(5.3), Inches(11.733), Inches(1.4), bg_color=CARD_ACCENT_BG, border_color=CARD_BORDER, border_width=1.5)
    btf = bot_card.text_frame
    btf.word_wrap = True
    btf.margin_left = Inches(0.3)
    btf.margin_right = Inches(0.3)
    btf.margin_top = Inches(0.18)

    bp0 = btf.paragraphs[0]
    bp0.text = "LANGGRAPH TYPED STATE MANAGEMENT & IMMUTABLE AUDIT TRAIL"
    bp0.font.name = "Segoe UI"
    bp0.font.size = Pt(10)
    bp0.font.bold = True
    bp0.font.color.rgb = ACCENT_CYAN
    bp0.space_after = Pt(4)

    bp1 = btf.add_paragraph()
    bp1.text = "• LegalWorkflowState Schema: Fully typed state dictionary passing normalized document text, extracted JSON metadata, jurisprudential reasoning dicts, neural summary strings, validation scores, and execution errors."
    bp1.font.name = "Segoe UI"
    bp1.font.size = Pt(9.5)
    bp1.font.color.rgb = TEXT_WHITE
    bp1.space_after = Pt(3)

    bp2 = btf.add_paragraph()
    bp2.text = "• Decoupled Resilience: Cloud LLM failures (HTTP 503) trigger up to 3 exponential backoff attempts (2s, 4s, 8s). If cloud access fails, local BART abstractive summary continues uninterrupted without crashing the pipeline."
    bp2.font.name = "Segoe UI"
    bp2.font.size = Pt(9.5)
    bp2.font.color.rgb = ACCENT_TEAL

    set_speaker_notes(slide, """
Slide 4 illustrates our end-to-end multi-agent architecture as implemented in LangGraph.

Notice the five sequential stages across the screen:
Stage 1 is the PDF Extractor. It ingests raw court documents, strips running court headers and watermarks, and cleans up irregular whitespace.

Stage 2 is the Document Analysis Agent. It invokes Google Gemini with strict JSON schema constraints to isolate metadata: case title, court jurisdiction, bench composition, petitioner, respondent, and the acts involved.

Stage 3 is the Legal Reasoner Agent. This agent performs the heavy jurisprudential heavy lifting. It identifies the formal Questions of Law, summarizes the competing contentions, extracts the judge's Ratio Decidendi, and records the final disposition.

Stage 4 is our local Supervised Neural Summarizer. It applies our 30/70 tail-aware windowing algorithm and passes the consolidated text into our fine-tuned facebook/bart-base model running locally on CUDA.

Finally, Stage 5 is our Validation Auditor. Rather than relying on another LLM that might also hallucinate, Stage 5 is a deterministic, rule-based program that parses cited statutory sections with regex, validates them against the source text, and checks for disposition concordance.

All data flows through a strongly typed LegalWorkflowState dictionary, ensuring every stage is recorded in an immutable audit trail.
""")


def build_slide_05_tech_stack(prs):
    """Slide 5: Technology Stack."""
    slide = create_base_slide(
        prs,
        category="ENGINEERING FOUNDATION  |  HIGH-PERFORMANCE TOOLCHAIN",
        title="Technology Stack & Environment Architecture",
        subtitle="Modern, type-safe, and GPU-accelerated technologies chosen for production reliability.",
        slide_num=5
    )

    card_w = Inches(2.78)
    card_h = Inches(4.8)
    card_y = Inches(1.9)
    gap = Inches(0.2)
    start_x = Inches(0.8)

    stacks = [
        ("AGENTIC ORCHESTRATION", ACCENT_CYAN, [
            ("LangGraph", "Stateful Directed Acyclic Graph (DAG) managing multi-agent state transitions."),
            ("Google GenAI SDK (v2.28.0)", "Official modern SDK accessing gemini-2.5-flash for high-speed legal reasoning."),
            ("Tenacity Backoff", "Exponential retry with random jitter (2s, 4s, 8s) for robust HTTP 503 fault tolerance."),
            ("Pydantic & Typing", "Enforces strict JSON schema contracts across all agent interfaces.")
        ]),
        ("DEEP LEARNING & NLP", ACCENT_TEAL, [
            ("facebook/bart-base", "139M-parameter bidirectional encoder & autoregressive decoder sequence model."),
            ("PyTorch 2.14.1+cu126", "Optimized CUDA 12.6 runtime tensor calculations on local RTX 4060 GPU."),
            ("Hugging Face Transformers", "Pipeline integration for sequence-to-sequence beam search decoding."),
            ("FP16 Mixed Precision", "Halves memory bandwidth and accelerates inference throughput.")
        ]),
        ("SERVING & INTERFACE", ACCENT_PURPLE, [
            ("Streamlit Reactive UI", "Interactive dark-mode workbench with multi-tab legal workspace."),
            ("PyPDF & Regex", "Fast, stream-based extraction and normalization of complex PDF legal filings."),
            ("Multi-Format Exporter", "Outputs structured legal briefs as TXT, Markdown reports, and JSON."),
            ("Immutable Audit Logger", "Persists full execution traces and confidence metrics to disk.")
        ]),
        ("BENCHMARK & QUALITY", ACCENT_EMERALD, [
            ("Pytest Test Suite", "60 / 60 automated unit and integration tests passing (100% pass rate)."),
            ("Official ROUGE Scorer", "Google official rouge_scorer computing ROUGE-1, ROUGE-2, and ROUGE-L."),
            ("CivilSum (SIGIR 2024)", "Benchmark corpus of 23,350 Indian Supreme Court and High Court cases."),
            ("Hardware Acceleration", "Local NVIDIA GeForce RTX 4060 Laptop GPU (8GB VRAM).")
        ])
    ]

    for i, (col_title, color, items) in enumerate(stacks):
        x = start_x + i * (card_w + gap)
        card = add_card(slide, x, card_y, card_w, card_h)

        # Top pill badge
        add_badge(slide, x + Inches(0.15), card_y + Inches(0.2), card_w - Inches(0.3), Inches(0.3), col_title, color, RGBColor(10, 17, 40))

        tf = card.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = Inches(0.2)
        tf.margin_top = Inches(0.45)

        p0 = tf.paragraphs[0]
        p0.text = "\n"

        for comp_name, comp_desc in items:
            p = tf.add_paragraph()
            p.text = f"{comp_name}"
            p.font.name = "Segoe UI"
            p.font.size = Pt(11)
            p.font.bold = True
            p.font.color.rgb = TEXT_WHITE

            pd = tf.add_paragraph()
            pd.text = comp_desc
            pd.font.name = "Segoe UI"
            pd.font.size = Pt(9)
            pd.font.color.rgb = TEXT_LIGHT
            pd.space_after = Pt(10)

    set_speaker_notes(slide, """
Slide 5 breaks down our technology stack across four pillars.

Under Agentic Orchestration, we rely on LangGraph to coordinate the state machine. We utilize the newly released Google GenAI SDK (v2.28.0) to communicate with gemini-2.5-flash. Crucially, we wrap all remote LLM calls with Tenacity exponential backoff to handle transient network drops.

Under Deep Learning and NLP, our core summarizer is facebook/bart-base, which contains 139 million parameters. We execute on PyTorch with CUDA 12.6 and FP16 precision, granting us rapid execution on our local RTX 4060 GPU without hitting VRAM bottlenecks.

For Serving, we built a modern Streamlit workbench that organizes the complex output into clear tabs for Abstractive Summary, Legal Doctrine, Validation Audits, and JSON Export.

Finally, for Validation and Quality, we maintain a robust Pytest suite comprising 60 automated unit and integration tests, all currently passing. We evaluate summary quality using the official Google ROUGE scorer.
""")


def build_slide_06_civilsum(prs):
    """Slide 6: CivilSum Dataset and Preprocessing."""
    slide = create_base_slide(
        prs,
        category="DATASET PROVENANCE  |  BENCHMARK FOUNDATION",
        title="CivilSum Dataset & Tail-Aware Preprocessing",
        subtitle="Grounding the neural summarizer in 23,350 peer-reviewed Indian court judgments (SIGIR '24).",
        slide_num=6
    )

    card_w = Inches(5.67)
    card_h = Inches(4.8)
    card_y = Inches(1.9)

    # Left Card: Dataset Provenance
    cl = add_card(slide, Inches(0.8), card_y, card_w, card_h)
    tfl = cl.text_frame
    tfl.word_wrap = True
    tfl.margin_left = tfl.margin_right = tfl.margin_top = Inches(0.3)

    add_badge(slide, Inches(1.1), card_y + Inches(0.25), Inches(2.6), Inches(0.3), "DATASET PROVENANCE", ACCENT_TEAL, RGBColor(10, 17, 40))
    p0 = tfl.paragraphs[0]
    p0.text = "\n\nCivilSum Benchmark (SIGIR 2024)"
    p0.font.name = "Segoe UI"
    p0.font.size = Pt(16)
    p0.font.bold = True
    p0.font.color.rgb = TEXT_WHITE
    p0.space_after = Pt(10)

    ds_points = [
        ("Publication", "Presented at SIGIR 2024 by Ramanujan et al. as the benchmark for abstractive court summarization."),
        ("Licensing", "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)."),
        ("Jurisdiction", "Appellate civil judgments from the Supreme Court of India and Indian High Courts."),
        ("Training Set", "21,015 court cases (278 MB) with full judgment text and expert-written summaries."),
        ("Validation Set", "1,168 court cases (15.5 MB) used for epoch-level checkpoint validation."),
        ("Held-out Test Set", "1,167 court cases (14.9 MB) reserved exclusively for unbiased final evaluation.")
    ]
    for lbl, val in ds_points:
        p = tfl.add_paragraph()
        p.text = f"•  {lbl}: "
        p.font.name = "Segoe UI"
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = ACCENT_CYAN
        run = p.add_run()
        run.text = val
        run.font.bold = False
        run.font.color.rgb = TEXT_LIGHT
        p.space_after = Pt(6)

    # Right Card: Tail-Aware Windowing
    cr = add_card(slide, Inches(6.86), card_y, card_w, card_h, bg_color=CARD_ACCENT_BG, border_color=ACCENT_CYAN, border_width=2.0)
    tfr = cr.text_frame
    tfr.word_wrap = True
    tfr.margin_left = tfr.margin_right = tfr.margin_top = Inches(0.3)

    add_badge(slide, Inches(7.16), card_y + Inches(0.25), Inches(2.8), Inches(0.3), "PREPROCESSING INNOVATION", ACCENT_CYAN, RGBColor(10, 17, 40))
    pr = tfr.paragraphs[0]
    pr.text = "\n\n800-Word Tail-Aware Trimming Algorithm"
    pr.font.name = "Segoe UI"
    pr.font.size = Pt(16)
    pr.font.bold = True
    pr.font.color.rgb = ACCENT_CYAN
    pr.space_after = Pt(10)

    algo_desc = [
        ("The Token Budget Constraint", "BART-base is architecturally bounded by an input attention context of 1,024 tokens (approx. 800 English words). Judgments easily reach 10,000+ words."),
        ("30% Lead Window (240 Words)", "Captures the formal title, presiding bench, litigant names, lower court appeal history, and the primary statutory questions at issue."),
        ("70% Tail Window (560 Words)", "Captures the decisive legal arguments, judicial interpretation of statutes, ratio decidendi, and the final operative decree ('Appeal Dismissed')."),
        ("Procedural Joining Tag", "Lead and Tail segments are joined with an explicit '[...]' omission tag, maintaining grammatical continuity without confusing the transformer attention heads.")
    ]
    for lbl, val in algo_desc:
        p = tfr.add_paragraph()
        p.text = f"✔  {lbl}: "
        p.font.name = "Segoe UI"
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = ACCENT_TEAL
        run = p.add_run()
        run.text = val
        run.font.bold = False
        run.font.color.rgb = TEXT_LIGHT
        p.space_after = Pt(8)

    set_speaker_notes(slide, """
Slide 6 highlights our dataset provenance and our algorithmic solution to tail bias.

We trained exclusively on the official CivilSum dataset published at SIGIR 2024. This is an authentic corpus containing 23,350 civil cases from the Supreme Court of India and state High Courts. It is partitioned into 21,015 training cases, 1,168 validation cases, and 1,167 test cases under a Creative Commons CC BY-NC-SA 4.0 license.

The key engineering innovation on this slide is our 800-word Tail-Aware Trimming Algorithm.
As mentioned earlier, standard transformers like BART-base have an input limit of 1,024 tokens—roughly 800 words. Because legal decisions are 20 to 50 pages long, blind truncation discards the decision.

To solve this, our preprocessor divides the 800-word budget into two asymmetrical windows:
The first 30% (240 words) preserves the lead: court identity, parties, and the statutory issue.
The remaining 70% (560 words) preserves the tail: the judge's reasoning, statutory analysis, and final verdict.
These are stitched together with a procedural omission tag. This single preprocessing step ensures that BART always sees the verdict and never hallucinates an inverted disposition.
""")


def build_slide_07_bart_training(prs):
    """Slide 7: BART Fine-Tuning."""
    slide = create_base_slide(
        prs,
        category="SUPERVISED TRAINING  |  GPU ACCELERATION",
        title="Supervised Fine-Tuning of facebook/bart-base",
        subtitle="Domain adaptation of sequence-to-sequence transformer weights on NVIDIA RTX 4060.",
        slide_num=7
    )

    # 4 Top Metric Cards
    met_w = Inches(2.78)
    met_h = Inches(1.3)
    met_y = Inches(1.9)
    gap = Inches(0.2)
    start_x = Inches(0.8)

    add_metric_card(slide, start_x, met_y, met_w, met_h, "139M", "Model Parameters", "facebook/bart-base architecture", ACCENT_CYAN)
    add_metric_card(slide, start_x + (met_w + gap), met_y, met_w, met_h, "196.14s", "Training Duration", "3.27 mins on local RTX 4060", ACCENT_TEAL)
    add_metric_card(slide, start_x + 2 * (met_w + gap), met_y, met_w, met_h, "2.306", "Best Validation Loss", "Down from initial ~14.0 cross-entropy", ACCENT_EMERALD)
    add_metric_card(slide, start_x + 3 * (met_w + gap), met_y, met_w, met_h, "225", "Global Steps", "3 Epochs, Effective Batch Size 16", ACCENT_GOLD)

    # 2 Bottom Cards
    card_w = Inches(5.67)
    card_h = Inches(3.3)
    card_y = Inches(3.4)

    # Left: Hyperparameters
    cl = add_card(slide, Inches(0.8), card_y, card_w, card_h)
    tfl = cl.text_frame
    tfl.word_wrap = True
    tfl.margin_left = tfl.margin_right = Inches(0.25)
    tfl.margin_top = Inches(0.2)

    p0 = tfl.paragraphs[0]
    p0.text = "HYPERPARAMETERS & HARDWARE ACCELERATION"
    p0.font.name = "Segoe UI"
    p0.font.size = Pt(11)
    p0.font.bold = True
    p0.font.color.rgb = ACCENT_CYAN
    p0.space_after = Pt(8)

    params = [
        ("Hardware Accelerator", "NVIDIA GeForce RTX 4060 Laptop GPU (8,188 MiB VRAM), CUDA 12.6"),
        ("Optimizer & Learning Rate", "AdamW optimizer, lr = 3e-5, weight_decay = 0.01"),
        ("Batch Configuration", "Per-device batch size = 4, Gradient Accumulation = 4 (Effective batch size = 16)"),
        ("Precision", "FP16 Mixed Precision enabled for enhanced tensor core throughput"),
        ("Sample Subset", "1,200 training cases, 300 validation cases, 3 full training epochs"),
        ("Model Checkpoint", "models/checkpoints/civilsum_bart (saved via load_best_model_at_end)")
    ]
    for lbl, val in params:
        p = tfl.add_paragraph()
        p.text = f"• {lbl}: "
        p.font.name = "Segoe UI"
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = TEXT_WHITE
        run = p.add_run()
        run.text = val
        run.font.bold = False
        run.font.color.rgb = TEXT_LIGHT
        p.space_after = Pt(4)

    # Right: Loss Progression & Safety
    cr = add_card(slide, Inches(6.86), card_y, card_w, card_h)
    tfr = cr.text_frame
    tfr.word_wrap = True
    tfr.margin_left = tfr.margin_right = Inches(0.25)
    tfr.margin_top = Inches(0.2)

    pr0 = tfr.paragraphs[0]
    pr0.text = "TRAINING PROGRESSION & INTEGRITY GUARDS"
    pr0.font.name = "Segoe UI"
    pr0.font.size = Pt(11)
    pr0.font.bold = True
    pr0.font.color.rgb = ACCENT_TEAL
    pr0.space_after = Pt(8)

    prog_points = [
        ("Loss Descent Convergence", "Validation cross-entropy loss descended rapidly: Initial loss ~14.0 → Epoch 2 loss: 2.318 → Epoch 3 loss: 2.306 (final step loss: 9.852)."),
        ("Validation Throughput", "Sustained high evaluation speeds of 67.61 to 75.08 samples per second during validation passes."),
        ("Strict Checkpoint Enforcement", "The codebase strictly halts with an informative error if the fine-tuned checkpoint is missing, preventing silent fallbacks to untrained generic weights."),
        ("Deterministic Reproducibility", "Training metadata, random seeds, and hardware configurations are permanently serialized in training_metadata.json.")
    ]
    for lbl, val in prog_points:
        p = tfr.add_paragraph()
        p.text = f"✔ {lbl}: "
        p.font.name = "Segoe UI"
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = ACCENT_EMERALD
        run = p.add_run()
        run.text = val
        run.font.bold = False
        run.font.color.rgb = TEXT_LIGHT
        p.space_after = Pt(6)

    set_speaker_notes(slide, """
Slide 7 provides the empirical details of our supervised fine-tuning execution.

We chose facebook/bart-base, which features a bidirectional encoder and an autoregressive decoder with 139 million parameters. The model was trained locally on an NVIDIA GeForce RTX 4060 Laptop GPU with 8GB of VRAM running CUDA 12.6.

To maximize throughput within 8GB VRAM, we used FP16 mixed precision, a per-device batch size of 4, and gradient accumulation of 4 steps, producing an effective batch size of 16. Using AdamW with a learning rate of 3e-5, training ran for 3 epochs across 225 global optimization steps.

Total training time was exceptionally fast: 196.14 seconds, or roughly 3.27 minutes.
As shown in the cards, validation cross-entropy loss converged smoothly from an initial loss of ~14.0 down to 2.318 in Epoch 2 and 2.306 in Epoch 3. The best checkpoint was saved to models/checkpoints/civilsum_bart.

Importantly, our codebase implements strict checkpoint enforcement: if this local fine-tuned folder is ever missing, the pipeline halts immediately rather than silently falling back to a generic baseline model that lacks legal vocabulary.
""")


def build_slide_08_gemini_agents(prs):
    """Slide 8: Gemini Agents and Legal Reasoning Workflow."""
    slide = create_base_slide(
        prs,
        category="AGENTIC REASONING  |  HTTP 503 FAULT TOLERANCE",
        title="Gemini Reasoning Agents & Resilience Architecture",
        subtitle="Extracting complex legal doctrines via zero-shot prompts with enterprise backoff protection.",
        slide_num=8
    )

    card_w = Inches(5.67)
    card_h = Inches(4.8)
    card_y = Inches(1.9)

    # Left: Agent Roles
    cl = add_card(slide, Inches(0.8), card_y, card_w, card_h)
    tfl = cl.text_frame
    tfl.word_wrap = True
    tfl.margin_left = tfl.margin_right = Inches(0.3)
    tfl.margin_top = Inches(0.25)

    add_badge(slide, Inches(1.1), card_y + Inches(0.25), Inches(2.4), Inches(0.3), "SPECIALIZED AGENTS", ACCENT_PURPLE, RGBColor(10, 17, 40))
    p0 = tfl.paragraphs[0]
    p0.text = "\n\nZero-Shot Prompt Framing & Roles"
    p0.font.name = "Segoe UI"
    p0.font.size = Pt(16)
    p0.font.bold = True
    p0.font.color.rgb = TEXT_WHITE
    p0.space_after = Pt(10)

    roles = [
        ("Stage 2: Document Structure Agent", "Extracts structural legal entities into validated JSON: Case Title, Court Name, Coram/Bench, Petitioner, Respondent, and Statutory Acts involved."),
        ("Stage 3: Legal Reasoner Agent", "Extracts jurisprudential components: Procedural Background, Questions of Law, Litigant Contentions, Ratio Decidendi (the legal holding), and Court Decree."),
        ("Strict Schema Enforcement", "Both agents enforce strict JSON schemas with low temperature (0.2) to eliminate creative hallucination and ensure deterministic downstream parsing."),
        ("Zero Fabrication Rule", "Prompts explicitly mandate: 'If a statutory section or bench name is not mentioned in the source judgment, return null rather than guessing.'")
    ]
    for lbl, val in roles:
        p = tfl.add_paragraph()
        p.text = f"• {lbl}: "
        p.font.name = "Segoe UI"
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = ACCENT_CYAN
        run = p.add_run()
        run.text = val
        run.font.bold = False
        run.font.color.rgb = TEXT_LIGHT
        p.space_after = Pt(8)

    # Right: HTTP 503 Resiliency
    cr = add_card(slide, Inches(6.86), card_y, card_w, card_h, bg_color=CARD_ACCENT_BG, border_color=ACCENT_GOLD, border_width=2.0)
    tfr = cr.text_frame
    tfr.word_wrap = True
    tfr.margin_left = tfr.margin_right = Inches(0.3)
    tfr.margin_top = Inches(0.25)

    add_badge(slide, Inches(7.16), card_y + Inches(0.25), Inches(2.6), Inches(0.3), "ENTERPRISE RESILIENCE", ACCENT_GOLD, RGBColor(10, 17, 40))
    pr = tfr.paragraphs[0]
    pr.text = "\n\nHTTP 503 Mitigation & Backoff"
    pr.font.name = "Segoe UI"
    pr.font.size = Pt(16)
    pr.font.bold = True
    pr.font.color.rgb = ACCENT_GOLD
    pr.space_after = Pt(10)

    resilience = [
        ("The Challenge: Transient 503s", "Cloud LLMs frequently return HTTP 503 Service Unavailable during peak compute load, causing unhandled pipeline exceptions."),
        ("Tenacity Exponential Backoff", "Integrated tenacity retry decorators with exponential backoff and randomized jitter: Attempt 1 at 2s → Attempt 2 at 4s → Attempt 3 at 8s."),
        ("Retry Storm Prevention", "Decoupled retry loops between Document Structure and Legal Reasoner nodes to prevent compounding simultaneous requests from overwhelming the API."),
        ("Graceful Degradation", "If cloud services remain offline after 3 attempts, the pipeline flags the agent as unavailable without faking legal data, allowing the local BART model to continue.")
    ]
    for lbl, val in resilience:
        p = tfr.add_paragraph()
        p.text = f"✔ {lbl}: "
        p.font.name = "Segoe UI"
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = ACCENT_TEAL
        run = p.add_run()
        run.text = val
        run.font.bold = False
        run.font.color.rgb = TEXT_LIGHT
        p.space_after = Pt(8)

    set_speaker_notes(slide, """
Slide 8 focuses on our agentic reasoning layer powered by Google Gemini and our enterprise resiliency engineering.

While our fine-tuned BART model is responsible for generating fluent, abstractive summaries, legal research demands doctrinal decomposition. We deploy two specialized Gemini agents:
The Document Structure Agent extracts procedural entities into typed JSON.
The Legal Reasoner Agent extracts the Questions of Law, Litigant Contentions, Ratio Decidendi, and Final Holding.
We enforce a low temperature of 0.2 and strict schemas to prevent imaginative fabrication.

The right-hand card addresses a crucial production challenge: transient HTTP 503 UNAVAILABLE errors.
Cloud LLM endpoints can be temporarily congested. Previously, a 503 would crash the entire workflow. We re-engineered the pipeline with Tenacity exponential backoff, applying three retries with random jitter at 2, 4, and 8 seconds.
We also decoupled the execution of the Document Structure and Legal Reasoner nodes so they never trigger simultaneous retry storms.
If the API remains down after three attempts, the system surfaces a clear diagnostic message, logs the incident, and allows the local BART summarizer to complete its work without fabricating false legal doctrines.
""")


def build_slide_09_evaluation(prs):
    """Slide 9: Validation, Test Results, and Evaluation Metrics."""
    slide = create_base_slide(
        prs,
        category="EMPIRICAL BENCHMARKING  |  QUALITY ASSURANCE",
        title="Empirical Results, Grounding Auditor, & Test Suite",
        subtitle="Quantitative ROUGE scores on held-out test data, deterministic fact-checking, and test coverage.",
        slide_num=9
    )

    # 4 Top Metric Cards
    met_w = Inches(2.78)
    met_h = Inches(1.3)
    met_y = Inches(1.9)
    gap = Inches(0.2)
    start_x = Inches(0.8)

    add_metric_card(slide, start_x, met_y, met_w, met_h, "37.39", "ROUGE-1 F1", "Unigram Overlap & Key Terminology", ACCENT_CYAN)
    add_metric_card(slide, start_x + (met_w + gap), met_y, met_w, met_h, "14.31", "ROUGE-2 F1", "Bigram Overlap & Legal Phrasing", ACCENT_TEAL)
    add_metric_card(slide, start_x + 2 * (met_w + gap), met_y, met_w, met_h, "24.62", "ROUGE-L F1", "Sentence Structure & Sequence Flow", ACCENT_GOLD)
    add_metric_card(slide, start_x + 3 * (met_w + gap), met_y, met_w, met_h, "60 / 60", "Automated Tests", "100% Pass Rate across Pytest Suite", ACCENT_EMERALD)

    # 2 Bottom Cards
    card_w = Inches(5.67)
    card_h = Inches(3.3)
    card_y = Inches(3.4)

    # Left: Evaluation Protocol
    cl = add_card(slide, Inches(0.8), card_y, card_w, card_h)
    tfl = cl.text_frame
    tfl.word_wrap = True
    tfl.margin_left = tfl.margin_right = Inches(0.25)
    tfl.margin_top = Inches(0.2)

    p0 = tfl.paragraphs[0]
    p0.text = "EMPIRICAL EVALUATION PROTOCOL & DISCLOSURE"
    p0.font.name = "Segoe UI"
    p0.font.size = Pt(11)
    p0.font.bold = True
    p0.font.color.rgb = ACCENT_CYAN
    p0.space_after = Pt(8)

    eval_items = [
        ("Official Test Split", "Evaluated on 50 randomly sampled test court cases from official data/test.csv."),
        ("Scoring Mechanism", "Computed via official Google rouge_scorer comparing generated abstractive text directly against expert-written judicial headnotes."),
        ("ROUGE-1 (37.39)", "Measures informative lexical coverage—capturing party names, statutory acts, and core subject matter."),
        ("ROUGE-2 (14.31)", "Measures paired legal phrasing fluency (e.g., 'civil appeal', 'substantial question of law', 'decree passed')."),
        ("ROUGE-L (24.62)", "Measures Longest Common Subsequence, confirming syntactic coherence and narrative flow.")
    ]
    for lbl, val in eval_items:
        p = tfl.add_paragraph()
        p.text = f"• {lbl}: "
        p.font.name = "Segoe UI"
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = TEXT_WHITE
        run = p.add_run()
        run.text = val
        run.font.bold = False
        run.font.color.rgb = TEXT_LIGHT
        p.space_after = Pt(4)

    # Right: Grounding Auditor
    cr = add_card(slide, Inches(6.86), card_y, card_w, card_h)
    tfr = cr.text_frame
    tfr.word_wrap = True
    tfr.margin_left = tfr.margin_right = Inches(0.25)
    tfr.margin_top = Inches(0.2)

    pr0 = tfr.paragraphs[0]
    pr0.text = "DETERMINISTIC GROUNDING AUDITOR & TEST SUITE"
    pr0.font.name = "Segoe UI"
    pr0.font.size = Pt(11)
    pr0.font.bold = True
    pr0.font.color.rgb = ACCENT_EMERALD
    pr0.space_after = Pt(8)

    aud_items = [
        ("Deterministic Regex Parsing", "Scans the generated summary for all cited statutory sections (e.g., 'Section 9 CPC') and checks verbatim grounding in the source judgment."),
        ("Disposition Concordance Gate", "Validates that the final holding in the summary matches the extracted court disposition, eliminating the catastrophic inversion error."),
        ("Factual Consistency Metric", "Generates an objective grounding score between 0.0 and 1.0 based on entity overlap and statutory grounding."),
        ("60/60 Passing Test Suite", "Full test suite covering BART checkpoint loading, LangGraph state transitions, retry backoffs, mock 503 handling, and PDF parsing.")
    ]
    for lbl, val in aud_items:
        p = tfr.add_paragraph()
        p.text = f"✔ {lbl}: "
        p.font.name = "Segoe UI"
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = ACCENT_TEAL
        run = p.add_run()
        run.text = val
        run.font.bold = False
        run.font.color.rgb = TEXT_LIGHT
        p.space_after = Pt(4)

    set_speaker_notes(slide, """
Slide 9 presents our quantitative evaluation metrics, deterministic validation rules, and automated test suite.

Across our held-out test evaluation—conducted on 50 randomly sampled cases from data/test.csv—our fine-tuned model achieved:
A ROUGE-1 F1 score of 37.39, indicating strong lexical and concept recall;
A ROUGE-2 score of 14.31, reflecting accurate consecutive legal phrasing;
And a ROUGE-L score of 24.62, confirming preservation of sentence structure and narrative continuity.
These numbers are documented in evaluation_results.json.

In addition to ROUGE, our architecture includes a deterministic Grounding Auditor. It does not use generative heuristics; instead, it uses regular expressions to extract every cited statutory section and validates that each one appears in the original text. It also verifies that the summary's disposition matches the court's operative holding, preventing inversion errors.

Finally, we emphasize that our entire system is validated by an automated Pytest suite of 60 unit and integration tests, which currently stands at a 100% pass rate.
""")


def build_slide_10_screenshots(prs):
    """Slide 10: Application Screenshots and Live Demo Workflow."""
    slide = create_base_slide(
        prs,
        category="PRODUCTION SYSTEM  |  USER WORKFLOW",
        title="Application Interface & Interactive Workflow",
        subtitle="Streamlit-powered interactive interface designed specifically for legal practitioners and researchers.",
        slide_num=10
    )

    # 4 Screenshot Cards arranged horizontally
    card_w = Inches(2.78)
    card_h = Inches(4.8)
    card_y = Inches(1.9)
    gap = Inches(0.2)
    start_x = Inches(0.8)

    demo_steps = [
        ("1. Ingestion & Status", "02_pdf_uploaded.png", "Upload legal PDF; inspect real-time extraction, token count, and active model checkpoint."),
        ("2. Abstractive Summary", "03_abstractive_summary.png", "Fine-tuned BART generates a concise neural headnote using 30/70 tail-aware synthesis."),
        ("3. Legal Doctrine", "04_legal_analysis_and_doctrine.png", "Inspect Questions of Law, Litigant Contentions, Ratio Decidendi, and Final Holding."),
        ("4. Validation & Audit", "05_validation_and_grounding.png", "Deterministic statutory grounding scores, consistency verification, and full audit trail.")
    ]

    for i, (step_title, img_filename, desc) in enumerate(demo_steps):
        x = start_x + i * (card_w + gap)
        card = add_card(slide, x, card_y, card_w, card_h)

        # Header tag
        add_badge(slide, x + Inches(0.15), card_y + Inches(0.15), card_w - Inches(0.3), Inches(0.3), step_title, ACCENT_CYAN, RGBColor(10, 17, 40))

        # Embed screenshot
        img_path = SCREENSHOTS_DIR / img_filename
        if img_path.exists():
            img_y = card_y + Inches(0.55)
            img_w = card_w - Inches(0.3)
            img_h = Inches(2.6)
            slide.shapes.add_picture(str(img_path), x + Inches(0.15), img_y, img_w, img_h)
        else:
            # Placeholder card if image missing
            ph = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x + Inches(0.15), card_y + Inches(0.55), card_w - Inches(0.3), Inches(2.6))
            ph.fill.solid()
            ph.fill.fore_color.rgb = RGBColor(15, 23, 42)

        # Text explanation below image
        tbox = slide.shapes.add_textbox(x + Inches(0.15), card_y + Inches(3.25), card_w - Inches(0.3), Inches(1.4))
        tf = tbox.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

        p = tf.paragraphs[0]
        p.text = desc
        p.font.name = "Segoe UI"
        p.font.size = Pt(9.5)
        p.font.color.rgb = TEXT_LIGHT

    set_speaker_notes(slide, """
Slide 10 presents the interactive user experience in our Streamlit application, capturing the four primary tabs.

In Column 1, we see Document Ingestion. The user uploads a court judgment in PDF format or enters raw text. The application validates character integrity, reports token counts, and displays the active checkpoint status.

In Column 2, Tab 1 presents the Abstractive Summary generated by our fine-tuned BART model. Notice that it provides a coherent, four-to-five sentence synthesis capturing the core procedural issue and final decree.

In Column 3, Tab 2 displays the Legal Reasoning breakdown. The practitioner can review the extracted Questions of Law, the arguments of the petitioner and respondent, the ratio decidendi, and the operative holding.

In Column 4, Tab 3 displays the Validation and Grounding report. The user sees an objective Grounding Score, a list of verified statutory provisions, and confirmation that the disposition is concordant with the judgment. The user can also export the entire structured brief as Markdown, plain text, or an immutable JSON audit log.
""")


def build_slide_11_limitations(prs):
    """Slide 11: Limitations and Future Improvements."""
    slide = create_base_slide(
        prs,
        category="ACADEMIC INTEGRITY  |  ROADMAP & ETHICAL DISCLOSURES",
        title="Technical Limitations & Future Roadmap",
        subtitle="Honest disclosure of model boundaries, technical constraints, and planned engineering upgrades.",
        slide_num=11
    )

    card_w = Inches(5.67)
    card_h = Inches(4.8)
    card_y = Inches(1.9)

    # Left: Limitations
    cl = add_card(slide, Inches(0.8), card_y, card_w, card_h)
    tfl = cl.text_frame
    tfl.word_wrap = True
    tfl.margin_left = tfl.margin_right = Inches(0.3)
    tfl.margin_top = Inches(0.25)

    add_badge(slide, Inches(1.1), card_y + Inches(0.25), Inches(2.6), Inches(0.3), "TECHNICAL BOUNDARIES", ACCENT_GOLD, RGBColor(10, 17, 40))
    p0 = tfl.paragraphs[0]
    p0.text = "\n\nCurrent Constraints & Disclosures"
    p0.font.name = "Segoe UI"
    p0.font.size = Pt(16)
    p0.font.bold = True
    p0.font.color.rgb = TEXT_WHITE
    p0.space_after = Pt(10)

    limits = [
        ("1,024-Token Context Limit", "BART-base is bounded by a 1,024-token attention window. While our 30/70 tail trimming preserves core rulings, intermediate witness details in 50+ page rulings are inevitably omitted."),
        ("Evaluation Subset Disclosure", "In adherence to research integrity: official evaluation was conducted on 50 sampled test cases (due to single-laptop GPU time constraints) rather than all 1,167 test cases."),
        ("Scanned PDF Dependency", "PyPDF relies on digital PDF text streams. Scanned image-only judgments without an embedded OCR text layer require pre-extraction."),
        ("Jurisdiction Specificity", "Weights are fine-tuned on Indian civil appellate judgments; criminal jurisprudence and foreign common-law systems have not been benchmarked.")
    ]
    for lbl, val in limits:
        p = tfl.add_paragraph()
        p.text = f"• {lbl}: "
        p.font.name = "Segoe UI"
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = ACCENT_GOLD
        run = p.add_run()
        run.text = val
        run.font.bold = False
        run.font.color.rgb = TEXT_LIGHT
        p.space_after = Pt(8)

    # Right: Roadmap
    cr = add_card(slide, Inches(6.86), card_y, card_w, card_h, bg_color=CARD_ACCENT_BG, border_color=ACCENT_CYAN, border_width=2.0)
    tfr = cr.text_frame
    tfr.word_wrap = True
    tfr.margin_left = tfr.margin_right = Inches(0.3)
    tfr.margin_top = Inches(0.25)

    add_badge(slide, Inches(7.16), card_y + Inches(0.25), Inches(2.6), Inches(0.3), "FUTURE ROADMAP", ACCENT_CYAN, RGBColor(10, 17, 40))
    pr = tfr.paragraphs[0]
    pr.text = "\n\nPlanned Upgrades & Research Path"
    pr.font.name = "Segoe UI"
    pr.font.size = Pt(16)
    pr.font.bold = True
    pr.font.color.rgb = ACCENT_CYAN
    pr.space_after = Pt(10)

    roadmap = [
        ("Long-Context Transformer (LED-16384)", "Upgrade base summarizer to allenai/led-base-16384 (Longformer Encoder-Decoder) to ingest entire 50-page judgments natively without trimming."),
        ("Full-Split Cluster Evaluation", "Execute distributed batch evaluation across all 1,167 held-out CivilSum test cases on a multi-GPU compute cluster."),
        ("Judicial OCR Pipeline", "Integrate Surya or Tesseract OCR with judicial stamp layout analysis to process historical scanned trial court orders."),
        ("Live Citation Verification (RAG)", "Connect the validation node to live Indian Kanoon and Supreme Court e-Courts APIs to verify whether cited precedents remain good law or have been overruled.")
    ]
    for lbl, val in roadmap:
        p = tfr.add_paragraph()
        p.text = f"➔ {lbl}: "
        p.font.name = "Segoe UI"
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = ACCENT_TEAL
        run = p.add_run()
        run.text = val
        run.font.bold = False
        run.font.color.rgb = TEXT_LIGHT
        p.space_after = Pt(8)

    set_speaker_notes(slide, """
Slide 11 addresses our technical limitations and future roadmap with full academic integrity.

Every engineering project has constraints, and we document ours clearly:
First, while our 30/70 tail-aware windowing solves the holding omission problem, BART-base's 1,024-token window cannot ingest extensive intermediate evidence from 60-page constitutional bench rulings.
Second, as disclosed in our documentation, our evaluation metrics reflect 50 held-out test judgments. Evaluating all 1,167 test cases with beam search on a single laptop GPU requires significant compute time.
Third, our current extractor relies on digital PDF text layers; scanned photocopies require external OCR.
Finally, the model is specialized for Indian civil appellate law and has not been tuned on criminal or foreign jurisdictions.

Our future engineering roadmap addresses these areas directly:
We plan to upgrade from BART to allenai/led-base-16384, expanding our attention window sixteen-fold to ingest complete judgments.
We will run full-corpus benchmarking on multi-GPU cloud infrastructure.
We will integrate dedicated judicial OCR for historical appeals.
And we aim to connect our validation auditor to live Indian Kanoon APIs to verify whether cited case law has been subsequently overturned.
""")


def build_slide_12_conclusion(prs):
    """Slide 12: Conclusion and Q&A."""
    slide = create_base_slide(
        prs,
        category="PROJECT SUMMARY  |  ACADEMIC DEFENSE",
        title="Conclusion & Research Contributions",
        subtitle="A verified blueprint for combining local specialized transformers with agentic reasoning in high-stakes domains.",
        slide_num=12
    )

    card_w = Inches(3.64)
    card_h = Inches(3.4)
    card_y = Inches(1.9)

    # 3 Summary Cards
    cards_data = [
        ("Hybrid Architecture", ACCENT_CYAN, [
            "Proved that high-stakes legal summarization is best solved not by monolithic models, but by combining local fine-tuned transformers with zero-shot reasoning agents.",
            "Retains local privacy and high throughput for neural abstractive text.",
            "Leverages cloud LLMs solely for structured legal doctrine extraction."
        ]),
        ("Tail Bias Solution", ACCENT_TEAL, [
            "Engineered a domain-aware 30/70 lead/tail dynamic trimming heuristic.",
            "Eliminated the catastrophic omission of judicial ratio decidendi and court orders under tight token limits.",
            "Yielded competitive ROUGE-1 (37.39) and ROUGE-L (24.62) scores."
        ]),
        ("Production Reliability", ACCENT_EMERALD, [
            "Engineered enterprise fault-tolerance: exponential backoff eliminates HTTP 503 crash vulnerabilities.",
            "Deterministic grounding auditor flags statutory hallucinations and prevents inversion errors.",
            "Backed by 60/60 passing automated tests and immutable JSON audit trails."
        ])
    ]

    for i, (title_txt, color, bullets) in enumerate(cards_data):
        x = Inches(0.8) + i * (card_w + Inches(0.4))
        card = add_card(slide, x, card_y, card_w, card_h)

        add_badge(slide, x + Inches(0.2), card_y + Inches(0.2), card_w - Inches(0.4), Inches(0.32), title_txt.upper(), color, RGBColor(10, 17, 40))

        tf = card.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = Inches(0.2)
        tf.margin_top = Inches(0.5)

        p0 = tf.paragraphs[0]
        p0.text = "\n"

        for b in bullets:
            p = tf.add_paragraph()
            p.text = f"• {b}"
            p.font.name = "Segoe UI"
            p.font.size = Pt(9.5)
            p.font.color.rgb = TEXT_LIGHT
            p.space_after = Pt(6)

    # Bottom Banner Card
    bot_card = add_card(slide, Inches(0.8), Inches(5.5), Inches(11.733), Inches(1.2), bg_color=CARD_ACCENT_BG, border_color=ACCENT_CYAN, border_width=2.0)
    btf = bot_card.text_frame
    btf.word_wrap = True
    btf.vertical_anchor = MSO_ANCHOR.MIDDLE
    btf.margin_left = Inches(0.4)
    btf.margin_right = Inches(0.4)

    bp0 = btf.paragraphs[0]
    bp0.text = "THANK YOU  |  OPEN FOR QUESTIONS & DISCUSSION"
    bp0.alignment = PP_ALIGN.CENTER
    bp0.font.name = "Segoe UI"
    bp0.font.size = Pt(16)
    bp0.font.bold = True
    bp0.font.color.rgb = ACCENT_CYAN
    bp0.space_after = Pt(4)

    bp1 = btf.add_paragraph()
    bp1.text = "Repository: Legal-Document-Summarization  •  Verified Checkpoint: models/checkpoints/civilsum_bart  •  60/60 Tests Passing"
    bp1.alignment = PP_ALIGN.CENTER
    bp1.font.name = "Segoe UI"
    bp1.font.size = Pt(10)
    bp1.font.color.rgb = TEXT_WHITE

    set_speaker_notes(slide, """
In conclusion, Slide 12 summarizes our primary contributions:

First, we demonstrated that high-stakes legal NLP is most effectively solved through a hybrid architecture. By dividing responsibilities between a locally fine-tuned sequence-to-sequence model and zero-shot reasoning agents, we achieve both data privacy and deep legal reasoning without relying blindly on an ungrounded black-box LLM.

Second, we introduced a reproducible 30/70 tail-aware windowing heuristic that directly addresses the unique topological tail bias of Indian judicial rulings, ensuring that the court's holding is never lost to truncation.

Third, we engineered enterprise-grade reliability into our workflow: incorporating exponential backoff against API downtime, building a deterministic grounding auditor that guards against hallucination and inversion, and validating the entire system through 60 automated tests.

Thank you very much for your time and attention. I now welcome your questions, critique, and discussion.
""")


# -----------------------------------------------------------------------------
# MAIN GENERATOR ROUTINE
# -----------------------------------------------------------------------------
def main():
    print(f"[*] Initializing presentation generator...")
    prs = Presentation()
    prs.slide_width = SLIDE_WIDTH
    prs.slide_height = SLIDE_HEIGHT

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[*] Building 12 slides...")
    build_slide_01_title(prs)
    build_slide_02_problem(prs)
    build_slide_03_objectives(prs)
    build_slide_04_architecture(prs)
    build_slide_05_tech_stack(prs)
    build_slide_06_civilsum(prs)
    build_slide_07_bart_training(prs)
    build_slide_08_gemini_agents(prs)
    build_slide_09_evaluation(prs)
    build_slide_10_screenshots(prs)
    build_slide_11_limitations(prs)
    build_slide_12_conclusion(prs)

    total_slides = len(prs.slides)
    print(f"[*] Total slides generated: {total_slides}")
    assert total_slides == 12, f"Expected exactly 12 slides, but got {total_slides}"

    prs.save(OUTPUT_FILE)
    print(f"[OK] Presentation saved successfully to:\n    {OUTPUT_FILE}")
    print(f"[OK] File size: {OUTPUT_FILE.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
