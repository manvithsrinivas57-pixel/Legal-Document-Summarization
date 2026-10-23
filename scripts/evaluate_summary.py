"""Held-out Evaluation Script for Legal Document Summarization on CivilSum.

Computes genuine ROUGE-1, ROUGE-2, ROUGE-L, and BERTScore on test split.
"""

import argparse
import json
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from evaluation.metrics import compute_rouge_scores, compute_bertscore
import config


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate legal summarizer on held-out test split.")
    parser.add_argument("--test_file", type=str, default="data/test.csv", help="Path to CivilSum test.csv")
    parser.add_argument(
        "--model_path",
        type=str,
        default="models/checkpoints/civilsum_bart",
        help="Path to fine-tuned model checkpoint or Hugging Face model ID",
    )
    parser.add_argument(
        "--predictions_file",
        type=str,
        default=None,
        help="Optional pre-generated predictions JSON/CSV file",
    )
    parser.add_argument(
        "--output_file",
        type=str,
        default="evaluation_results.json",
        help="File to save computed metric results",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Number of test samples to evaluate (default: 100 for fast eval, 1167 for full test split)",
    )
    parser.add_argument(
        "--compute_bertscore",
        action="store_true",
        help="Whether to compute BERTScore alongside ROUGE",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    test_path = Path(args.test_file)

    if not test_path.exists():
        print(f"ERROR: Test split file not found at '{test_path}'.")
        print("Download official test.csv via 'python scripts/inspect_dataset.py --download test'.")
        sys.exit(1)

    import pandas as pd

    df = pd.read_csv(test_path).dropna(subset=["text", "summary"])
    if args.limit and args.limit < len(df):
        print(f"Subsetting to first {args.limit} test samples for evaluation...")
        df = df.head(args.limit)

    references = [str(s).strip() for s in df["summary"].tolist()]
    predictions = []

    if args.predictions_file:
        pred_path = Path(args.predictions_file)
        if not pred_path.exists():
            print(f"ERROR: Specified predictions file '{pred_path}' does not exist.")
            sys.exit(1)
        with open(pred_path, "r", encoding="utf-8") as f:
            predictions = json.load(f)
    else:
        # Generate predictions dynamically using the model
        model_path = Path(args.model_path)
        is_local_dir = model_path.exists() and model_path.is_dir()

        if is_local_dir and not config.is_checkpoint_available(model_path):
            print(f"ERROR: Checkpoint at '{model_path}' is incomplete or missing weights.")
            sys.exit(1)

        print(f"Loading model from '{args.model_path}' for generation...")
        try:
            import torch
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

            tokenizer = AutoTokenizer.from_pretrained(str(model_path))
            model = AutoModelForSeq2SeqLM.from_pretrained(str(model_path))
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model = model.to(device)

            print(f"Generating abstractive summaries on {device}...")
            start_gen = time.time()
            for idx, text in enumerate(df["text"].tolist()):
                if (idx + 1) % 10 == 0 or idx == len(df) - 1:
                    print(f"Generating: {idx + 1}/{len(df)} samples...")

                # Apply CivilSum tail-aware truncation to capture the court holding
                words = str(text).split()
                if len(words) > 800:
                    lead = " ".join(words[:240])
                    tail = " ".join(words[-560:])
                    eval_text = f"{lead} {tail}"
                else:
                    eval_text = str(text)

                inputs = tokenizer(
                    eval_text,
                    max_length=config.BART_MAX_INPUT_TOKENS,
                    truncation=True,
                    return_tensors="pt",
                ).to(device)

                summary_ids = model.generate(
                    inputs["input_ids"],
                    max_length=config.BART_MAX_SUMMARY_TOKENS,
                    min_length=config.BART_MIN_SUMMARY_TOKENS,
                    num_beams=4,
                    length_penalty=2.0,
                    early_stopping=True,
                    no_repeat_ngram_size=3,
                )
                pred = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
                predictions.append(pred.strip())

            print(f"Generation complete in {(time.time() - start_gen):.2f}s.")

        except ImportError as err:
            print(f"ERROR: Transformers and Torch are required for live evaluation: {err}")
            sys.exit(1)

    print("\nComputing ROUGE metrics against human reference summaries...")
    rouge_results = compute_rouge_scores(predictions, references)

    print("\n================ EVALUATION METRIC REPORT ================")
    print(f" Dataset Split: CivilSum Held-Out Test ({len(references)} samples)")
    print(f" ROUGE-1 F1: {rouge_results['rouge1']:.2f}")
    print(f" ROUGE-2 F1: {rouge_results['rouge2']:.2f}")
    print(f" ROUGE-L F1: {rouge_results['rougeL']:.2f}")

    bert_results = {}
    if args.compute_bertscore:
        print("\nComputing BERTScore...")
        bert_results = compute_bertscore(predictions, references)
        if bert_results.get("available"):
            print(f" BERTScore F1: {bert_results['bertscore_f1']:.2f}")
            print(f" BERTScore Precision: {bert_results['bertscore_precision']:.2f}")
            print(f" BERTScore Recall: {bert_results['bertscore_recall']:.2f}")

    full_output = {
        "evaluation_timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model_path": str(args.model_path),
        "test_file": str(args.test_file),
        "samples_evaluated": len(references),
        "metrics": {
            "rouge": rouge_results,
            "bertscore": bert_results,
        },
    }

    out_file = Path(args.output_file)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(full_output, f, indent=2)

    print(f"\nDetailed evaluation metrics saved to: {out_file.resolve()}")


if __name__ == "__main__":
    main()
