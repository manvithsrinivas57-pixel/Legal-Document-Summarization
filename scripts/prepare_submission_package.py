"""Script to prepare clean college submission package and create ZIP archive."""

import os
import shutil
import zipfile
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
PROJECT_DIR = WORKSPACE_ROOT / "Legal-Document-Summarization"
SUBMISSION_DIR = WORKSPACE_ROOT / "Legal-Document-Summarization-Submission"
ZIP_PATH = WORKSPACE_ROOT / "Legal-Document-Summarization-Submission.zip"

print(f"Project Source: {PROJECT_DIR}")
print(f"Target Submission: {SUBMISSION_DIR}")
print(f"Target ZIP: {ZIP_PATH}")

# 1. Clean previous submission folder if exists
if SUBMISSION_DIR.exists():
    shutil.rmtree(SUBMISSION_DIR)
SUBMISSION_DIR.mkdir(parents=True, exist_ok=True)

# 2. Files and Directories to copy
DIRECTORIES_TO_COPY = [
    "agents",
    "workflow",
    "evaluation",
    "scripts",
    "notebooks",
    "sample_data",
    "tests",
    "screenshots",
]

FILES_TO_COPY = [
    "app.py",
    "config.py",
    "requirements.txt",
    "requirements-colab.txt",
    ".env.example",
    "README.md",
]

# Copy Directories
for d in DIRECTORIES_TO_COPY:
    src = PROJECT_DIR / d
    dst = SUBMISSION_DIR / d
    if src.exists():
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"))
        print(f"Copied directory: {d} -> {dst}")

# Copy Individual Files
for f in FILES_TO_COPY:
    src = PROJECT_DIR / f
    dst = SUBMISSION_DIR / f
    if src.exists():
        shutil.copy2(src, dst)
        print(f"Copied file: {f} -> {dst}")

# Copy Models metadata (excluding the 532MB safetensors for lightweight portable ZIP submission)
MODELS_SUBMISSION_DIR = SUBMISSION_DIR / "models" / "checkpoints" / "civilsum_bart"
MODELS_SUBMISSION_DIR.mkdir(parents=True, exist_ok=True)

SRC_CHECKPOINT_DIR = PROJECT_DIR / "models" / "checkpoints" / "civilsum_bart"
if SRC_CHECKPOINT_DIR.exists():
    for item in SRC_CHECKPOINT_DIR.iterdir():
        if item.name != "model.safetensors" and not item.is_dir():
            shutil.copy2(item, MODELS_SUBMISSION_DIR / item.name)
            print(f"Copied checkpoint asset: {item.name}")

# Create MODEL_CHECKPOINT_INSTRUCTIONS.md in submission
instructions = f"""# Fine-Tuned CivilSum-BART Model Checkpoint Setup

The fine-tuned model configuration, tokenizer vocabularies, training logs, and metadata are bundled in this folder:
- `config.json`
- `training_metadata.json`
- `tokenizer_config.json`
- `generation_config.json`
- `training_args.bin`

### Where are the 532 MB Model Weights (`model.safetensors`)?
To keep the ZIP archive lightweight and email/LMS-portable (~3 MB instead of >550 MB), the heavy binary weights file `model.safetensors` is not packed into the ZIP. 

### How to configure the weights:
1. **Option A (Automatic Helper Script):**
   From the submission root directory, run:
   ```powershell
   python scripts/setup_checkpoint.py
   ```
   This will automatically locate and link or copy `model.safetensors` from adjacent project folders.

2. **Option B (Direct PowerShell Copy):**
   ```powershell
   Copy-Item "..\\Legal-Document-Summarization\\models\\checkpoints\\civilsum_bart\\model.safetensors" "models\\checkpoints\\civilsum_bart\\model.safetensors"
   ```

3. **Option C (Train on Google Colab GPU):**
   Open `notebooks/civilsum_bart_finetuning.ipynb` on Google Colab, execute the training workflow on the official CivilSum dataset, and download the checkpoint weights.

4. **Option D (Pretrained Baseline Mode):**
   You can also select **'Pretrained Baseline (facebook/bart-base)'** directly in the Streamlit web sidebar to run the application immediately even before custom weights are placed.
"""
(MODELS_SUBMISSION_DIR / "README.md").write_text(instructions, encoding="utf-8")

# Also add a root app.py launcher wrapper in workspace root style
launcher_code = """\"\"\"Root entrypoint wrapper for submission application.\"\"\"
import os
import sys
from pathlib import Path
import runpy

PROJECT_DIR = Path(__file__).resolve().parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

app_path = PROJECT_DIR / "app.py"
runpy.run_path(str(app_path), run_name="__main__")
"""
(SUBMISSION_DIR / "run_app.py").write_text(launcher_code, encoding="utf-8")

# 3. Create ZIP archive of the submission package
print("\nCreating ZIP archive...")
if ZIP_PATH.exists():
    ZIP_PATH.unlink()

with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(SUBMISSION_DIR):
        for file in files:
            file_path = Path(root) / file
            rel_path = file_path.relative_to(SUBMISSION_DIR)
            zipf.write(file_path, arcname=str(rel_path))

zip_size_mb = ZIP_PATH.stat().st_size / (1024 * 1024)
print(f"SUCCESS: Submission package created at {SUBMISSION_DIR}")
print(f"SUCCESS: ZIP archive created at {ZIP_PATH} ({zip_size_mb:.2f} MB)")
