"""Helper script to detect, link, or guide setup of the fine-tuned CivilSum-BART weights."""

import sys
import shutil
from pathlib import Path

def setup_checkpoint():
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    target_dir = project_root / "models" / "checkpoints" / "civilsum_bart"
    target_weights = target_dir / "model.safetensors"

    print("=" * 70)
    print("CivilSum-BART Model Checkpoint Setup Helper")
    print("=" * 70)

    if target_weights.exists():
        size_mb = target_weights.stat().st_size / (1024 * 1024)
        print(f"✓ Fine-tuned weights already present at:")
        print(f"  {target_weights} ({size_mb:.2f} MB)")
        print("✓ Model is ready for execution.")
        return 0

    print("Target weights not currently present at:")
    print(f"  {target_weights}\n")

    candidates = [
        project_root.parent / "models" / "checkpoints" / "civilsum_bart" / "model.safetensors",
        project_root.parent / "Legal-Document-Summarizer" / "models" / "checkpoints" / "civilsum_bart" / "model.safetensors",
        project_root / "model.safetensors",
    ]

    found = None
    for c in candidates:
        if c.exists():
            found = c
            break

    if found:
        print(f"Detected model weights at adjacent location:")
        print(f"  {found} ({found.stat().st_size / (1024 * 1024):.2f} MB)")
        print("Copying to target checkpoint folder...")
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(found, target_weights)
        print(f"✓ Successfully copied weights to {target_weights}")
        return 0

    print("No local weights found automatically.")
    print("To configure the fine-tuned weights:")
    print("  1. Place 'model.safetensors' (532 MB) into:")
    print(f"     {target_dir}/")
    print("  2. Or train a new checkpoint on Google Colab GPU using:")
    print("     notebooks/civilsum_bart_finetuning.ipynb")
    print("  3. Or select 'Pretrained Baseline' in the Streamlit sidebar")
    print("     to evaluate raw facebook/bart-base base model performance.")
    print("=" * 70)
    return 1

if __name__ == "__main__":
    sys.exit(setup_checkpoint())
