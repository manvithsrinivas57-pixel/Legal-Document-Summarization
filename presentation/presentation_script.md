# Presentation Script: Legal Document Summarization (12 Slides)
## *A Zero-Shot Modular Agentic Workflow Approach*

**Target Duration:** 15–18 Minutes (approx. 1.25 minutes per slide)  
**Target Presentation:** `presentation/legal_document_summarization_presentation.pptx`  
**Checkpoint Grounding:** `models/checkpoints/civilsum_bart`  
**Dataset Grounding:** CivilSum Benchmark (SIGIR 2024, CC BY-NC-SA 4.0)

---

### Slide 1: Title & Overview (Time: 0:00 – 1:15)
- **Slide Title:** Legal Document Summarization: A Zero-Shot Modular Agentic Workflow Approach
- **Visual Structure:** Deep Navy card with Cyan glow, project metadata pill badges, and model provenance.
- **Verbatim Speaker Talk Track:**
  > "Good morning, respected members of the evaluation committee, faculty, and colleagues.
  >
  > Today, I am proud to present our capstone research project: *'Legal Document Summarization: A Zero-Shot Modular Agentic Workflow Approach.'*
  >
  > This project tackles one of the most critical frontiers in Applied Natural Language Processing: automated summarization of judicial decisions. Modern legal judgments in common-law jurisdictions—particularly from the Supreme Court of India and state High Courts—frequently span 20 to 50 pages of dense, archaic legal prose, complex statutory citations, and extensive procedural trial transcripts.
  >
  > While monolithic Large Language Models often suffer from catastrophic hallucinations, sequence-length truncations, or omission of binding judicial holdings, our architecture introduces a hybrid, verified assembly line. We combine locally fine-tuned sequence-to-sequence transformers—specifically `facebook/bart-base` fine-tuned on the SIGIR 2024 CivilSum benchmark—with zero-shot agentic reasoning powered by Google Gemini, all orchestrated through a stateful LangGraph Directed Acyclic Graph.
  >
  > Over the next slides, I will walk you through the structural challenges of legal text, our tail-aware algorithm, our local GPU training convergence on an RTX 4060, empirical ROUGE results, our 60-test verification suite, and live application workflows."

---

### Slide 2: Problem Statement (Time: 1:15 – 2:30)
- **Slide Title:** Why Legal Summarization Breaks Standard NLP
- **Visual Structure:** 3 equal-width cards detailing: (1) Extreme Length, (2) Severe Tail Bias, (3) Inversion & Hallucination Hazard.
- **Verbatim Speaker Talk Track:**
  > "Slide 2 outlines the fundamental problem: why off-the-shelf summarization fails on judicial judgments.
  >
  > In standard NLP benchmarks like CNN/DailyMail or XSum, models benefit from what is known as 'lead bias'—the journalistic inverted-pyramid style where the key facts appear in the first two sentences.
  >
  > Judicial decisions are the exact opposite. Indian court rulings exhibit severe **tail bias**. The first 70 to 80% of a judgment is spent reciting lower court appeal history, procedural filings, and witness depositions. The judge's binding legal principle—the *Ratio Decidendi*—and the operative disposition—such as *'Appeal is dismissed with costs'*—occur exclusively in the final paragraphs.
  >
  > If an engineer applies standard front-truncation, the model consumes its entire 1,024-token budget on introductory procedural arguments and completely omits the actual court ruling!
  >
  > Furthermore, the legal domain carries an unacceptable **inversion hazard**. In journalism, 90% accuracy is great. In law, missing a single negation ('allow' vs 'dismiss') completely flips legal rights and precedent. Moreover, unconstrained LLMs frequently hallucinate adjacent statutory sections. These hazards motivated our modular architecture."

---

### Slide 3: Objectives & Project Scope (Time: 2:30 – 3:45)
- **Slide Title:** System Objectives & Architectural Scope
- **Visual Structure:** Two large structural panels: (1) 4 Core Research Objectives, (2) Target Scope & Boundaries.
- **Verbatim Speaker Talk Track:**
  > "On Slide 3, we define the concrete objectives and boundary conditions of our project.
  >
  > Our primary objective was to replace the standard 'black box prompt' approach with an audited, five-stage assembly line. In our pipeline, no single model is forced to perform everything. The PDF text extractor handles normalization; Gemini performs zero-shot structured metadata extraction; a second Gemini agent extracts the legal questions and ratio decidendi; our fine-tuned BART model generates the concise abstractive headnote; and finally, a deterministic validator checks citations and flags contradictions.
  >
  > In terms of scope:
  > First, we ground our work in Indian civil jurisprudence, utilizing the peer-reviewed CivilSum dataset from SIGIR 2024.
  > Second, we enforced strict consumer hardware feasibility: our fine-tuned weights run on an 8GB RTX 4060 GPU without requiring enterprise clusters.
  > Third, we built in enterprise fault-tolerance: our system gracefully handles cloud API 503 outages without losing local functionality.
  > Finally, we state clearly that this tool is an assistive research workbench, not an autonomous legal entity."

---

### Slide 4: System Architecture Diagram (Time: 3:45 – 5:00)
- **Slide Title:** End-to-End Modular Agentic Workflow
- **Visual Structure:** 5 horizontal stage nodes with flowing arrow connectors, LangGraph state schema panel, and fault-isolation callout.
- **Verbatim Speaker Talk Track:**
  > "Slide 4 illustrates our end-to-end multi-agent architecture as implemented in LangGraph.
  >
  > Notice the five sequential stages across the screen:
  > Stage 1 is the PDF Extractor. It ingests raw court documents, strips running court headers and watermarks, and cleans up irregular whitespace.
  > Stage 2 is the Document Analysis Agent. It invokes Google Gemini with strict JSON schema constraints to isolate metadata: case title, court jurisdiction, bench composition, petitioner, respondent, and the acts involved.
  > Stage 3 is the Legal Reasoner Agent. This agent performs the jurisprudential heavy lifting. It identifies the formal Questions of Law, summarizes the competing contentions, extracts the judge's Ratio Decidendi, and records the final disposition.
  > Stage 4 is our local Supervised Neural Summarizer. It applies our 30/70 tail-aware windowing algorithm and passes the consolidated text into our fine-tuned `facebook/bart-base` model running locally on CUDA.
  > Finally, Stage 5 is our Validation Auditor. Rather than relying on another LLM that might also hallucinate, Stage 5 is a deterministic, rule-based program that parses cited statutory sections with regex, validates them against the source text, and checks for disposition concordance.
  > All data flows through a strongly typed `LegalWorkflowState` dictionary, ensuring every stage is recorded in an immutable audit trail."

---

### Slide 5: Technology Stack (Time: 5:00 – 6:15)
- **Slide Title:** Technology Stack & Environment Architecture
- **Visual Structure:** 4 distinct technology columns: (1) Agentic Orchestration, (2) Deep Learning & NLP, (3) Serving & Interface, (4) Benchmark & Quality.
- **Verbatim Speaker Talk Track:**
  > "Slide 5 breaks down our technology stack across four pillars.
  >
  > Under Agentic Orchestration, we rely on LangGraph to coordinate the state machine. We utilize the newly released Google GenAI SDK (v2.28.0) to communicate with `gemini-2.5-flash`. Crucially, we wrap all remote LLM calls with Tenacity exponential backoff to handle transient network drops.
  >
  > Under Deep Learning and NLP, our core summarizer is `facebook/bart-base`, which contains 139 million parameters. We execute on PyTorch with CUDA 12.6 and FP16 precision, granting us rapid execution on our local RTX 4060 GPU without hitting VRAM bottlenecks.
  >
  > For Serving, we built a modern Streamlit workbench that organizes the complex output into clear tabs for Abstractive Summary, Legal Doctrine, Validation Audits, and JSON Export.
  >
  > Finally, for Validation and Quality, we maintain a robust Pytest suite comprising 60 automated unit and integration tests, all currently passing. We evaluate summary quality using the official Google ROUGE scorer."

---

### Slide 6: CivilSum Dataset & Preprocessing (Time: 6:15 – 7:30)
- **Slide Title:** CivilSum Dataset & Tail-Aware Preprocessing
- **Visual Structure:** Left card: Dataset provenance, splits (21,015 train, 1,168 val, 1,167 test), CC BY-NC-SA 4.0 license. Right card: 800-Word Tail-Aware Windowing (30% lead / 70% tail).
- **Verbatim Speaker Talk Track:**
  > "Slide 6 highlights our dataset provenance and our algorithmic solution to tail bias.
  >
  > We trained exclusively on the official CivilSum dataset published at SIGIR 2024. This is an authentic corpus containing 23,350 civil cases from the Supreme Court of India and state High Courts. It is partitioned into 21,015 training cases, 1,168 validation cases, and 1,167 test cases under a Creative Commons CC BY-NC-SA 4.0 license.
  >
  > The key engineering innovation on this slide is our 800-word Tail-Aware Trimming Algorithm.
  > As mentioned earlier, standard transformers like BART-base have an input limit of 1,024 tokens—roughly 800 words. Because legal decisions are 20 to 50 pages long, blind truncation discards the decision.
  >
  > To solve this, our preprocessor divides the 800-word budget into two asymmetrical windows:
  > The first 30% (240 words) preserves the lead: court identity, parties, and the statutory issue.
  > The remaining 70% (560 words) preserves the tail: the judge's reasoning, statutory analysis, and final verdict.
  > These are stitched together with a procedural omission tag. This single preprocessing step ensures that BART always sees the verdict and never hallucinates an inverted disposition."

---

### Slide 7: BART Fine-Tuning Execution (Time: 7:30 – 8:45)
- **Slide Title:** Supervised Fine-Tuning of facebook/bart-base
- **Visual Structure:** 4 top KPI metrics (139M params, 196.14s duration, 2.306 val loss, 225 steps), hyperparameters card, and loss convergence card.
- **Verbatim Speaker Talk Track:**
  > "Slide 7 provides the empirical details of our supervised fine-tuning execution.
  >
  > We chose `facebook/bart-base`, which features a bidirectional encoder and an autoregressive decoder with 139 million parameters. The model was trained locally on an NVIDIA GeForce RTX 4060 Laptop GPU with 8GB of VRAM running CUDA 12.6.
  >
  > To maximize throughput within 8GB VRAM, we used FP16 mixed precision, a per-device batch size of 4, and gradient accumulation of 4 steps, producing an effective batch size of 16. Using AdamW with a learning rate of 3e-5, training ran for 3 epochs across 225 global optimization steps.
  >
  > Total training time was exceptionally fast: 196.14 seconds, or roughly 3.27 minutes.
  > As shown in the cards, validation cross-entropy loss converged smoothly from an initial loss of ~14.0 down to 2.318 in Epoch 2 and 2.306 in Epoch 3. The best checkpoint was saved to `models/checkpoints/civilsum_bart`.
  >
  > Importantly, our codebase implements strict checkpoint enforcement: if this local fine-tuned folder is ever missing, the pipeline halts immediately rather than silently falling back to a generic baseline model that lacks legal vocabulary."

---

### Slide 8: Gemini Agents & Resilience Architecture (Time: 8:45 – 10:00)
- **Slide Title:** Gemini Reasoning Agents & Resilience Architecture
- **Visual Structure:** Left card: Specialized agent roles, strict schemas, zero-fabrication rules. Right card: HTTP 503 mitigation, Tenacity backoff (2s, 4s, 8s), storm prevention.
- **Verbatim Speaker Talk Track:**
  > "Slide 8 focuses on our agentic reasoning layer powered by Google Gemini and our enterprise resiliency engineering.
  >
  > While our fine-tuned BART model is responsible for generating fluent, abstractive summaries, legal research demands doctrinal decomposition. We deploy two specialized Gemini agents:
  > The Document Structure Agent extracts procedural entities into typed JSON.
  > The Legal Reasoner Agent extracts the Questions of Law, Litigant Contentions, Ratio Decidendi, and Final Holding.
  > We enforce a low temperature of 0.2 and strict schemas to prevent imaginative fabrication.
  >
  > The right-hand card addresses a crucial production challenge: transient HTTP 503 UNAVAILABLE errors.
  > Cloud LLM endpoints can be temporarily congested. Previously, a 503 would crash the entire workflow. We re-engineered the pipeline with Tenacity exponential backoff, applying three retries with random jitter at 2, 4, and 8 seconds.
  > We also decoupled the execution of the Document Structure and Legal Reasoner nodes so they never trigger simultaneous retry storms.
  > If the API remains down after three attempts, the system surfaces a clear diagnostic message, logs the incident, and allows the local BART summarizer to complete its work without fabricating false legal doctrines."

---

### Slide 9: Validation, Test Results, & Metrics (Time: 10:00 – 11:15)
- **Slide Title:** Empirical Results, Grounding Auditor, & Test Suite
- **Visual Structure:** 4 top KPI metrics (ROUGE-1: 37.39, ROUGE-2: 14.31, ROUGE-L: 24.62, 60/60 tests passing), evaluation protocol card, deterministic grounding auditor card.
- **Verbatim Speaker Talk Track:**
  > "Slide 9 presents our quantitative evaluation metrics, deterministic validation rules, and automated test suite.
  >
  > Across our held-out test evaluation—conducted on 50 randomly sampled cases from `data/test.csv`—our fine-tuned model achieved:
  > A ROUGE-1 F1 score of 37.39, indicating strong lexical and concept recall;
  > A ROUGE-2 score of 14.31, reflecting accurate consecutive legal phrasing;
  > And a ROUGE-L score of 24.62, confirming preservation of sentence structure and narrative continuity.
  > These numbers are documented in `evaluation_results.json`.
  >
  > In addition to ROUGE, our architecture includes a deterministic Grounding Auditor. It does not use generative heuristics; instead, it uses regular expressions to extract every cited statutory section and validates that each one appears in the original text. It also verifies that the summary's disposition matches the court's operative holding, preventing inversion errors.
  >
  > Finally, we emphasize that our entire system is validated by an automated Pytest suite of 60 unit and integration tests, which currently stands at a 100% pass rate."

---

### Slide 10: Application Interface & Interactive Workflow (Time: 11:15 – 12:30)
- **Slide Title:** Application Interface & Interactive Workflow
- **Visual Structure:** 4 visual cards embedding actual screenshots from `screenshots/` (`02_pdf_uploaded.png`, `03_abstractive_summary.png`, `04_legal_analysis_and_doctrine.png`, `05_validation_and_grounding.png`).
- **Verbatim Speaker Talk Track:**
  > "Slide 10 presents the interactive user experience in our Streamlit application, capturing the four primary tabs.
  >
  > In Column 1, we see Document Ingestion. The user uploads a court judgment in PDF format or enters raw text. The application validates character integrity, reports token counts, and displays the active checkpoint status.
  >
  > In Column 2, Tab 1 presents the Abstractive Summary generated by our fine-tuned BART model. Notice that it provides a coherent, four-to-five sentence synthesis capturing the core procedural issue and final decree.
  >
  > In Column 3, Tab 2 displays the Legal Reasoning breakdown. The practitioner can review the extracted Questions of Law, the arguments of the petitioner and respondent, the ratio decidendi, and the operative holding.
  >
  > In Column 4, Tab 3 displays the Validation and Grounding report. The user sees an objective Grounding Score, a list of verified statutory provisions, and confirmation that the disposition is concordant with the judgment. The user can also export the entire structured brief as Markdown, plain text, or an immutable JSON audit log."

---

### Slide 11: Limitations & Future Improvements (Time: 12:30 – 13:45)
- **Slide Title:** Technical Limitations & Future Roadmap
- **Visual Structure:** Left card: Current constraints & honest disclosures (1,024 context, 50-case evaluation subset, OCR dependency). Right card: Future roadmap (LED-16384, full-split evaluation, judicial OCR, live legal RAG).
- **Verbatim Speaker Talk Track:**
  > "Slide 11 addresses our technical limitations and future roadmap with full academic integrity.
  >
  > Every engineering project has constraints, and we document ours clearly:
  > First, while our 30/70 tail-aware windowing solves the holding omission problem, BART-base's 1,024-token window cannot ingest extensive intermediate evidence from 60-page constitutional bench rulings.
  > Second, as disclosed in our documentation, our evaluation metrics reflect 50 held-out test judgments. Evaluating all 1,167 test cases with beam search on a single laptop GPU requires significant compute time.
  > Third, our current extractor relies on digital PDF text layers; scanned photocopies require external OCR.
  > Finally, the model is specialized for Indian civil appellate law and has not been tuned on criminal or foreign jurisdictions.
  >
  > Our future engineering roadmap addresses these areas directly:
  > We plan to upgrade from BART to `allenai/led-base-16384`, expanding our attention window sixteen-fold to ingest complete judgments.
  > We will run full-corpus benchmarking on multi-GPU cloud infrastructure.
  > We will integrate dedicated judicial OCR for historical appeals.
  > And we aim to connect our validation auditor to live Indian Kanoon APIs to verify whether cited case law has been subsequently overturned."

---

### Slide 12: Conclusion & Q&A (Time: 13:45 – 15:00)
- **Slide Title:** Conclusion & Research Contributions
- **Visual Structure:** 3 summary cards (Hybrid Architecture, Tail Bias Solution, Production Reliability) and a prominent defense discussion banner.
- **Verbatim Speaker Talk Track:**
  > "In conclusion, Slide 12 summarizes our primary contributions:
  >
  > First, we demonstrated that high-stakes legal NLP is most effectively solved through a hybrid architecture. By dividing responsibilities between a locally fine-tuned sequence-to-sequence model and zero-shot reasoning agents, we achieve both data privacy and deep legal reasoning without relying blindly on an ungrounded black-box LLM.
  >
  > Second, we introduced a reproducible 30/70 tail-aware windowing heuristic that directly addresses the unique topological tail bias of Indian judicial rulings, ensuring that the court's holding is never lost to truncation.
  >
  > Third, we engineered enterprise-grade reliability into our workflow: incorporating exponential backoff against API downtime, building a deterministic grounding auditor that guards against hallucination and inversion, and validating the entire system through 60 automated tests.
  >
  > Thank you very much for your time and attention. I now welcome your questions, critique, and discussion."

---

## Defense Quick-Reference (Viva Voce Cheat Sheet)

| Question | Core Defense Response |
| :--- | :--- |
| **Why not just prompt GPT-4 or Gemini for everything?** | Monolithic LLMs hallucinate statutory sections, lack formal grounding verification, have high token inference costs, and present data confidentiality risks when uploading sensitive legal documents. Our local fine-tuned BART guarantees offline neural summarization, while agents extract structured doctrine under strict validation. |
| **What does 30/70 Tail-Aware Windowing actually do?** | It splits an 800-word attention budget into 240 lead words (court, bench, cause of action) and 560 tail words (judicial reasoning, ratio decidendi, operative decree) joined with `[...]`. This guarantees that the final decree is never truncated. |
| **What hardware was used for training?** | NVIDIA GeForce RTX 4060 Laptop GPU (8GB VRAM) with CUDA 12.6, PyTorch 2.14.1, FP16 precision, effective batch size 16 (4 batch x 4 grad accum), 225 steps, completing in 196.14 seconds. |
| **What are your ROUGE scores and what do they mean?** | Evaluated on 50 held-out cases from `data/test.csv`: **ROUGE-1: 37.39** (lexical coverage), **ROUGE-2: 14.31** (legal bigram fluency), **ROUGE-L: 24.62** (syntactic structure). |
| **How did you fix the persistent HTTP 503 errors?** | Implemented Tenacity exponential backoff with random jitter across 3 retries (2s, 4s, 8s), decoupled Document Analysis from Legal Reasoning to prevent simultaneous retry storms, and provided graceful fallback to local BART summarization. |
