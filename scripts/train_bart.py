"""Fine-tuning script for training facebook/bart-base on official CivilSum dataset.

Designed for Google Colab GPU or local server execution.
Adheres strictly to research integrity: authentic training, no synthetic metrics.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import config


def parse_args():
    parser = argparse.ArgumentParser(description="Fine-tune facebook/bart-base on CivilSum dataset.")
    parser.add_argument("--train_file", type=str, default="data/train.csv", help="Path to train.csv")
    parser.add_argument("--val_file", type=str, default="data/validation.csv", help="Path to validation.csv")
    parser.add_argument(
        "--output_dir",
        type=str,
        default="models/checkpoints/civilsum_bart",
        help="Directory to save fine-tuned model checkpoint",
    )
    parser.add_argument(
        "--model_name_or_path", type=str, default=config.BASE_BART_MODEL, help="Base Hugging Face model"
    )
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=4, help="Per device train batch size")
    parser.add_argument("--grad_accum_steps", type=int, default=4, help="Gradient accumulation steps")
    parser.add_argument("--learning_rate", type=float, default=3e-5, help="Learning rate")
    parser.add_argument("--weight_decay", type=float, default=0.01, help="Weight decay")
    parser.add_argument("--max_source_length", type=int, default=1024, help="Maximum input token length")
    parser.add_argument("--max_target_length", type=int, default=350, help="Maximum summary token length")
    parser.add_argument("--fp16", action="store_true", help="Use 16-bit mixed precision (GPU only)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument(
        "--sample_limit",
        type=int,
        default=None,
        help="Optional row limit for quick training validation or resource-constrained runs",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # 1. Dependency Verification
    try:
        import torch
        from datasets import Dataset
        from transformers import (
            AutoModelForSeq2SeqLM,
            AutoTokenizer,
            DataCollatorForSeq2Seq,
            Seq2SeqTrainer,
            Seq2SeqTrainingArguments,
            set_seed,
        )
    except ImportError as exc:
        print(f"ERROR: Required ML libraries missing ({exc}).")
        print("Please install training dependencies: pip install -r requirements-colab.txt")
        sys.exit(1)

    set_seed(args.seed)

    train_path = Path(args.train_file)
    val_path = Path(args.val_file)
    out_dir = Path(args.output_dir)

    # 2. Strict Dataset Verification (Research Integrity: No silent substitutions)
    if not train_path.exists():
        print(f"ERROR: Train dataset not found at '{train_path}'.")
        print("Please obtain official CivilSum train.csv via 'python scripts/inspect_dataset.py --download train'.")
        print("Never substitute an unrelated dataset without documenting the variance.")
        sys.exit(1)

    if not val_path.exists():
        print(f"ERROR: Validation dataset not found at '{val_path}'.")
        print("Please obtain official CivilSum validation.csv via 'python scripts/inspect_dataset.py --download validation'.")
        sys.exit(1)

    print(f"\n=======================================================")
    print(f" Legal Document Summarization - Supervised Fine-Tuning")
    print(f" Base Model: {args.model_name_or_path}")
    print(f" Train Split: {train_path}")
    print(f" Validation Split: {val_path}")
    print(f" Checkpoint Output: {out_dir}")
    print(f" CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f" GPU Device: {torch.cuda.get_device_name(0)}")
    print(f"=======================================================\n")

    import pandas as pd

    train_df = pd.read_csv(train_path).dropna(subset=["text", "summary"])
    val_df = pd.read_csv(val_path).dropna(subset=["text", "summary"])

    if args.sample_limit:
        print(f"Applying sample limit of {args.sample_limit} for testing run...")
        train_df = train_df.head(args.sample_limit)
        val_df = val_df.head(min(args.sample_limit // 4, len(val_df)))

    print(f"Loaded {len(train_df):,} training cases and {len(val_df):,} validation cases.")

    # 3. Load Tokenizer & Model
    print(f"Loading base tokenizer and model '{args.model_name_or_path}'...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name_or_path)
    model = AutoModelForSeq2SeqLM.from_pretrained(args.model_name_or_path)

    # 4. Tokenization & Preprocessing with Tail-Aware Strategy for CivilSum
    def preprocess_batch(batch):
        # Apply tail-aware preservation if document is long
        processed_texts = []
        for doc in batch["text"]:
            words = str(doc).split()
            if len(words) > 800:
                lead = " ".join(words[:240])
                tail = " ".join(words[-560:])
                processed_texts.append(f"{lead} {tail}")
            else:
                processed_texts.append(str(doc))

        model_inputs = tokenizer(
            processed_texts,
            max_length=args.max_source_length,
            truncation=True,
            padding="max_length",
        )

        labels = tokenizer(
            text_target=[str(s) for s in batch["summary"]],
            max_length=args.max_target_length,
            truncation=True,
            padding="max_length",
        )

        # Replace padding token id with -100 so it is ignored by CrossEntropyLoss
        labels_matrix = [
            [(token if token != tokenizer.pad_token_id else -100) for token in seq]
            for seq in labels["input_ids"]
        ]
        model_inputs["labels"] = labels_matrix
        return model_inputs

    train_dataset = Dataset.from_pandas(train_df[["text", "summary"]])
    val_dataset = Dataset.from_pandas(val_df[["text", "summary"]])

    print("Tokenizing datasets...")
    train_tokenized = train_dataset.map(preprocess_batch, batched=True, remove_columns=["text", "summary"])
    val_tokenized = val_dataset.map(preprocess_batch, batched=True, remove_columns=["text", "summary"])

    # 5. Training Arguments
    training_args = Seq2SeqTrainingArguments(
        output_dir=str(out_dir / "checkpoints_epoch"),
        eval_strategy="epoch",
        save_strategy="epoch",
        learning_rate=args.learning_rate,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum_steps,
        weight_decay=args.weight_decay,
        save_total_limit=2,
        num_train_epochs=args.epochs,
        predict_with_generate=False,
        fp16=args.fp16 and torch.cuda.is_available(),
        logging_steps=50,
        load_best_model_at_end=True,
        metric_for_best_model="loss",
        report_to="none",
        seed=args.seed,
    )

    data_collator = DataCollatorForSeq2Seq(tokenizer, model=model)

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train_tokenized,
        eval_dataset=val_tokenized,
        processing_class=tokenizer,
        data_collator=data_collator,
    )

    # 6. Execute Training
    start_train_time = time.time()
    print("Initiating supervised fine-tuning...")
    train_result = trainer.train()
    total_train_seconds = time.time() - start_train_time

    # 7. Save Final Checkpoint
    print(f"\nTraining completed in {total_train_seconds/60:.2f} minutes.")
    print(f"Saving fine-tuned model checkpoint and tokenizer to '{out_dir}'...")
    out_dir.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(out_dir))
    tokenizer.save_pretrained(str(out_dir))

    # 8. Record Genuine Training Provenance Metadata
    metadata = {
        "status": "COMPLETED",
        "base_model": args.model_name_or_path,
        "dataset": "CivilSum (SIGIR 2024)",
        "train_samples_used": len(train_df),
        "val_samples_used": len(val_df),
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "grad_accum_steps": args.grad_accum_steps,
        "learning_rate": args.learning_rate,
        "total_train_seconds": round(total_train_seconds, 2),
        "train_loss": float(train_result.training_loss),
        "global_steps": int(train_result.global_step),
        "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
        "date_completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    with open(out_dir / "training_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print("\nCheckpoint successfully exported. Verified files:")
    for f in out_dir.iterdir():
        print(f"  - {f.name} ({f.stat().st_size / (1024*1024):.2f} MB)")


if __name__ == "__main__":
    main()
