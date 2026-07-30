import os
import re
from typing import Dict, List, Optional, Tuple

from bs4 import BeautifulSoup, Tag

from shared.helpers import write_obj_to_json
from shared.model import CharacterClass, ClassFeature
from shared.requestor import base_url, make_get_request

TEST_HTML_DIR = "./generator/test_html"
OUTPUT_DIR = "./misc_loader"

ORDINAL_RE = re.compile(r"(\d+)(?:st|nd|rd|th)\s+level", re.IGNORECASE)
LEVEL_RE = re.compile(r"(\d+)")
ONCE_PER_REST_RE = re.compile(
    r"can'?t use (?:it|this feature) again until you finish", re.IGNORECASE
)


def _clean_text(node: Tag) -> str:
    """collapse whitespace and strip the non-breaking spaces wikidot litters everywhere"""
    return re.sub(r"\s+", " ", node.get_text().replace("\xa0", " ")).strip()


def _normalize_name(name: str) -> str:
    """lower-cased name with parentheticals removed, used to match/merge features"""
    name = re.sub(r"\(.*?\)", "", name)
    return re.sub(r"\s+", " ", name).strip().lower()


def _display_name(name: str) -> str:
    return re.sub(r"\s*\(Optional\)\s*$", "", name.strip()).strip()


def _class_page_key(char_class: str) -> str:
    return char_class.lower().replace(" ", "-")


def _load_html(page_key: str, is_dry_run: bool) -> Optional[str]:
    """read a local fixture when doing a dry run, otherwise fetch the live page"""
    if is_dry_run:
        path = os.path.join(TEST_HTML_DIR, page_key + ".html")
        if os.path.exists(path):
            with open(path, "r") as fp:
                return fp.read()
        return None
    return make_get_request(base_url + "/" + page_key)


def _parse_level_table(table: Tag) -> Tuple[Dict[str, int], Dict[str, dict]]:
    """
    parse the class progression table.
    returns (feature_levels, resource_columns) where
        feature_levels maps a normalized feature name -> earliest level gained
        resource_columns maps a normalized (singularized) column name -> {level: value}
    """
    rows = table.find_all("tr")
    header_cells: List[str] = []
    header_idx = 0
    for idx, row in enumerate(rows):
        cells = [_clean_text(c) for c in row.find_all(["th", "td"])]
        if "Level" in cells and "Features" in cells:
            header_cells = cells
            header_idx = idx
            break
    if not header_cells:
        return {}, {}

    features_col = header_cells.index("Features")
    resource_cols = {
        i: header_cells[i] for i in range(len(header_cells)) if i > features_col
    }

    feature_levels: Dict[str, int] = {}
    resource_values: Dict[str, Dict[int, object]] = {
        name: {} for name in resource_cols.values()
    }

    for row in rows[header_idx + 1 :]:
        cells = row.find_all("td")
        if len(cells) < len(header_cells):
            continue
        level_match = LEVEL_RE.search(_clean_text(cells[0]))
        if not level_match:
            continue
        level = int(level_match.group(1))

        for feature in _clean_text(cells[features_col]).split(","):
            norm = _normalize_name(feature)
            if norm and (norm not in feature_levels or level < feature_levels[norm]):
                feature_levels[norm] = level

        for col_idx, col_name in resource_cols.items():
            value = _clean_text(cells[col_idx])
            resource_values[col_name][level] = int(value) if value.isdigit() else value

    # reduce each resource column to the levels where its value changes
    breakpoints: Dict[str, dict] = {}
    for col_name, per_level in resource_values.items():
        singular = _normalize_name(
            col_name[:-1] if col_name.endswith("s") else col_name
        )
        reduced: Dict[int, object] = {}
        last = object()
        for level in sorted(per_level):
            if per_level[level] != last:
                reduced[level] = per_level[level]
                last = per_level[level]
        breakpoints[singular] = reduced
    return feature_levels, breakpoints


def _iter_features(container: Tag):
    """
    walk a page-content container in document order, yielding (name, description)
    tuples. A feature starts at a header (h2-h6) and its description is every
    paragraph / list that follows until the next header. Tables are skipped so the
    subclass list doesn't leak into the Primal Path description.
    """
    current_name = None
    current_desc: List[str] = []
    for node in container.find_all(["h2", "h3", "h4", "h5", "h6", "p", "ul"]):
        if node.name in ("h2", "h3", "h4", "h5", "h6"):
            if current_name is not None:
                yield current_name, "\n\n".join(current_desc).strip()
            current_name = _clean_text(node)
            current_desc = []
        elif current_name is not None:
            if node.name == "ul":
                for li in node.find_all("li"):
                    current_desc.append("\u2022 " + _clean_text(li))
            else:
                text = _clean_text(node)
                if text:
                    current_desc.append(text)
    if current_name is not None:
        yield current_name, "\n\n".join(current_desc).strip()


def _prose_level(description: str) -> Optional[int]:
    levels = [int(m) for m in ORDINAL_RE.findall(description)]
    return min(levels) if levels else None


def _merge_feature(features: Dict[str, ClassFeature], feature: ClassFeature) -> None:
    """
    add a feature, improving an existing one instead of duplicating it when the
    (normalized) name already exists.
    """
    key = _normalize_name(feature.name)
    if key in features:
        existing = features[key]
        existing.level = min(existing.level, feature.level)
        if feature.description and feature.description not in existing.description:
            existing.description = (
                existing.description + "\n\n" + feature.description
            ).strip()
        if existing.uses is None:
            existing.uses = feature.uses
    else:
        features[key] = feature


def _parse_base_class(
    html: str, char_class: str
) -> Tuple[List[ClassFeature], List[str]]:
    """returns (base features, subclass page keys linked from this page)"""
    soup = BeautifulSoup(html, "html.parser")
    content = soup.find("div", id="page-content")

    feature_levels: Dict[str, int] = {}
    resource_breakpoints: Dict[str, dict] = {}
    tables = content.find_all("table", {"class": "wiki-content-table"})
    if tables:
        feature_levels, resource_breakpoints = _parse_level_table(tables[0])

    features: Dict[str, ClassFeature] = {}
    for name, description in _iter_features(content):
        if _normalize_name(name) == "class features":
            continue
        feature = ClassFeature()
        feature.name = _display_name(name)
        feature.description = description
        feature.character_class = char_class
        norm = _normalize_name(name)
        feature.level = feature_levels.get(norm) or _prose_level(description) or 1
        if norm in resource_breakpoints:
            feature.uses = resource_breakpoints[norm]
        elif ONCE_PER_REST_RE.search(description):
            feature.uses = 1
        _merge_feature(features, feature)

    page_key = _class_page_key(char_class)
    subclasses = _find_subclass_keys(content, page_key)
    return list(features.values()), subclasses


def _find_subclass_keys(content: Tag, class_page_key: str) -> List[str]:
    """collect unique subclass page keys (e.g. "barbarian:ancestral-guardian")"""
    keys: List[str] = []
    seen = set()
    pattern = re.compile(
        r"^(?:https?://dnd5e\.wikidot\.com)?/("
        + re.escape(class_page_key)
        + r":[a-z0-9-]+)$"
    )
    for anchor in content.find_all("a", href=True):
        match = pattern.match(anchor["href"].strip())
        if match:
            key = match.group(1)
            if key not in seen:
                seen.add(key)
                keys.append(key)
    return keys


def _parse_subclass(html: str, char_class: str) -> List[ClassFeature]:
    soup = BeautifulSoup(html, "html.parser")
    content = soup.find("div", id="page-content")

    title = soup.find("div", class_="page-title")
    subclass_name = _clean_text(title) if title else ""
    prefix = char_class + ":"
    if subclass_name.startswith(prefix):
        subclass_name = subclass_name[len(prefix) :].strip()

    source = None
    for p in content.find_all("p"):
        text = _clean_text(p)
        source_match = re.match(r"source:\s*(.+)", text, re.IGNORECASE)
        if source_match:
            source = source_match.group(1).strip()
            break

    features: Dict[str, ClassFeature] = {}
    for name, description in _iter_features(content):
        feature = ClassFeature()
        feature.name = _display_name(name)
        feature.description = description
        feature.character_class = char_class
        feature.subclass = subclass_name
        feature.level = _prose_level(description) or 3
        if ONCE_PER_REST_RE.search(description):
            feature.uses = 1
        _merge_feature(features, feature)

    for feature in features.values():
        feature.source = source
    return list(features.values())


def get_class_features(
    char_class: str | CharacterClass, is_dry_run: bool = False, save: bool = True
) -> List[ClassFeature]:
    """
    scrape every class feature (base class + subclasses) for a D&D 5e class.
    returns a flat list of ClassFeature objects; base features have subclass=None.
    """
    if isinstance(char_class, str):
        char_class = CharacterClass[char_class.capitalize()].value
    page_key = _class_page_key(char_class)
    html = _load_html(page_key, is_dry_run)
    if not html:
        print("could not load page for " + char_class)
        return []

    all_features, subclass_keys = _parse_base_class(html, char_class)

    for subclass_key in subclass_keys:
        subclass_html = _load_html(subclass_key, is_dry_run)
        if not subclass_html:
            print("skipping (no html): " + subclass_key)
            continue
        all_features.extend(_parse_subclass(subclass_html, char_class))

    if save:
        write_obj_to_json(
            all_features, os.path.join(OUTPUT_DIR, page_key + "_features.json")
        )
    return all_features


def load_class_features(char_class: str = "Barbarian", is_dry_run: bool = True):
    return get_class_features(char_class, is_dry_run=is_dry_run)


if __name__ == "__main__":
    load_class_features()
