# System Architecture: Agent Workflow & Component Responsibilities

## 1. Architectural Philosophy
The system implements a **Modular Agentic Workflow** orchestrated by **LangGraph**. Decomposing the system into specialized nodes addresses the primary failure mode of end-to-end monolithic LLM summarization: loss of legal nuance, loss of operative holding, and ungrounded hallucinations.

```
       ┌────────────────────────────────────────────────────────┐
       │                   Incoming Request                     │
       │   (PDF Document Bytes OR Raw Legal Judgment Text)      │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │             Stage 1: PDF Extractor Agent               │
       │   • Technology: PyPDF + Regular Expression Cleaners    │
       │   • Task: Raw text extraction, stripping headers,      │
       │     normalizing whitespace & legal citation strings    │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │          Stage 2: Document Analysis Agent              │
       │   • Technology: Google Gemini (gemini-2.5-flash)       │
       │   • Task: Zero-shot JSON extraction: Case Title, Court │
       │     Bench, Petitioner, Respondent, Statues Involved    │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │            Stage 3: Legal Reasoner Agent               │
       │   • Technology: Google Gemini (gemini-2.5-flash)       │
       │   • Task: Jurisprudential extraction: Questions of     │
       │     Law, Contentions, Ratio Decidendi, Final Holding   │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │          Stage 4: Supervised BART Summarizer           │
       │   • Technology: facebook/bart-base Fine-Tuned (CUDA)   │
       │   • Preprocessing: Tail-Aware Window (30% lead/70% tail│
       │   • Task: Neural abstractive headnote summary          │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │             Stage 5: Validation Agent                  │
       │   • Technology: Deterministic Rule-Based Auditor       │
       │   • Task: Factual consistency scoring, coverage score, │
       │     hallucination detection (dates, statutory sections)│
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │                  Final Workflow State                  │
       │   • Rendered in Multi-Tab Streamlit UI                 │
       │   • Recorded in Immutable Audit Trail (.json)          │
       │   • Multi-format Export (TXT, Markdown Report, JSON)   │
       └────────────────────────────────────────────────────────┘
```

---

## 2. Detailed Component Responsibilities

### Component 1: Ingestion & Text Normalization (`PDFExtractorAgent`)
- **Module:** [agents/pdf_extractor.py](file:///c:/Users/sujat.MANVITH/OneDrive/Desktop/antigravity/Legal-Document-Summarization/agents/pdf_extractor.py)
- **Inputs:** PDF byte stream or direct text input.
- **Responsibilities:**
  - Extracts text across multiple PDF pages with error trapping for empty or password-protected files.
  - Normalizes idiosyncratic judicial formats: line breaks inside citations, page numbers, trailing appellate stamps, and courtroom header artifacts.
  - Outputs sanitized UTF-8 legal text and document metadata (word count, page count).

### Component 2: Structural Analysis (`DocumentAnalysisAgent`)
- **Module:** [agents/document_analyzer.py](file:///c:/Users/sujat.MANVITH/OneDrive/Desktop/antigravity/Legal-Document-Summarization/agents/document_analyzer.py)
- **Engine:** Google Gemini (`gemini-2.5-flash` or configurable `gemini-1.5-pro`).
- **Prompt Architecture:** Zero-shot system prompt requiring strict JSON adherence.
- **Extracted Fields:**
  - `case_title`: Standard appellate or original jurisdiction case title.
  - `court_name`: Supreme Court of India or respective High Court.
  - `petitioner` & `respondent`: Litigating parties.
  - `bench`: Presiding judges or bench constitution.
  - `statutes_involved`: Specific Acts (e.g., *Code of Civil Procedure, 1908*).
  - `factual_background`: 2–3 sentence factual predicate of the dispute.
- **Safety / Fallback:** Gracefully halts if `GEMINI_API_KEY` is missing without crashing.

### Component 3: Jurisprudential Reasoning (`LegalReasonerAgent`)
- **Module:** [agents/legal_reasoner.py](file:///c:/Users/sujat.MANVITH/OneDrive/Desktop/antigravity/Legal-Document-Summarization/agents/legal_reasoner.py)
- **Engine:** Google Gemini.
- **Responsibilities:**
  - `questions_of_law`: Primary constitutional or statutory questions formulated for determination.
  - `petitioner_arguments`: Core contentions advanced by appellant/petitioner counsel.
  - `respondent_arguments`: Defenses raised by the opposing party.
  - `ratio_decidendi`: The core legal principle underlying the decision.
  - `court_holding_and_disposition`: The operative decree (e.g., *appeal allowed, decree set aside, remanded for fresh adjudication*).
  - `obiter_dicta`: Judicial remarks not essential to the determination.

### Component 4: Neural Abstractive Summarizer (`BARTSummarizerAgent`)
- **Module:** [agents/bart_summarizer.py](file:///c:/Users/sujat.MANVITH/OneDrive/Desktop/antigravity/Legal-Document-Summarization/agents/bart_summarizer.py)
- **Model:** Fine-tuned `facebook/bart-base` checkpoint stored at `models/checkpoints/civilsum_bart/`.
- **Inference Mode:**
  - `fine_tuned`: Strictly requires valid local checkpoint weights (`model.safetensors`).
  - `pretrained_base`: Explicit baseline comparison mode using raw `facebook/bart-base`.
- **Tail-Aware Trimming:**
  - Legal judgments exceed the 1024-token context window of BART.
  - Preserves first 240 words (lead 30%) and final 560 words (tail 70%).
- **Generation Parameters:** `num_beams=4`, `length_penalty=2.0`, `no_repeat_ngram_size=3`, `max_length=350`, `min_length=80`.

### Component 5: Grounding & Validation Agent (`ValidationAgent`)
- **Module:** [agents/validator.py](file:///c:/Users/sujat.MANVITH/OneDrive/Desktop/antigravity/Legal-Document-Summarization/agents/validator.py)
- **Mechanism:** Deterministic verification against the source judgment.
- **Checks Performed:**
  - **Entity Grounding:** Extracts all dates (e.g., *14.05.2018*, *August 12, 2021*) and statutory sections (e.g., *Section 11B*, *Article 226*) in the summary and checks if they exist in the source document.
  - **Coverage Score:** Percentage of essential legal components (Parties, Sections, Ratio, Disposition) reflected in the summary.
  - **Factual Consistency Score:** Heuristic measure penalizing ungrounded claims.
  - **Status Grading:** `PASSED`, `WARNING`, or `FAILED`.

---

## 3. LangGraph Orchestration & State Machine
The entire flow is implemented as a directed acyclic graph using LangGraph's `StateGraph`:
- **State Schema:** Defined in [workflow/state.py](file:///c:/Users/sujat.MANVITH/OneDrive/Desktop/antigravity/Legal-Document-Summarization/workflow/state.py) (`LegalWorkflowState` TypedDict).
- **Audit Tracking:** Implemented in [workflow/audit.py](file:///c:/Users/sujat.MANVITH/OneDrive/Desktop/antigravity/Legal-Document-Summarization/workflow/audit.py), logging ISO timestamps, latencies, and stage statuses into the state dictionary.
- **Execution Graph:** [workflow/graph.py](file:///c:/Users/sujat.MANVITH/OneDrive/Desktop/antigravity/Legal-Document-Summarization/workflow/graph.py) connects:
  `extract_pdf` ──► `analyze_document` ──► `reason_legal_doctrine` ──► `summarize_bart` ──► `validate_summary`
