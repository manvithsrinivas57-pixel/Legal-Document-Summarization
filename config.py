"""Configuration and environment management for Legal Document Summarization."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base project paths
BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"
CHECKPOINTS_DIR = MODELS_DIR / "checkpoints"
DEFAULT_CHECKPOINT_PATH = CHECKPOINTS_DIR / "civilsum_bart"
SAMPLE_DATA_DIR = BASE_DIR / "sample_data"
SCRIPTS_DIR = BASE_DIR / "scripts"

# Load local .env if present
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

# Gemini configuration
DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
# Official verified text models supporting generateContent from google.genai catalog
FALLBACK_GEMINI_MODELS = [
    "gemini-flash-lite-latest",
    "gemini-3.5-flash-lite",
    "gemini-3-flash-preview",
    "gemini-flash-latest",
    "gemini-3.8-flash",
    "gemini-3.5-flash",
    "gemini-pro-latest",
]

# BART configuration
BASE_BART_MODEL = "facebook/bart-base"
BART_MAX_INPUT_TOKENS = 1024
BART_MAX_SUMMARY_TOKENS = 350
BART_MIN_SUMMARY_TOKENS = 130  # Encourages complete 100-150 word legal summaries
BART_LENGTH_PENALTY = 2.5      # Encourages comprehensive coverage over premature termination
BART_NUM_BEAMS = 4

# Legal Disclaimer
LEGAL_DISCLAIMER = (
    "DISCLAIMER: This system generates automated analytical summaries for educational and "
    "research purposes only. The outputs do not constitute professional legal advice, formal "
    "statutory interpretation, or legal representation. Always verify all citations and holdings "
    "against primary official court records."
)

# CivilSum Dataset Information (SIGIR 2024 Benchmark)
CIVILSUM_METADATA = {
    "title": "CivilSum: A Dataset for Abstractive Summarization of Court Decisions",
    "venue": "47th International ACM SIGIR Conference on Research and Development in Information Retrieval (SIGIR '24)",
    "official_repo": "https://github.com/ra-MANUJ-an/CivilSum",
    "license": "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)",
    "total_samples": 23350,
    "splits": {
        "train": {"samples": 21015, "gdrive_id": "1WX5w-ClK82Yy916350bRp3hcuqab1D-x"},
        "validation": {"samples": 1168, "gdrive_id": "1khcDFSca6zUv-dFQ4XaxMt8jRf-9PZbV"},
        "test": {"samples": 1167, "gdrive_id": "1v0EM35CFWxFPc5D4bFxpf59mV_kEv0pw"},
    },
    "schema": {
        "document_column": "text",
        "summary_column": "summary",
        "jurisdiction": "Supreme Court of India and Indian High Courts",
    },
}


def get_gemini_api_key() -> str:
    """Retrieve Gemini API key from environment variable safely without printing."""
    return os.getenv("GEMINI_API_KEY", "").strip()


def resolve_checkpoint_path(path_input: str | Path | None = None) -> Path:
    """Resolve checkpoint path safely against BASE_DIR if given a relative path."""
    if path_input is None:
        custom = os.getenv("BART_CHECKPOINT_PATH")
        if custom:
            p = Path(custom)
            if not p.is_absolute() and not p.exists() and (BASE_DIR / p).exists():
                return (BASE_DIR / p).resolve()
            return p.resolve() if p.exists() else (BASE_DIR / p).resolve()
        return DEFAULT_CHECKPOINT_PATH.resolve()

    p = Path(path_input)
    if not p.is_absolute() and not p.exists() and (BASE_DIR / p).exists():
        return (BASE_DIR / p).resolve()
    return p.resolve() if p.exists() else (BASE_DIR / p).resolve()


def is_checkpoint_available(checkpoint_path: str | Path | None = None) -> bool:
    """Verify whether a genuinely fine-tuned BART checkpoint exists at the designated path.

    Checks for valid Hugging Face model directory containing config.json and weights.
    """
    target = resolve_checkpoint_path(checkpoint_path)

    if not target.exists() or not target.is_dir():
        return False

    has_config = (target / "config.json").exists()
    has_weights = (
        (target / "model.safetensors").exists()
        or (target / "pytorch_model.bin").exists()
        or (target / "model.safetensors.index.json").exists()
    )
    return has_config and has_weights


def get_active_checkpoint_path() -> Path:
    """Get the active checkpoint path from environment or default."""
    return resolve_checkpoint_path()

