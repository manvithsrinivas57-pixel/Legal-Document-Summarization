"""CivilSum Dataset Inspection and Verification Script.

Verifies the official CivilSum dataset splits, schemas, sample counts, and license.
Repository: https://github.com/ra-MANUJ-an/CivilSum (SIGIR 2024)
License: CC BY-NC-SA 4.0 (Data) / Apache 2.0 (Code)
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import argparse
import pandas as pd
import config


def download_official_civilsum_split(split_name: str, output_path: Path) -> bool:
    """Download official split from ra-MANUJ-an/CivilSum Google Drive link using gdown."""
    splits = config.CIVILSUM_METADATA["splits"]
    if split_name not in splits:
        print(f"Unknown split: {split_name}. Choose from: {list(splits.keys())}")
        return False

    gdrive_id = splits[split_name]["gdrive_id"]
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        import gdown

        url = f"https://drive.google.com/uc?id={gdrive_id}"
        print(f"Downloading official CivilSum {split_name}.csv from Google Drive (ID: {gdrive_id})...")
        gdown.download(url, str(output_path), quiet=False)
        return output_path.exists()
    except ImportError:
        print("gdown package is required for direct downloading. Install with: pip install gdown")
        print(f"Or manually download from: https://drive.google.com/file/d/{gdrive_id}/view?usp=sharing")
        return False


def inspect_file(file_path: Path, expected_split: str | None = None) -> dict:
    """Read CSV, verify expected columns and report genuine statistics without fabrication."""
    if not file_path.exists():
        return {"error": f"File not found: {file_path}", "exists": False}

    print(f"\n=======================================================")
    print(f" Inspecting File: {file_path.name}")
    print(f" Path: {file_path}")
    print(f"=======================================================")

    df = pd.read_csv(file_path)
    total_rows = len(df)
    columns = list(df.columns)

    print(f"Total Rows: {total_rows:,}")
    print(f"Columns: {columns}")

    expected_cols = [
        config.CIVILSUM_METADATA["schema"]["document_column"],
        config.CIVILSUM_METADATA["schema"]["summary_column"],
    ]
    missing_cols = [c for c in expected_cols if c not in columns]

    if missing_cols:
        print(f"WARNING: Missing expected columns: {missing_cols}")
    else:
        print("Schema Validation: PASSED (contains 'text' and 'summary' columns)")

    # Null checks
    null_texts = df["text"].isna().sum() if "text" in df else 0
    null_summaries = df["summary"].isna().sum() if "summary" in df else 0
    print(f"Null Documents: {null_texts}")
    print(f"Null Summaries: {null_summaries}")

    # Length statistics
    valid_df = df.dropna(subset=[c for c in ["text", "summary"] if c in df])
    text_word_counts = valid_df["text"].str.split().str.len()
    summary_word_counts = valid_df["summary"].str.split().str.len()

    print("\nDocument Word Lengths:")
    print(f"  Mean: {text_word_counts.mean():.1f} words")
    print(f"  Median: {text_word_counts.median():.1f} words")
    print(f"  Min: {text_word_counts.min()} words | Max: {text_word_counts.max():,} words")

    print("\nSummary Word Lengths:")
    print(f"  Mean: {summary_word_counts.mean():.1f} words")
    print(f"  Median: {summary_word_counts.median():.1f} words")
    print(f"  Min: {summary_word_counts.min()} words | Max: {summary_word_counts.max():,} words")

    if expected_split and expected_split in config.CIVILSUM_METADATA["splits"]:
        expected_samples = config.CIVILSUM_METADATA["splits"][expected_split]["samples"]
        print(f"\nOfficial CivilSum {expected_split} Benchmark:")
        print(f"  Expected samples: {expected_samples:,}")
        print(f"  Actual samples in inspected file: {total_rows:,}")
        if total_rows == expected_samples:
            print(f"  Match: EXACT MATCH with official {expected_split} split count.")
        else:
            print(f"  Match: Row count differs (custom subset or modified version).")

    return {
        "exists": True,
        "total_rows": total_rows,
        "columns": columns,
        "null_texts": int(null_texts),
        "null_summaries": int(null_summaries),
        "mean_doc_words": float(text_word_counts.mean()),
        "mean_summary_words": float(summary_word_counts.mean()),
    }


def main():
    parser = argparse.ArgumentParser(description="Inspect and verify CivilSum legal dataset files.")
    parser.add_argument("--data_dir", type=str, default="data", help="Directory containing dataset files")
    parser.add_argument("--file", type=str, help="Specific CSV file to inspect")
    parser.add_argument("--download", type=str, choices=["train", "validation", "test", "all"], help="Download official split")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)

    print("CivilSum Dataset Specification:")
    print(f" Title: {config.CIVILSUM_METADATA['title']}")
    print(f" Venue: {config.CIVILSUM_METADATA['venue']}")
    print(f" License: {config.CIVILSUM_METADATA['license']}")
    print(f" Repository: {config.CIVILSUM_METADATA['official_repo']}")
    print(f" Total Samples: {config.CIVILSUM_METADATA['total_samples']:,} (train: 21,015 | val: 1,168 | test: 1,167)")

    if args.download:
        splits = ["train", "validation", "test"] if args.download == "all" else [args.download]
        for s in splits:
            dest = data_dir / f"{s}.csv"
            download_official_civilsum_split(s, dest)

    if args.file:
        inspect_file(Path(args.file))
    else:
        # Check standard splits in data_dir
        for s in ["train", "validation", "test"]:
            p = data_dir / f"{s}.csv"
            if p.exists():
                inspect_file(p, expected_split=s)
            else:
                print(f"\nNote: '{p}' not present locally. Use --download {s} or manual download.")


if __name__ == "__main__":
    main()
