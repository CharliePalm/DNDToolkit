"""One-off: correct `level` on existing artifacts/classes/*_features.json for UA
multiclass subclass features whose description leads with "Level N+ ... Feature".

The original scrape missed this header format and fell back to a default (often
picking up a spurious ordinal like "4th level" from spell-slot text). This only
touches features that carry the header, leaving table-derived levels intact.

    .venv/bin/python misc_cleaning/backfill_levels.py
"""

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from misc_loader.class_features import FEATURE_LEVEL_RE  # noqa: E402

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
            header = FEATURE_LEVEL_RE.search(feature.get("description", ""))
            if not header:
                continue
            level = int(header.group(1))
            if feature.get("level") != level:
                feature["level"] = level
                changed_features += 1
                file_changed = True
        if file_changed:
            changed_files += 1
            with open(path, "w") as handle:
                json.dump(features, handle, indent=4)
    print(f"updated {changed_features} features across {changed_files} files")


if __name__ == "__main__":
    main()
