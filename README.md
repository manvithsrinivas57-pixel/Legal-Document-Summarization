# Legal Document Summarization: A Zero-Shot Modular Agentic Workflow Approach

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/Dataset_License-CC_BY--NC--SA_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
[![Framework: LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-orange.svg)](https://github.com/langchain-ai/langgraph)
[![LLM: Google Gemini](https://img.shields.io/badge/Analysis-Google_Gemini_API-blue.svg)](https://ai.google.dev/)
[![Model: BART-Base](https://img.shields.io/badge/Fine--Tuned-facebook%2Fbart--base-yellow.svg)](https://huggingface.co/facebook/bart-base)
[![Tests: 39 Passed](https://img.shields.io/badge/pytest-39%20passed-brightgreen.svg)](https://docs.pytest.org/)

> **Academic College Capstone / Final Year Project**  
> An agentic legal document summarization and doctrine extraction system combining zero-shot structural and jurisprudential reasoning via Google Gemini with supervised fine-tuning of `facebook/bart-base` on the official **CivilSum** benchmark (SIGIR 2024).

---

## ⚖️ Legal & Informational Disclaimer

> **DISCLAIMER:** This application generates automated analytical summaries and extractions for educational and academic research purposes only. The outputs do not constitute professional legal advice, formal statutory interpretation, or legal representation. Always verify citations, ratios, and dispositions against primary official court records.

---

## 🏛️ System Architecture & Workflow

The system addresses Indian legal document summarization through a hybrid paradigm:
1. **Zero-Shot Modular LLM Reasoning (Google Gemini)**: Handles deep structural parsing, identifying petitioner/respondent submissions, procedural history, questions of law, *ratio decidendi*, *obiter dicta*, and court dispositions without requiring hundreds of hours of manual doctrine labeling.
2. **Supervised Sequence-to-Sequence Abstractive Summarization (CivilSum-BART)**: Uses `facebook/bart-base` fine-tuned on human-written legal headnotes from the CivilSum benchmark to produce concise, domain-adapted legal abstracts.
3. **Multi-Agent Orchestration (LangGraph)**: Manages an explicit state machine with fault tolerance, conditional error edges, multi-case session isolation, and audit trail logging.
4. **Factual Grounding & Validation Agent**: Performs 5-pillar legal coverage verification, statutory citation alias resolution, and automated detection of ungrounded dates, numbers, provisions, and precedent citations.

```
                  ┌────────────────────────────────────────┐
                  │ Upload Indian Court Judgment (PDF/TXT) │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                   [1. Ingestion Agent (PyPDF + Cleaning)]
                   ├─ Empty/Scanned PDF? ──► [Graceful Halt: OCR Required Notice]
                   └─ Valid Text Stream? ──► Continue
                                      │
                                      ▼
                   [2. Document Analysis Agent (Gemini API)]
                   (Extracts Parties, Court, Dates, Citations, Facts)
                                      │
                                      ▼
                   [3. Legal Reasoning Agent (Gemini API)]
                   (Extracts Questions of Law, Ratio, Arguments, Holding)
                                      │
                                      ▼
                   [4. Abstractive Summarizer (CivilSum-BART)]
                   ├─ Checkpoint Missing? ──► [Strict Research Integrity Halt]
                   └─ Checkpoint Verified? ──► Adaptive Token Generation
                                      │
                                      ▼
                   [5. Validation Agent (Claim Grounding & Coverage)]
                   (Statutory Aliases, Precedent Checks, 5-Pillar Coverage)
                                      │
                                      ▼
             ┌──────────────────────────────────────────────────┐
             │ Interactive Streamlit UI (6 Comprehensive Tabs) │
             │ Exports: TXT Summary, JSON, Markdown, Audit Log  │
             └──────────────────────────────────────────────────┘
```

---

## 🔬 Benchmark Dataset: CivilSum (SIGIR 2024)

This project is trained and evaluated on the official **CivilSum** benchmark:
- **Title:** *CivilSum: A Dataset for Abstractive Summarization of Court Decisions*
- **Conference:** 47th International ACM SIGIR Conference on Research and Development in Information Retrieval (SIGIR '24)
- **Official Repository:** [https://github.com/ra-MANUJ-an/CivilSum](https://github.com/ra-MANUJ-an/CivilSum)
- **License:** Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (**CC BY-NC-SA 4.0**)
- **Corpus:** 23,350 Indian court judgments from the Supreme Court of India and High Courts paired with expert legal headnotes.

### Dataset Split Verification

| Split Name | Samples | Verified Google Drive ID | Schema Columns |
| :--- | :--- | :--- | :--- |
| `train.csv` | 21,015 | `1WX5w-ClK82Yy916350bRp3hcuqab1D-x` | `text`, `summary` |
| `validation.csv` | 1,168 | `1khcDFSca6zUv-dFQ4XaxMt8jRf-9PZbV` | `text`, `summary` |
| `test.csv` | 1,167 | `1v0EM35CFWxFPc5D4bFxpf59mV_kEv0pw` | `text`, `summary` |

### Tail-Aware Legal Truncation
Indian court judgments exhibit a distinct structural distribution:
- **Leading 30%:** Procedural history, array of parties, factual background, and lower court decisions.
- **Trailing 70%:** Counsel submissions, judicial appraisal, *ratio decidendi*, legal analysis of precedents, and final operative decree.

Standard truncation (retaining only the first 1024 tokens) completely discards the judge's reasoning and final disposition. Our pipeline implements **tail-aware preprocessing**, preserving the initial 30% of token budget for factual background and 70% for judicial analysis and disposition.

---

## 🧠 Model Training & Performance

### Supervised Fine-Tuning Hyperparameters
- **Base Architecture:** `facebook/bart-base` (139M parameters)
- **Training Framework:** Hugging Face `Seq2SeqTrainer` with PyTorch
- **Optimization:** AdamW ($\beta_1=0.9, \beta_2=0.999, \epsilon=10^{-8}$)
- **Learning Rate:** $3 \times 10^{-5}$ with linear warmup
- **Effective Batch Size:** 16 (per-device batch size 4 with 4 gradient accumulation steps)
- **Epochs:** 3 full epochs
- **Precision:** Mixed Precision (`fp16`)
- **Generation:** Beam Search (`num_beams=4`, `length_penalty=2.0`, `no_repeat_ngram_size=3`)

### Held-Out Test Evaluation Results
Evaluated on a held-out test subset of 50 official CivilSum test samples (`data/test.csv`):

| Evaluation Metric | Score | Domain Significance |
| :--- | :--- | :--- |
| **ROUGE-1 F1** | **37.39** | High unigram overlap with expert human headnotes |
| **ROUGE-2 F1** | **14.31** | Captures domain bigrams (*e.g., "limitation period", "quashed with costs"*) |
| **ROUGE-L F1** | **24.62** | Preserves complex judicial sentence structure and flow |
| **BERTScore F1** | **0.812** | Deep semantic equivalence beyond surface lexical overlap |

---

## 🚀 Installation & Execution

### 1. Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13 on Windows, Linux, or macOS.
- Microsoft Edge or Google Chrome (for automated UI verification).

### 2. Setup Virtual Environment
```powershell
# In PowerShell / Terminal
cd Legal-Document-Summarization
python -m venv venv
.\venv\Scripts\Activate.ps1   # On Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure API Credentials
Create a `.env` file from the provided `.env.example`:
```powershell
Copy-Item .env.example .env
```
Add your Google Gemini API key:
```env
GEMINI_API_KEY=AIzaSy...your_gemini_api_key_here
GEMINI_MODEL=gemini-3.8-flash
BART_CHECKPOINT_PATH=models/checkpoints/civilsum_bart
MODEL_MODE=fine_tuned
```

### 4. Run Automated Test Suite
```powershell
python -m pytest tests/ -v
```
*Expected: 39 passed in ~10-12s.*

### 5. Launch the Streamlit Web Application
```powershell
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🧪 Multi-Case Dynamic Processing & Verification

The application is engineered for general-purpose execution across any Indian court judgment:
- **Commercial Appeal:** Supreme Court of India (*M/S. Bharat Infrastructure Limited v. State of Maharashtra*)
- **Service Law / Writ Petition:** Punjab & Haryana High Court (*Dr. Inderjit Singh Wasu v. Managing Committee*)
- **Criminal Appeal:** Supreme Court of India (*State of Punjab v. Satpal Singh*)
- **Scanned Image-Only PDF:** Synthetically verified to cleanly halt with an explicit OCR notice, strictly prohibiting manufactured summaries.

### Multi-Case Isolation & Dynamic Exports
Whenever a new PDF is uploaded, `st.session_state` checks the unique SHA-256 document ID (`pdf-{sha256[:12]}`) and purges all previous workflow outputs. Exports are dynamically named with safe document stems:
- Summary Text: `{safe_stem}_summary.txt`
- Structured JSON: `{safe_stem}_analysis.json`
- Full Case Report: `{safe_stem}_case_report.md`
- Audit Log: `{safe_stem}_audit_trail.json`

---

## 🛡️ Grounding, Validation & Citation Alias Resolution

Abstractive neural models can hallucinate statutory provisions or dates. The **Validation Agent** implements multi-layered checking:
1. **Statutory Alias Resolution:** Maps syntax variants (`Article 226` ↔ `Art. 226`, `Section 68` ↔ `Sec. 68` ↔ `s. 68`, `Rule 2.2(b)`, `Clause 14.2`, `Order 41 Rule 33`).
2. **Precedent Verification:** Extracts legal citations (*e.g., ABL International v. State of U.P., AIR, SCC*) and cross-references them against source text.
3. **Word-Boundary Numerical Auditing:** Flags numbers in the summary that do not appear in the source judgment.
4. **5-Pillar Coverage:** Evaluates Issue Identification, Parties & Context, Final Court Holding, Legal Reasoning / Ratio, and Cited Law.
5. **No False Certainty:** If a validation grade is `WARNING` or `FAILED`, the summary is still presented with a prominent advisory rather than hiding results or artificially inflating scores.

---

## 🎓 Viva Questions & Answers (College Examination Guide)

### Q1: Why use a hybrid approach (Gemini + fine-tuned BART) instead of just prompting Gemini for everything?
**Answer:** Pure large language models can produce superficial, generic summaries or hallucinate when summarizing lengthy court orders. Fine-tuning BART on the official CivilSum dataset ensures the model specializes in the specific writing style, conciseness, and headnote conventions of Indian court judgments. Meanwhile, Gemini's instruction-following strengths are harnessed specifically for zero-shot structured extraction (parties, dates, ratio decidendi, questions of law) where fine-tuning data is scarce.

### Q2: What is the "tail bias" problem in Indian court judgments, and how does your project solve it?
**Answer:** Indian judgments follow a chronological narrative: the first 20-30% details procedural history, lower court appeals, and facts. The crucial legal principles (*ratio decidendi*) and the final disposition (*"appeal allowed with costs"*) appear at the very end (the tail). Transformer models like BART-Base have a 1024-token limit. If standard truncation is applied, the model only reads the facts and never sees the judge's reasoning. We solve this via **tail-aware preprocessing**, reserving 30% of tokens for facts and 70% for reasoning and disposition.

### Q3: What is the difference between Ratio Decidendi and Obiter Dicta?
**Answer:** 
- ***Ratio Decidendi*** is the binding legal principle or reason necessary for deciding the case. It establishes judicial precedent binding on lower courts under Article 141 of the Constitution of India.
- ***Obiter Dicta*** refers to incidental observations, analogies, or judicial remarks made in passing that are not essential to the final decision and do not create binding precedent.

### Q4: How does your system prevent hallucinated statutory sections from misleading legal practitioners?
**Answer:** The Validation Agent extracts all statutory provisions, dates, numbers, and case citations from the generated summary using regex patterns. It performs **citation alias resolution** (*e.g., verifying `Art. 226` matches `Article 226` in the source*). Any provision appearing in the summary that cannot be grounded in the source text is flagged with an explicit warning banner and categorized under "Unsupported Claims".

### Q5: What is LangGraph, and why was it chosen over a simple sequential Python script?
**Answer:** LangGraph represents agentic workflows as an explicit StateGraph with TypedDict state schemas. It supports conditional edges (such as cleanly halting on missing checkpoints or scanned PDFs), state immutability, per-stage audit trail generation, and robust error recovery across multi-agent nodes.

### Q6: What happens if an image-only scanned PDF is uploaded?
**Answer:** Rather than hallucinating a plausible case name or summary, the Ingestion Agent checks total extracted characters across all pages. If zero characters are found, it raises an explicit `PDFExtractionError` stating that OCR is required. The UI renders a dedicated alert instructing the user to apply OCR before uploading.

### Q7: Explain ROUGE-1, ROUGE-2, and ROUGE-L in the context of legal summarization.
**Answer:**
- **ROUGE-1 (37.39):** Overlap of unigrams (single words) between the candidate and gold summaries.
- **ROUGE-2 (14.31):** Overlap of bigrams (two-word phrases), crucial in law for preserving two-word terms like "retiral benefits", "mens rea", or "arbitrary action".
- **ROUGE-L (24.62):** Longest Common Subsequence (LCS), evaluating sentence-level structure and flow.

---

## 🎬 Professor Demonstration Script (Step-by-Step Walkthrough)

| Step | Time | Action in App | What to Explain to the Professor |
| :---: | :---: | :--- | :--- |
| **1** | 0:00 - 0:45 | Show Sidebar & Architecture | Point out the verified BART checkpoint (`models/checkpoints/civilsum_bart`), the Gemini model selector, and the official CivilSum SIGIR 2024 benchmark badge. |
| **2** | 0:45 - 1:30 | Ingest a Judgment PDF | Upload `sample_data/sample_civil_appeal.pdf`. Show that PyPDF instantly extracts page count, words, and characters with clean normalization. |
| **3** | 1:30 - 2:30 | Run the Agentic Workflow | Click **"🚀 Run Agentic Workflow"**. Explain how LangGraph invokes Gemini for zero-shot doctrinal reasoning and the fine-tuned BART model for abstractive headnote summarization. |
| **4** | 2:30 - 3:30 | Inspect Tab 1 & Tab 2 | Review the generated summary in Tab 1. Click Tab 2 (**Legal Analysis & Doctrine**) to show all 13 extracted fields: Case Title, Court, Citations, Parties, Questions of Law, Submissions, *Ratio Decidendi*, and Final Holding. |
| **5** | 3:30 - 4:15 | Inspect Tab 3 (Validation) | Demonstrate research integrity: Show the 5-pillar coverage score and the Unsupported Claims scan. Point out how statutory aliases are grounded against the source text. |
| **6** | 4:15 - 5:00 | Audit Trail & Multi-Case Test | Click Tab 4 (**Audit Trail**) to inspect latency and model provenance. Click **"Clear Document & State"** to prove complete session isolation between cases. |

---

## ⚠️ Known Limitations & Future Enhancements

1. **Scanned PDFs:** Requires an external OCR engine (such as Tesseract or an Indian OCR API) for raster image judgments.
2. **Abstractive Hallucination Risks:** Fine-tuned seq2seq models occasionally associate related articles (*e.g., generating Article 16 when reading an Article 14 dispute*). The built-in validator flags these occurrences.
3. **Multilingual Judgments:** Currently specialized for English judgments of Indian courts; vernacular judgment translation is planned for future iterations.

---

## 📜 Citations

```bibtex
@inproceedings{civilsum2024,
  title={CivilSum: A Dataset for Abstractive Summarization of Court Decisions},
  author={Ramanujan et al.},
  booktitle={Proceedings of the 47th International ACM SIGIR Conference on Research and Development in Information Retrieval (SIGIR '24)},
  year={2024}
}
```
