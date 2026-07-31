"""
Clean the generated class feature artifacts in artifacts/classes.

Rules:
  1. Collapse the boilerplate entries (Hit Points, Proficiencies, Equipment,
     Optional Rule: Firearm Proficiency) into a single "Base Features" entry.
  2. Collapse the spellcasting sub-block (Spellcasting / Pact Magic and its
     related sub-features) into a single "Spellcasting" entry.
  3. Extract features that are shared by two or more classes (same name and a
     near-identical description) into shared_features.json, and remove them from
     each parent class file.
"""

from copy import copy
import json
import re
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List

CLASSES_DIR = Path(__file__).resolve().parent.parent / "artifacts" / "classes"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "artifacts" / "cleaned_classes"
SHARED_FILE = OUTPUT_DIR / "shared.json"

# entries merged into a single "Base Features" feature
BASE_FEATURE_NAMES = {
    "Hit Points",
    "Proficiencies",
    "Equipment",
    "Optional Rule: Firearm Proficiency",
}

# entries merged into a single "Spellcasting" feature
SPELLCASTING_NAMES = {
    "Spellcasting",
    "Pact Magic",
    "Tools Required",
    "Cantrips",
    "Cantrips (0-Level Spells)",
    "Spell Slots",
    "Spells Known of 1st Level and Higher",
    "Spellcasting Ability",
    "Preparing and Casting Spells",
    "Ritual Casting",
    "Spellcasting Focus",
    "Spellbook",
    "Learning Spells of 1st Level and Higher",
}

# "Base Features" is class-specific boilerplate, never eligible for cross-class
# sharing; the consolidated "Spellcasting" entry is still eligible so identical
# subclass spellcasting (e.g. Eldritch Knight / Arcane Trickster) can be shared.
CONSOLIDATED_NAMES = {"Base Features"}

# how similar two descriptions must be to count as "the same" feature
DESCRIPTION_SIMILARITY_THRESHOLD = 0.8

# UA multiclass features lead each description with "Level 6+ <Subclass> Feature"
FEATURE_PREFIX_RE = re.compile(
    r"^\s*Level \d+\+?\s+.*?\bFeature\b[\s:.\u2014-]*", re.IGNORECASE
)


def _strip_feature_prefix(description: str) -> str:
    """remove the "Level N+ <Subclass> Feature" boilerplate prefix from a description"""
    return FEATURE_PREFIX_RE.sub("", description or "", count=1).strip()


def _normalize_subclass(subclass):
    """wrap a trailing "UA" marker in parentheses (e.g. "Mage of Lorehold UA" ->
    "Mage of Lorehold (UA)"), leaving already-parenthesized names untouched"""
    if not subclass:
        return subclass
    return re.sub(r"\s+UA\s*$", " (UA)", subclass.rstrip())


def _normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name).strip().lower()


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", (text or "").lower())).strip()


def _similar(a: str, b: str) -> bool:
    return SequenceMatcher(None, _normalize_text(a), _normalize_text(b)).ratio() >= (
        DESCRIPTION_SIMILARITY_THRESHOLD
    )


def _merge_descriptions(features: List[dict]) -> str:
    """join a group of features into one description with a sub-heading per part"""
    return "\n\n".join(f"{f['name']}:\n{f['description']}" for f in features)


def _consolidate(features: List[dict], names: set, merged_name: str) -> List[dict]:
    """
    replace every feature whose name is in `names` with a single `merged_name`
    feature, consolidated per subclass so base-class and each subclass keep their
    own merged entry, placed where that group's first match appeared.
    """
    matches = [f for f in features if f["name"] in names]
    if len(matches) < 1:
        return features

    # one merged entry per subclass (None for the base class)
    merged_by_subclass: Dict = {}
    for f in matches:
        merged_by_subclass.setdefault(f.get("subclass"), []).append(f)

    merged_entries = {}
    for subclass, group in merged_by_subclass.items():
        merged_entries[subclass] = {
            "name": merged_name,
            "description": _merge_descriptions(group),
            "character_class": group[0]["character_class"],
            "level": min(f.get("level") or 1 for f in group),
            "is_choice": False,
            "uses": None,
            "subclass": subclass,
            "source": None,
        }

    result: List[dict] = []
    match_ids = {id(f) for f in matches}
    inserted: set = set()
    for f in features:
        if id(f) in match_ids:
            subclass = f.get("subclass")
            if subclass not in inserted:
                result.append(merged_entries[subclass])
                inserted.add(subclass)
        else:
            result.append(f)
    return result


def _cluster_by_description(group: List[dict]) -> List[List[dict]]:
    """greedily cluster same-named features by near-identical description"""
    clusters: List[List[dict]] = []
    for feature in group:
        for cluster in clusters:
            if _similar(cluster[0]["description"], feature["description"]):
                cluster.append(feature)
                break
        else:
            clusters.append([feature])
    return clusters


def clean() -> None:
    # 1 & 2: per-class consolidation
    data: Dict[Path, List[dict]] = {}
    for path in sorted(CLASSES_DIR.glob("*_features.json")):
        with open(path, "r") as fp:
            features: List[dict] = json.load(fp)
        for feature in features:
            feature["description"] = _strip_feature_prefix(
                feature.get("description", "")
            )
            feature["subclass"] = _normalize_subclass(feature.get("subclass"))
        features = _consolidate(features, BASE_FEATURE_NAMES, "Base Features")
        features = _consolidate(features, SPELLCASTING_NAMES, "Spellcasting")
        data[path] = features

    # 3: gather sharable features grouped by normalized name
    groups: Dict[str, List[dict]] = defaultdict(list)
    owner: Dict[int, Path] = {}
    for path, features in data.items():
        for feature in features:
            if feature["name"] in CONSOLIDATED_NAMES:
                continue
            groups[_normalize_name(feature["name"])].append(feature)
            owner[id(feature)] = path

    shared: List[dict] = []
    remove_ids: set = set()
    for group in groups.values():
        for cluster in _cluster_by_description(group):
            classes = sorted({f["character_class"] for f in cluster})
            if len(classes) < 2:
                continue
            pairs = sorted(
                {(f["character_class"], f.get("subclass")) for f in cluster},
                key=lambda pair: (pair[0], pair[1] or ""),
            )
            representative = copy(cluster[0])
            if "character_class" in representative:
                del representative["character_class"]
            shared.append(
                {
                    **representative,
                    "classes": [
                        {"character_class": cls, "subclass": subclass}
                        for cls, subclass in pairs
                    ],
                }
            )
            remove_ids.update(id(f) for f in cluster)

    shared.sort(key=lambda entry: entry["name"].lower())

    # remove shared features from their parent class files and write everything back
    for path, features in data.items():
        cleaned = [f for f in features if id(f) not in remove_ids]
        output_path = OUTPUT_DIR / path.name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as fp:
            json.dump(cleaned, fp, indent=4)

    SHARED_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SHARED_FILE, "w") as fp:
        json.dump(shared, fp, indent=4)

    print(f"consolidated {len(data)} class files")
    print(f"extracted {len(shared)} shared features -> {SHARED_FILE.name}")


if __name__ == "__main__":
    clean()
