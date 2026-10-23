# Comprehensive Viva Voce Questions & Answers

### Q1: What is the main objective of this project?
**Answer:** To develop an automated legal document summarizer that combines zero-shot agentic reasoning (using Google Gemini) with a locally fine-tuned sequence-to-sequence model (`facebook/bart-base`) to extract structured legal doctrines and generate grounded, abstractive summaries of Indian court judgments.

### Q2: Why is legal document summarization harder than news summarization?
**Answer:** Legal judgments are significantly longer (often 20–50+ pages), contain dense statutory citations and complex syntax, and suffer from "tail bias", where the most crucial decision elements (holding and ratio decidendi) appear at the very end rather than at the beginning.

### Q3: What is "tail bias" in legal NLP?
**Answer:** In standard journalism, the key points appear in the lead paragraph (lead bias). In Indian court rulings, the judges dedicate the first 70–80% to procedural filings, trial notes, and arguments, placing the crucial legal reasoning and operative disposition in the final paragraphs (the tail).

### Q4: How does your system solve the tail bias problem?
**Answer:** We implement **tail-aware trimming**: instead of truncating from the start or end blindly, we extract an 800-word window composed of the lead 30% (case background and parties) and the tail 70% (arguments and final court holding).

### Q5: What base model was chosen for supervised fine-tuning and why?
**Answer:** `facebook/bart-base` (139M parameters). It utilizes a bidirectional encoder and an autoregressive decoder, making it well-suited for abstractive text generation, while being computationally efficient enough to train and deploy locally on consumer GPUs.

### Q6: What dataset was used for training and what is its license?
**Answer:** The official **CivilSum** dataset published at SIGIR 2024 by Ramanujan et al. It contains 23,350 Indian court cases (21,015 train, 1,168 validation, 1,167 test) under a Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0) license.

### Q7: On what hardware was the model fine-tuned?
**Answer:** On a local **NVIDIA GeForce RTX 4060 Laptop GPU** (8 GB VRAM) using CUDA 12.6, PyTorch `2.14.1+cu126`, and FP16 mixed precision.

### Q8: What were your fine-tuning hyperparameters?
**Answer:** 3 epochs, batch size of 4 with gradient accumulation of 4 (effective batch size of 16), AdamW optimizer with learning rate $3 \times 10^{-5}$, weight decay of $0.01$, and FP16 enabled.

### Q9: What was the training duration and loss convergence?
**Answer:** Training completed in **196.14 seconds (~3.27 minutes)** across 225 global optimization steps. Validation loss decreased across epochs down to **2.306**, and final step loss reached **9.852** (average training loss: 10.73).

### Q10: How did you evaluate the fine-tuned model?
**Answer:** Using the official ROUGE metrics on 50 held-out cases from `data/test.csv`. The model achieved:
- **ROUGE-1 F1:** **37.39**
- **ROUGE-2 F1:** **14.31**
- **ROUGE-L F1:** **24.62**

### Q11: What do ROUGE-1, ROUGE-2, and ROUGE-L measure?
**Answer:**
- **ROUGE-1:** Unigram (single word) overlap between generated and reference summaries.
- **ROUGE-2:** Bigram (two consecutive words) overlap, measuring phrasing and term accuracy.
- **ROUGE-L:** Longest Common Subsequence, measuring sentence structure and word order preservation.

### Q12: Why did you adopt a modular multi-agent workflow instead of end-to-end prompting?
**Answer:** End-to-end LLM prompting on long texts frequently misses operative rulings, loses specific statutory sections, and produces uncontrollable hallucinations. Modular decomposition isolates extraction, doctrine reasoning, neural summarization, and validation into verifiable, auditable stages.

### Q13: What is the role of LangGraph in your project?
**Answer:** LangGraph coordinates the workflow as a stateful directed acyclic graph (`StateGraph`). It passes a unified state dictionary (`LegalWorkflowState`) between agent nodes, handles conditional routing, and logs an immutable audit trail.

### Q14: What is the responsibility of the Document Analysis Agent?
**Answer:** To perform zero-shot extraction of basic case metadata: Case Title, Court Name, Petitioner, Respondent, Bench composition, Statutes Involved, and the factual dispute.

### Q15: What is the responsibility of the Legal Reasoner Agent?
**Answer:** To isolate jurisprudential components: formulated Questions of Law, counsel arguments, the *ratio decidendi* (legal justification), and the final court holding/disposition.

### Q16: What is the difference between Ratio Decidendi and Obiter Dicta?
**Answer:**
- ***Ratio Decidendi*** is the binding legal principle essential to reaching the decision in the case.
- ***Obiter Dicta*** refers to incidental judicial remarks, observations, or illustrations made by the judge that are not binding precedent.

### Q17: How does the Validation Agent detect hallucinations?
**Answer:** It extracts all dates, statutory sections (e.g., *Section 11B*), and constitutional articles from the summary and verifies deterministically whether those exact entities exist in the original source judgment. Any ungrounded entity is flagged as an unsupported claim.

### Q18: What is your strict Research Integrity policy regarding missing checkpoints?
**Answer:** If the local fine-tuned BART checkpoint is absent or corrupted, the system halts with a `CHECKPOINT_MISSING` status and explanation. It strictly refuses to fabricate fake summaries or silently substitute Gemini in place of BART.

### Q19: How are PDF files processed in the ingestion agent?
**Answer:** Using `pypdf` with regex post-processing to remove OCR artifacts, line breaks within statutory sections, header/footer page stamps, and courtroom stenographer formatting.

### Q20: What happens if the Gemini API key is missing?
**Answer:** The pipeline reports an explicit `API_KEY_MISSING` status for the analysis and reasoning stages. The BART neural summarizer can still execute independently if text is provided.

### Q21: What decoding strategy is used during inference in BART?
**Answer:** Beam search with `num_beams=4`, `length_penalty=2.0`, `no_repeat_ngram_size=3`, `min_length=80`, and `max_length=350`.

### Q22: Why use `no_repeat_ngram_size=3`?
**Answer:** To prevent repetitive loops and redundant legal phrasing (e.g., *"and the court held that the court held that..."*), common in autoregressive sequence-to-sequence decoding.

### Q23: How does the Streamlit UI handle model provenance?
**Answer:** Tab 5 ("Model & Training Status") displays the live checkpoint path, an on-disk verification badge, the hardware device, total training runtime, training loss, global steps, and the authentic held-out test evaluation scores.

### Q24: What export formats are supported?
**Answer:** Four formats: plain text summary (`.txt`), structured JSON containing all agent states (`.json`), comprehensive Markdown report (`.md`), and the workflow audit trail (`.json`).

### Q25: How does your system comply with legal tech ethical guidelines?
**Answer:** Every screen and exported report carries an explicit legal disclaimer stating that the system produces automated analytical summaries for educational/research purposes and does not constitute formal legal counsel or statutory advice.

### Q26: What are the main limitations of this system?
**Answer:** The BART context window is restricted to 1,024 tokens (mitigated by tail-aware trimming); OCR quality affects scanned PDFs; and the evaluation was performed on 50 test cases rather than the complete 1,167 CivilSum test set due to local inference time constraints.
