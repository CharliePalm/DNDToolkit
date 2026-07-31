"""
Load every class feature from artifacts/classes and create a page for each in a
single Notion database (DB_ID).

Each feature becomes one database page:
  - "Name" (title), "Class" / "Subclass" (multi_select) come from the feature.
  - "ismanual", "Important Effects", "Total Uses", "Remaining Uses" mirror the
    empty defaults of the target database.
  - The feature's "description" is appended to the page body as blocks.
  - The page icon is taken from artifacts/classes/class_icons.json (a native
    Notion icon set by name/color).

Run from the repo root:  python puts/put_class_features.py
(requires the NOTION_TOKEN environment variable)
"""

from asyncio import run
import json
import sys
from pathlib import Path
from typing import Dict, List

# allow running the file directly (puts/ is not on sys.path otherwise)
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from shared.model import bullet_char, serialize_uses  # noqa: E402
from shared.notion.notion import Notion  # noqa: E402

NON_FEATURE_SUBCLASSES = set(
    [
        "Blood Curse",
        "Artificer Infusions",
    ]
)
DB_ID = "4ef5625c1efa82ee840201ed25c122a0"

CLASSES_DIR = REPO_ROOT / "artifacts" / "cleaned_classes"
ICONS_FILE = CLASSES_DIR / "class_icons.json"
SHARED_FILE = "shared.json"

FALLBACK_ICON = "hexagon-three-sixths"
FALLBACK_COLOR = "gray"

# colors the Notion icon API accepts ("white" from class_icons.json is not one)
API_COLORS = {
    "gray",
    "lightgray",
    "brown",
    "yellow",
    "orange",
    "green",
    "blue",
    "purple",
    "pink",
    "red",
}

# Notion rejects a single rich_text content longer than this
MAX_RICH_TEXT = 2000
# Notion rejects more than this many block children per append request
MAX_CHILDREN = 100


def _load_icons() -> Dict[str, dict]:
    if not ICONS_FILE.exists():
        return {}
    return {entry["key"]: entry for entry in json.load(open(ICONS_FILE))}


def _icon_for(name: str, icons: Dict[str, dict]) -> dict:
    entry = icons.get(name)
    icon_name = entry["value"] if entry else FALLBACK_ICON
    color = entry["color"] if entry else FALLBACK_COLOR
    if color not in API_COLORS:
        color = FALLBACK_COLOR
    return {"type": "icon", "icon": {"name": icon_name, "color": color}}


def _properties(
    name: str,
    classes: List[str],
    subclasses: List[str],
    level: int,
    uses: int | dict[int | str, int | str] | str | None,
) -> dict:
    uses_value = serialize_uses(uses)
    return {
        "Name": {"title": [{"text": {"content": name}}]},
        "Class": {"multi_select": [{"name": c} for c in classes]},
        "Subclass": {"multi_select": [{"name": s} for s in subclasses]},
        "_ismanual": {"checkbox": False},
        "_uselist": {
            "rich_text": [{"type": "text", "text": {"content": uses_value or ""}}]
        },
        "Important Effects": {"rich_text": []},
        "Total Uses": {"select": None},
        "Remaining Uses": {"select": None},
        "Level": {"number": level},
        # "Class/Level": {"relation:", "2b65625c-1efa-8022-b358-e55c4d02a510"},
    }


def _rich_text(content: str) -> List[dict]:
    return [
        {"type": "text", "text": {"content": content[i : i + MAX_RICH_TEXT]}}
        for i in range(0, len(content), MAX_RICH_TEXT)
    ]


def _description_blocks(description: str) -> List[dict]:
    blocks: List[dict] = []
    for paragraph in (description or "").split("\n\n"):
        paragraph = paragraph.strip("\n")
        if not paragraph.strip():
            continue
        block_type = "paragraph"
        if paragraph[:1] == bullet_char:
            block_type = "bulleted_list_item"
            paragraph = paragraph[1:].strip()
        blocks.append(
            {
                "object": "block",
                "type": block_type,
                block_type: {"rich_text": _rich_text(paragraph)},
            }
        )
    return blocks


def _iter_features():
    """yield (name, description, classes, subclasses, level, uses) for every feature"""

    def transform(feature, classes, subclasses):
        return (
            feature["name"],
            feature.get("description", ""),
            classes,
            subclasses,
            feature["level"],
            feature.get("uses"),
        )

    for path in sorted(CLASSES_DIR.glob("*_features.json")):
        features = json.load(open(path))
        if path.name == SHARED_FILE:
            for feature in features:
                classes, subclasses = [], []
                for entry in feature["classes"]:
                    if entry["character_class"] not in classes:
                        classes.append(entry["character_class"])
                    subclass = entry.get("subclass")
                    if subclass and subclass not in subclasses:
                        subclasses.append(subclass)
                yield transform(feature, classes, subclasses)
        else:
            for feature in features:
                if (
                    feature.get("subclass")
                    and feature["subclass"] in NON_FEATURE_SUBCLASSES
                ):
                    continue
                yield transform(
                    feature,
                    [feature["character_class"]],
                    [feature["subclass"]] if feature.get("subclass") else [],
                )


def put_class_features() -> None:
    if not DB_ID:
        raise SystemExit("Set DB_ID at the top of this script before running.")

    notion = Notion()
    icons = _load_icons()

    created = 0
    failed = 0
    for name, description, classes, subclasses, level, uses in _iter_features():
        try:
            page = notion.insert_into_db(
                DB_ID,
                _properties(name, classes, subclasses, level, uses),
                _icon_for(name, icons),
            )

            blocks = _description_blocks(description)
            for start in range(0, len(blocks), MAX_CHILDREN):
                notion.client.blocks.children.append(
                    page["id"], children=blocks[start : start + MAX_CHILDREN]
                )
            created += 1
            print(f"created: {name} ({', '.join(classes)})")
        except Exception as exc:  # keep going on individual failures
            failed += 1
            print(f"FAILED: {name} -> {exc}")

    print(f"\ndone: {created} created, {failed} failed")


if __name__ == "__main__":
    put_class_features()
