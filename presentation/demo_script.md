# 5-Minute Professor Demonstration Script

## Overview
This script outlines a concise, structured 5-minute live demonstration designed for academic evaluators, faculty reviewers, or viva committees.

---

## Pre-Demo Checklist (Do Before the Committee Arrives)
- [ ] Terminal launched and virtual environment active:
  ```powershell
  cd C:\Users\sujat.MANVITH\OneDrive\Desktop\antigravity
  streamlit run app.py
  ```
- [ ] Browser open to **`http://localhost:8501`**.
- [ ] Fine-tuned checkpoint verified (green badge in sidebar).
- [ ] Google Gemini API key entered in sidebar or verified in `.env`.

---

## 5-Minute Demonstration Timeline

### Minute 1: Introduction & Problem Statement (Tabs: Main Header & Tab 6)
- **What to say:**
  > *"Good morning, Professors. Today I am presenting 'Legal Document Summarization: A Zero-Shot Modular Agentic Workflow Approach'.*
  > *Legal court decisions in India often exceed 20 to 50 pages, with dense statutory citations and extreme 'tail bias'—where the crucial judicial holding is located at the very end.*
  > *Rather than using a single monolithic prompt, we built a 5-stage modular agentic pipeline using LangGraph that decouples extraction, jurisprudential doctrine reasoning, neural summarization, and hallucination validation."*
- **What to show:**
  - Show the clean header and the legal disclaimer banner.
  - Switch to **Tab 6 ("Research & Benchmark")** to show the **CivilSum (SIGIR 2024)** dataset credentials: 23,350 Indian court cases under CC BY-NC-SA 4.0.

---

### Minute 2: Verified Training Status & Hardware Provenance (Tab 5)
- **What to say:**
  > *"Before showing inference, I want to emphasize our adherence to research integrity.*
  > *In Tab 5, we verify our supervised fine-tuning of `facebook/bart-base` on local GPU hardware.*
  > *As shown in the metadata, the model was trained on an NVIDIA GeForce RTX 4060 Laptop GPU for 3 epochs (225 steps), achieving a validation loss of 2.306 in 3.27 minutes.*
  > *On 50 held-out test cases from the CivilSum test split, our fine-tuned model achieved a ROUGE-1 of 37.39 and ROUGE-L of 24.62, outperforming standard non-domain baselines."*
- **What to show:**
  - Click on **Tab 5 ("Model & Training Status")**.
  - Point to the **Checkpoint Verified** badge, the JSON training metadata card, and the ROUGE metric scorecards.

---

### Minute 3: Ingesting a Case & Running the Workflow (Tab 1)
- **What to say:**
  > *"Now let us demonstrate the live pipeline on an Indian appellate court case.*
  > *We can either upload a PDF court order or paste text. For this demo, let's load our benchmark Supreme Court civil appeal."*
- **What to do:**
  1. Return to the sidebar and click **"Load Sample Supreme Court Judgment"**.
  2. Switch to **Tab 1 ("Summarization & Pipeline")**.
  3. Show the loaded judgment text in the input area.
  4. Click the blue **"🚀 Run Agentic Workflow"** button.
  5. The pipeline runs through all 5 stages in ~10–12 seconds.
- **What to say:**
  > *"The pipeline completes in about 12 seconds. Here is the final abstractive summary produced by our locally fine-tuned BART model.*
  > *Notice that it has captured the operative holding and used standard legal citation phrasing like '[Paras 2 and 3]' learned from CivilSum."*

---

### Minute 4: Legal Reasoning & Validation Audit (Tabs 2, 3, 4)
- **What to do:**
  1. Click **Tab 2 ("Legal Analysis & Doctrine")**:
     - Point out the extracted **Petitioner vs. Respondent**, **Bench**, and specifically the **Ratio Decidendi** and **Questions of Law**.
  2. Click **Tab 3 ("Validation & Consistency")**:
     - Point out the **Coverage Score (100%)** and **Factual Consistency Grade (PASSED)**.
     - Show the **"Zero ungrounded claims detected"** confirmation card, demonstrating that all dates and statutory sections were verified against the primary judgment.
  3. Click **Tab 4 ("Audit Trail & Provenance")**:
     - Expand Stage 1 to 5 to show exact ISO timestamps, latencies, and model names (`gemini-2.5-flash` vs `CivilSum-BART`).

---

### Minute 5: Artifact Export & Conclusion (Tab 1)
- **What to do:**
  1. Return to **Tab 1**.
  2. Point out the 4 download buttons:
     - `📄 Download Summary (.txt)`
     - `📊 Download Structured JSON`
     - `📑 Download Markdown Report`
     - `⏱️ Download Audit Log (.json)`
  3. Click **Download Markdown Report** to demonstrate the complete academic deliverable.
- **What to say:**
  > *"In conclusion, this project demonstrates that combining zero-shot foundation models for doctrine reasoning with a domain-fine-tuned sequence-to-sequence model and deterministic validation offers a robust, hallucination-resistant architecture for legal NLP.*
  > *Thank you, Professors. I am ready for questions."*
