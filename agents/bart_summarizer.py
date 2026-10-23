"""BART Summarization Agent for Legal Document Summarization.

Strictly manages fine-tuned checkpoints vs pretrained base models adhering to research integrity rules.
"""

import time
from pathlib import Path
from typing import Any
import config


class BARTSummarizerAgent:
    """Agent that runs local abstractive summarization using fine-tuned BART or pretrained baseline."""

    def __init__(
        self,
        checkpoint_path: str | Path | None = None,
        mode: str = "fine_tuned",  # "fine_tuned" or "pretrained_base"
        device: str = "auto",
    ):
        self.checkpoint_path = config.resolve_checkpoint_path(checkpoint_path)
        self.mode = mode
        self.device = device
        self._tokenizer = None
        self._model = None

    def check_checkpoint_status(self) -> dict[str, Any]:
        """Verify existence and validity of fine-tuned checkpoint."""
        exists = config.is_checkpoint_available(self.checkpoint_path)
        return {
            "checkpoint_path": str(self.checkpoint_path),
            "exists": exists,
            "mode": self.mode,
            "is_fine_tuned": exists and (self.mode == "fine_tuned"),
            "details": (
                f"Valid checkpoint verified at '{self.checkpoint_path}'"
                if exists
                else f"No fine-tuned checkpoint found at '{self.checkpoint_path}'."
            ),
        }

    def _prepare_tail_aware_text(self, text: str, max_words: int = 800) -> str:
        """Address CivilSum's verified 'tail bias' in Indian court judgments.

        Standard lead-bias truncation misses the critical final holding in court decisions.
        We preserve the lead 30% (case framing/parties) and tail 70% (arguments & holding).
        """
        words = text.split()
        if len(words) <= max_words:
            return text

        lead_count = int(max_words * 0.30)
        tail_count = max_words - lead_count

        lead_text = " ".join(words[:lead_count])
        tail_text = " ".join(words[-tail_count:])
        return f"{lead_text}\n\n[... procedural analysis omitted for token budget ...]\n\n{tail_text}"

    def summarize(self, legal_text: str) -> dict[str, Any]:
        """Generate final abstractive summary using the designated BART model."""
        start_time = time.time()
        status_info = self.check_checkpoint_status()

        # Strict Research Integrity Check: Do NOT fake or substitute missing checkpoint
        if self.mode == "fine_tuned" and not status_info["exists"]:
            latency = round(time.time() - start_time, 2)
            return {
                "status": "CHECKPOINT_MISSING",
                "summary": None,
                "model_identifier": f"CivilSum-BART Checkpoint ({self.checkpoint_path.name})",
                "is_fine_tuned": False,
                "latency_seconds": latency,
                "explanation": (
                    f"RESEARCH INTEGRITY NOTICE: No fine-tuned CivilSum BART model checkpoint was found at:\n"
                    f"`{self.checkpoint_path}`\n\n"
                    "In adherence to research ethics, Google Gemini has NOT been silently substituted as a "
                    "replacement for the final fine-tuned BART summary.\n\n"
                    "Next Steps:\n"
                    "1. Train facebook/bart-base on the official CivilSum dataset using Google Colab GPU via "
                    "`notebooks/civilsum_bart_finetuning.ipynb`.\n"
                    "2. Download your trained checkpoint folder and place it at `models/checkpoints/civilsum_bart`.\n"
                    "3. To test baseline behavior without fine-tuning, you may explicitly select the "
                    "'Pretrained Base (facebook/bart-base)' comparison mode in the application settings."
                ),
                "error": "Fine-tuned model checkpoint missing on local filesystem.",
            }

        # Check local transformers / torch availability
        try:
            import torch
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        except ImportError as err:
            latency = round(time.time() - start_time, 2)
            return {
                "status": "DEPENDENCIES_MISSING",
                "summary": None,
                "model_identifier": (
                    "facebook/bart-base" if self.mode == "pretrained_base" else "CivilSum-BART"
                ),
                "is_fine_tuned": False,
                "latency_seconds": latency,
                "explanation": (
                    f"PyTorch or Hugging Face Transformers is not installed in the local Python environment ({err}).\n"
                    "To run local neural summarization, install dependencies via:\n"
                    "`pip install torch transformers`\n"
                    "Or execute fine-tuning and evaluation directly on Google Colab GPU with the provided notebook."
                ),
                "error": str(err),
            }

        try:
            model_target = (
                str(self.checkpoint_path) if self.mode == "fine_tuned" else config.BASE_BART_MODEL
            )
            is_ft = self.mode == "fine_tuned"
            model_id = (
                f"CivilSum-BART ({self.checkpoint_path.name})"
                if is_ft
                else f"{config.BASE_BART_MODEL} (Pretrained Baseline - Untrained on CivilSum)"
            )

            # Lazy load model and tokenizer
            if self._model is None or self._tokenizer is None:
                self._tokenizer = AutoTokenizer.from_pretrained(model_target)
                self._model = AutoModelForSeq2SeqLM.from_pretrained(model_target)

                # Determine compute device
                if self.device == "auto":
                    device = "cuda" if torch.cuda.is_available() else "cpu"
                else:
                    device = self.device
                self._model = self._model.to(device)

            prepared_text = self._prepare_tail_aware_text(legal_text)
            input_words = legal_text.split()
            input_word_count = len(input_words)

            inputs = self._tokenizer(
                prepared_text,
                max_length=config.BART_MAX_INPUT_TOKENS,
                truncation=True,
                return_tensors="pt",
            )

            input_ids = inputs["input_ids"].to(self._model.device)
            attention_mask = inputs["attention_mask"].to(self._model.device)

            # Adapt summary bounds dynamically: avoid forcing long generation on short orders,
            # while enforcing full length budget on multi-page judgments.
            dynamic_min_tokens = min(
                config.BART_MIN_SUMMARY_TOKENS,
                max(35, int(input_word_count * 0.35))
            )
            dynamic_max_tokens = min(
                config.BART_MAX_SUMMARY_TOKENS,
                max(dynamic_min_tokens + 50, min(config.BART_MAX_SUMMARY_TOKENS, int(input_word_count * 0.85)))
            )

            # Generation parameters tailored for legal abstractive summarization
            summary_ids = self._model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_length=dynamic_max_tokens,
                min_length=dynamic_min_tokens,
                num_beams=config.BART_NUM_BEAMS,
                length_penalty=config.BART_LENGTH_PENALTY,
                early_stopping=True,
                no_repeat_ngram_size=3,
            )

            generated_summary = self._tokenizer.decode(
                summary_ids[0], skip_special_tokens=True, clean_up_tokenization_spaces=False
            )

            latency = round(time.time() - start_time, 2)
            return {
                "status": "SUCCESS",
                "summary": generated_summary.strip(),
                "model_identifier": model_id,
                "checkpoint_path": str(self.checkpoint_path),
                "is_fine_tuned": is_ft,
                "latency_seconds": latency,
                "input_word_count": len(legal_text.split()),
                "summary_word_count": len(generated_summary.split()),
                "explanation": None,
                "error": None,
            }

        except Exception as exc:
            latency = round(time.time() - start_time, 2)
            return {
                "status": "ERROR",
                "summary": None,
                "model_identifier": "BART-Inference-Error",
                "is_fine_tuned": False,
                "latency_seconds": latency,
                "explanation": f"Inference execution encountered an unexpected error: {str(exc)}",
                "error": str(exc),
            }
