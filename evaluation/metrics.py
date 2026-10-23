"""Evaluation metrics module for ROUGE and BERTScore calculation."""

import re
from typing import Any


def _simple_ngram_lcs(ref: str, pred: str) -> dict[str, float]:
    """Pure Python fallback for basic n-gram overlap and LCS when rouge-score is not installed."""
    def get_ngrams(tokens, n):
        return [tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]

    ref_toks = re.findall(r"\w+", ref.lower())
    pred_toks = re.findall(r"\w+", pred.lower())

    if not ref_toks or not pred_toks:
        return {"rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0}

    # Unigram (ROUGE-1)
    ref_1 = get_ngrams(ref_toks, 1)
    pred_1 = get_ngrams(pred_toks, 1)
    match_1 = sum(1 for g in pred_1 if g in ref_1)
    p1 = match_1 / len(pred_1) if pred_1 else 0
    r1 = match_1 / len(ref_1) if ref_1 else 0
    f1 = (2 * p1 * r1) / (p1 + r1) if (p1 + r1) > 0 else 0

    # Bigram (ROUGE-2)
    ref_2 = get_ngrams(ref_toks, 2)
    pred_2 = get_ngrams(pred_toks, 2)
    match_2 = sum(1 for g in pred_2 if g in ref_2)
    p2 = match_2 / len(pred_2) if pred_2 else 0
    r2 = match_2 / len(ref_2) if ref_2 else 0
    f2 = (2 * p2 * r2) / (p2 + r2) if (p2 + r2) > 0 else 0

    # Longest Common Subsequence (ROUGE-L approximation)
    m, n = len(ref_toks), len(pred_toks)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if ref_toks[i - 1] == pred_toks[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    lcs = dp[m][n]
    pl = lcs / n if n else 0
    rl = lcs / m if m else 0
    fl = (2 * pl * rl) / (pl + rl) if (pl + rl) > 0 else 0

    return {
        "rouge1": round(f1 * 100, 2),
        "rouge2": round(f2 * 100, 2),
        "rougeL": round(fl * 100, 2),
    }


def compute_rouge_scores(predictions: list[str], references: list[str]) -> dict[str, Any]:
    """Compute official ROUGE-1, ROUGE-2, and ROUGE-L scores using rouge_score or pure fallback."""
    if len(predictions) != len(references):
        raise ValueError("Predictions and references lists must have identical lengths.")

    if not predictions:
        return {"rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0}

    try:
        from rouge_score import rouge_scorer

        scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
        r1_f, r2_f, rl_f = [], [], []

        for pred, ref in zip(predictions, references):
            scores = scorer.score(ref, pred)
            r1_f.append(scores["rouge1"].fmeasure * 100)
            r2_f.append(scores["rouge2"].fmeasure * 100)
            rl_f.append(scores["rougeL"].fmeasure * 100)

        import numpy as np

        return {
            "rouge1": round(float(np.mean(r1_f)), 2),
            "rouge2": round(float(np.mean(r2_f)), 2),
            "rougeL": round(float(np.mean(rl_f)), 2),
            "method": "official_rouge_scorer",
        }

    except ImportError:
        # Fallback pure python calculation
        all_scores = [_simple_ngram_lcs(ref, pred) for pred, ref in zip(predictions, references)]
        avg_r1 = sum(s["rouge1"] for s in all_scores) / len(all_scores)
        avg_r2 = sum(s["rouge2"] for s in all_scores) / len(all_scores)
        avg_rl = sum(s["rougeL"] for s in all_scores) / len(all_scores)

        return {
            "rouge1": round(avg_r1, 2),
            "rouge2": round(avg_r2, 2),
            "rougeL": round(avg_rl, 2),
            "method": "native_ngram_lcs_fallback",
        }


def compute_bertscore(
    predictions: list[str], references: list[str], lang: str = "en"
) -> dict[str, Any]:
    """Compute BERTScore (Precision, Recall, F1) if bert_score package is installed."""
    try:
        from bert_score import score

        P, R, F1 = score(predictions, references, lang=lang, verbose=False)
        return {
            "bertscore_precision": round(float(P.mean()) * 100, 2),
            "bertscore_recall": round(float(R.mean()) * 100, 2),
            "bertscore_f1": round(float(F1.mean()) * 100, 2),
            "available": True,
        }
    except Exception as exc:
        return {
            "bertscore_precision": None,
            "bertscore_recall": None,
            "bertscore_f1": None,
            "available": False,
            "note": f"BERTScore not computed: {str(exc)}",
        }
