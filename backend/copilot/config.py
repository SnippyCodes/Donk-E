import os
from pathlib import Path
from typing import List

# Root project directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Reference date (configurable via env var)
AS_OF = os.getenv("AS_OF", "2026-10-17")

# Dataset roots (comma-separated paths)
_raw_roots = os.getenv("DATASET_ROOTS", "data/sample-data")
DATASET_ROOTS: List[str] = [
    r.strip() for r in _raw_roots.split(",") if r.strip()
]

# Database configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "backend" / "data" / "copilot.db"))

# Rules path
RULES_PATH = os.getenv("RULES_PATH", str(BASE_DIR / "rules.yaml"))


def ensure_data_dirs() -> None:
    """Ensure required runtime data directories exist."""
    db_file = Path(DATABASE_PATH)
    db_file.parent.mkdir(parents=True, exist_ok=True)


def get_dataset_roots() -> List[Path]:
    """Return verified existing Path objects for dataset roots."""
    valid_paths = []
    for r in DATASET_ROOTS:
        p = Path(r)
        if not p.is_absolute():
            p = BASE_DIR / p
        if p.exists():
            valid_paths.append(p)
    if not valid_paths:
        # Fallback to direct submodule path if available
        fallback = BASE_DIR / "flytbase-ahc-swe-asset-intelligence-dataset" / "sample-data"
        if fallback.exists():
            valid_paths.append(fallback)
    return valid_paths
