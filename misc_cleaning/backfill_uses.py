"""One-off: backfill `uses` on existing artifacts/classes/*_features.json using the
improved prose detection in misc_loader.class_features, without re-scraping.

Only fills features whose `uses` is currently null/missing; never overwrites an
existing value (e.g. level-table resource breakpoints). Run with the venv:

    .venv/bin/python misc_cleaning/backfill_uses.py
"""

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from misc_loader.class_features import _uses_from_description  # noqa: E402

OUTPUT_DIR = "artifacts/classes"


def main() -> None:
    changed_files = 0
    changed_features = 0
    for path in sorted(glob.glob(os.path.join(OUTPUT_DIR, "*_features.json"))):
        if os.path.basename(path) == "shared_features.json":
            continue
        with open(path) as handle:
            features = json.load(handle)
        file_changed = False
        for feature in features:
            if feature.get("uses"):
                continue
            inferred = _uses_from_description(feature.get("description", ""))
            if inferred is not None and inferred != feature.get("uses"):
                feature["uses"] = inferred
                changed_features += 1
                file_changed = True
        if file_changed:
            changed_files += 1
            with open(path, "w") as handle:
                json.dump(features, handle, indent=4)
    print(f"updated {changed_features} features across {changed_files} files")


if __name__ == "__main__":
    main()
