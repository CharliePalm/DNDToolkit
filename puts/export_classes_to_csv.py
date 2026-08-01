"""
Export the cleaned class-feature artifacts to a single CSV file.

The CSV includes:
- per-class feature files from artifacts/cleaned_classes/*_features.json
- the shared feature bundle from artifacts/cleaned_classes/shared.json

Each row corresponds to one feature/class/subclass combination.
"""

import csv
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, Iterator, List

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from shared.model import serialize_uses  # noqa: E402

CLASSES_DIR = REPO_ROOT / "artifacts" / "cleaned_classes"
OUTPUT_FILE = CLASSES_DIR / "all_class_features.csv"
SHARED_FILE = CLASSES_DIR / "shared.json"

CSV_COLUMNS = [
    "name",
    "description",
    "level",
    "character_class",
    "subclass",
    "is_choice",
    "uses",
    "source",
    "source_file",
]


def _load_json(path: Path) -> List[dict]:
    with open(path, "r") as fp:
        return json.load(fp)


def _iter_class_rows(path: Path) -> Iterator[dict]:
    for feature in _load_json(path):
        yield {
            "name": feature.get("name", ""),
            "description": feature.get("description", ""),
            "level": feature.get("level", 0),
            "character_class": feature.get("character_class", ""),
            "subclass": feature.get("subclass") or "",
            "is_choice": feature.get("is_choice", False),
            "uses": serialize_uses(feature.get("uses")),
            "source": feature.get("source") or "",
            "source_file": path.name,
        }


def _iter_shared_rows(path: Path) -> Iterator[dict]:
    for feature in _load_json(path):
        for entry in feature.get("classes", []):
            yield {
                "name": feature.get("name", ""),
                "description": feature.get("description", ""),
                "level": feature.get("level", 0),
                "character_class": entry.get("character_class", ""),
                "subclass": entry.get("subclass") or "",
                "is_choice": feature.get("is_choice", False),
                "uses": serialize_uses(feature.get("uses")),
                "source": feature.get("source") or "",
                "source_file": path.name,
            }


def _iter_rows() -> Iterator[dict]:
    for path in sorted(CLASSES_DIR.glob("*_features.json")):
        yield from _iter_class_rows(path)
    if SHARED_FILE.exists():
        yield from _iter_shared_rows(SHARED_FILE)


def export_to_csv() -> Path:
    with open(OUTPUT_FILE, "w", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in _iter_rows():
            writer.writerow(row)
    return OUTPUT_FILE


if __name__ == "__main__":
    output_path = export_to_csv()
    print(f"wrote {output_path}")
