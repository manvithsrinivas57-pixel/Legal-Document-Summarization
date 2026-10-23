"""Root entrypoint wrapper for submission application."""
import os
import sys
from pathlib import Path
import runpy

PROJECT_DIR = Path(__file__).resolve().parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

app_path = PROJECT_DIR / "app.py"
runpy.run_path(str(app_path), run_name="__main__")
