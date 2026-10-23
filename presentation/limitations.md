# Project Limitations, Ethical Risks, and Future Directions

## 1. Technical & Architectural Limitations

### 1.1 Context Window & Sequence Length Constraints
- **Limitation:** The base neural summarizer (`facebook/bart-base`) is architecturally bounded by an input context window of **1,024 tokens**.
- **Current Mitigation:** We employ an 800-word **tail-aware trimming heuristic** (preserving the initial 30% facts and final 70% holding).
- **Residual Risk:** For extraordinarily complex judgments spanning multiple procedural issues (e.g., 50+ page Constitutional Bench decisions), substantive intermediate arguments between pages 10 and 40 are omitted from BART's neural attention budget.

### 1.2 Evaluation Sample Size Disclosure
- **Limitation:** The official CivilSum test split contains **1,167 court cases**. Generating beam search summaries across the entire test set on a single laptop GPU requires several hours.
- **Scope Disclosed:** In adherence to research integrity, the evaluation reported in [evaluation_results.json](file:///c:/Users/sujat.MANVITH/OneDrive/Desktop/antigravity/Legal-Document-Summarization/evaluation_results.json) was conducted on **50 randomly sampled test cases** (ROUGE-1: 37.39, ROUGE-2: 14.31, ROUGE-L: 24.62).
- **Future Work:** Running distributed batch generation on multi-GPU server infrastructure to evaluate all 1,167 test samples.

### 1.3 Optical Character Recognition (OCR) Dependency
- **Limitation:** Indian court orders from earlier decades or district courts are often provided as scanned, low-resolution image PDFs.
- **Current Scope:** The `PDFExtractorAgent` relies on native digital PDF text extraction via `PyPDF`. Scanned image-only PDFs without an embedded text layer yield empty strings.
- **Future Work:** Integrating an OCR pipeline (e.g., Tesseract or Surya OCR) with judicial layout analysis.

---

## 2. Hallucination Risks & Legal Domain Vulnerabilities

### 2.1 The Inversion Risk (Appeal Allowed vs. Dismissed)
- In standard summarization, a 95% accurate summary is acceptable. In legal decisions, missing a single negation (*"We find no merit in the appeal and accordingly allow the appeal"* vs *"dismiss the appeal"*) completely inverts the legal reality.
- **Mitigation Implemented:** The `ValidationAgent` scans the generated summary against the extracted `court_holding_and_disposition` from the legal reasoner agent to detect conflicting dispositions.

### 2.2 Statutory Citation Grounding
- Generative models occasionally cite adjacent or familiar statutory sections (e.g., citing *Section 10* instead of *Section 9* of the Code of Civil Procedure).
- **Mitigation Implemented:** Deterministic regex parsing flags any statutory section appearing in the summary that is not verbatim grounded in the primary text.

---

## 3. Legal & Ethical Disclaimers
1. **Not a Substitute for Legal Counsel:** The application is an analytical assistive tool designed for legal researchers, law students, and legal professionals. It does not provide formal legal advice or substitute for human legal representation.
2. **Jurisdiction Specificity:** The fine-tuned model weights are adapted specifically to the terminology and style of the **Supreme Court of India and Indian High Courts** (Civil decisions). Performance on criminal jurisprudence or foreign common-law jurisdictions (e.g., US, UK, EU courts) has not been benchmarked.
3. **Licensing:** The CivilSum dataset is governed by the **CC BY-NC-SA 4.0** license, restricting commercial use of models derived strictly from the dataset.

---

## 4. Future Enhancements

| Timeline | Planned Enhancement | Technical Path |
| :--- | :--- | :--- |
| **Short Term** | Full Test Split Evaluation | Run overnight batch evaluation over all 1,167 held-out CivilSum test cases. |
| **Medium Term** | Long-Context Transformer Upgrade | Evaluate `allenai/led-base-16384` (Longformer Encoder-Decoder) to ingest 16,384 tokens natively without trimming. |
| **Medium Term** | Multi-Jurisdiction Support | Fine-tune on Indian criminal decisions (*IN-Abs* dataset) and US Supreme Court cases (*CourtListener*). |
| **Long Term** | Retrieval-Augmented Verification (RAG) | Connect validation agent to live Indian Kanoon / Supreme Court digital case registries to verify citation status (overruled vs good law). |
