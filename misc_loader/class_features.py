import os
import re
from typing import Dict, List, Optional, Tuple
import time
from bs4 import BeautifulSoup, Tag

from shared.helpers import write_obj_to_json
from shared.model import CharacterClass, ClassFeature
from shared.requestor import base_url, make_get_request

TEST_HTML_DIR = "./fixtures/test_html"
OUTPUT_DIR = "./artifacts/classes"

ORDINAL_RE = re.compile(r"(\d+)(?:st|nd|rd|th)\s+level", re.IGNORECASE)
# UA multiclass subclasses lead each feature with "Level 6+ <Subclass> Feature"
FEATURE_LEVEL_RE = re.compile(r"\bLevel (\d+)\+?\s+[^.]*?\bFeature\b", re.IGNORECASE)
LEVEL_RE = re.compile(r"(\d+)")

# wikidot descriptions mix curly and straight apostrophes; normalize before matching
_APOSTROPHES = str.maketrans({"\u2019": "'", "\u2018": "'"})

NUMBER_WORDS = {
    "once": 1,
    "one": 1,
    "twice": 2,
    "two": 2,
    "thrice": 3,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}

ONCE_PER_REST_RE = re.compile(
    r"can't use (?:it|this feature) again until you finish", re.IGNORECASE
)
# alternate once-per-rest phrasing: "you must finish a short or long rest ... to use it again"
MUST_REST_RE = re.compile(
    r"must finish a[n]? (?:short|long|short or long)[a-z ]*rest"
    r"[^.]{0,80}\b(?:use|do)\b[^.]{0,30}\bagain\b",
    re.IGNORECASE,
)
# "a number of times equal to ..." — a calculation-based count (ability modifier,
# proficiency bonus, etc). We deliberately leave `uses` null for these.
SCALING_USES_RE = re.compile(r"number of times equal to", re.IGNORECASE)
# an explicit fixed count, e.g. "you can use it twice" / "you can use this feature three times"
EXPLICIT_USES_RE = re.compile(
    r"you can use (?:it|this feature) "
    r"(once|twice|thrice|\d+ times|"
    r"(?:one|two|three|four|five|six|seven|eight|nine|ten) times)",
    re.IGNORECASE,
)


def _word_to_int(token: str) -> Optional[int]:
    """map a number word or digit token (optionally suffixed with 'times') to an int"""
    token = token.strip().lower().replace(" times", "").strip()
    if token.isdigit():
        return int(token)
    return NUMBER_WORDS.get(token)


def _uses_from_description(description: str) -> Optional[int]:
    """
    infer a feature's limited-use count from its prose. Returns the literal count for
    explicit "you can use it N times" phrasing, or 1 for once-per-rest features.
    Returns None when the description implies no per-rest limit, or when the count is
    calculation-based (e.g. scales with an ability modifier or proficiency bonus).
    """
    if not description:
        return None
    text = description.translate(_APOSTROPHES)
    if SCALING_USES_RE.search(text):
        return None
    explicit = EXPLICIT_USES_RE.search(text)
    if explicit:
        return _word_to_int(explicit.group(1))
    if ONCE_PER_REST_RE.search(text) or MUST_REST_RE.search(text):
        return 1
    return None


CHOICE_SUBCLASS_PLACEHOLDER = "Pick your subclass where you set your class (top left)"
SUBCLASS_CHOICE_KEYWORDS = (
    "archetype",
    "conclave",
    "oath",
    "domain",
    "patron",
    "tradition",
    "college",
    "circle",
    "path",
    "origin",
    "order",
)
SPECIALIZATION_CHOICE_PATTERNS = (
    re.compile(r"\b(type of|kind of)\s+(specialist|specialization)\b", re.IGNORECASE),
    re.compile(r"\b(specialist|specialization)\b", re.IGNORECASE),
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


def _page_content(html: str) -> Tag:
    """parse html and return the #page-content Tag, raising if it's missing"""
    soup = BeautifulSoup(html, "html.parser")
    content = soup.find("div", id="page-content")
    if not isinstance(content, Tag):
        raise ValueError("page-content div not found")
    return content


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


def _render_table(table: Tag) -> str:
    """flatten a table into text, one line per row with cells joined by ' | '"""
    lines: List[str] = []
    for row in table.find_all("tr"):
        cells = [_clean_text(c) for c in row.find_all(["th", "td"])]
        cells = [c for c in cells if c]
        if cells:
            lines.append(" | ".join(cells))
    return "\n".join(lines)


def _iter_features(container: Tag, skip_table_re: Optional[re.Pattern] = None):
    """
    walk a page-content container in document order, yielding (name, description)
    tuples. A feature starts at a header and its description is every block of
    content that follows (paragraphs, lists, and tables) until the next header at
    the same or a shallower level. A deeper header (e.g. an h5 "Dancing Item" stat
    block under an h3 feature) is a subsection: its heading and content fold into
    the current feature's description rather than starting a new one. Tables whose
    links match ``skip_table_re`` (the subclass-index table) are skipped so the
    subclass list doesn't leak into a feature description.
    """
    heading_tags = ("h2", "h3", "h4", "h5", "h6")
    current_name = None
    current_level = 0
    current_desc: List[str] = []
    for node in container.find_all([*heading_tags, "p", "ul", "table"]):
        if node.name in heading_tags:
            level = int(node.name[1])
            text = _clean_text(node)
            if current_name is not None and level > current_level:
                # subsection of the current feature: keep its heading in the description
                if text:
                    current_desc.append(text)
                continue
            if current_name is not None:
                yield current_name, "\n\n".join(current_desc).strip()
            current_name = text
            current_level = level
            current_desc = []
        elif current_name is not None:
            if node.name == "table":
                if skip_table_re and any(
                    skip_table_re.match(str(a["href"]).strip())
                    for a in node.find_all("a", href=True)
                ):
                    continue
                text = _render_table(node)
                if text:
                    current_desc.append(text)
            elif node.find_parent("table") is not None:
                # already captured as part of a rendered table; don't double-count
                continue
            elif node.name == "ul":
                for li in node.find_all("li"):
                    current_desc.append("\u2022 " + _clean_text(li))
            else:
                text = _clean_text(node)
                if text:
                    current_desc.append(text)
    if current_name is not None:
        yield current_name, "\n\n".join(current_desc).strip()


def _prose_level(description: str) -> Optional[int]:
    header = FEATURE_LEVEL_RE.search(description)
    if header:
        return int(header.group(1))
    # the opening clause states the level the feature is gained ("By 6th level ...");
    # later mentions (e.g. "a spell slot of 3rd level or higher") are unrelated, so
    # take the first ordinal rather than the minimum.
    match = ORDINAL_RE.search(description)
    return int(match.group(1)) if match else None


def _class_feature_choice(name: str, description: str) -> Tuple[bool, Optional[str]]:
    """return (is_choice_feature, placeholder_subclass_value) for subclass pickers"""
    text = f"{name}\n{description}".lower()
    if not text:
        return False, None

    has_choice_phrase = (
        re.search(r"\b(choose|choosing|choice|pick|select)\b", text) is not None
    )
    has_subclass_keyword = any(keyword in text for keyword in SUBCLASS_CHOICE_KEYWORDS)
    has_specialization_choice = any(
        pattern.search(text) for pattern in SPECIALIZATION_CHOICE_PATTERNS
    )
    if has_choice_phrase and (has_subclass_keyword or has_specialization_choice):
        return True, CHOICE_SUBCLASS_PLACEHOLDER
    return False, None


def _merge_feature(features: Dict[str, ClassFeature], feature: ClassFeature) -> None:
    """
    add a feature, improving an existing one instead of duplicating it when the
    (normalized) name already exists.
    """
    key = _normalize_name(feature.name)
    if key in features:
        existing = features[key]
        existing.level = min(existing.level, feature.level)
        existing.is_choice = existing.is_choice or feature.is_choice
        if feature.description and feature.description not in existing.description:
            existing.description = (
                existing.description + "\n\n" + feature.description
            ).strip()
        if existing.uses is None:
            existing.uses = feature.uses
        if feature.subclass is not None:
            existing.subclass = feature.subclass
    else:
        features[key] = feature


def _parse_base_class(
    html: str, char_class: str
) -> Tuple[List[ClassFeature], List[str]]:
    """returns (base features, subclass page keys linked from this page)"""
    content = _page_content(html)

    feature_levels: Dict[str, int] = {}
    resource_breakpoints: Dict[str, dict] = {}
    tables = content.find_all("table", {"class": "wiki-content-table"})
    if tables:
        feature_levels, resource_breakpoints = _parse_level_table(tables[0])

    page_key = _class_page_key(char_class)
    subclass_href_re = _subclass_href_re(page_key)

    features: Dict[str, ClassFeature] = {}
    for name, description in _iter_features(content, subclass_href_re):
        if _normalize_name(name) == "class features":
            continue
        feature = ClassFeature()
        feature.name = _display_name(name)
        feature.description = description
        feature.character_class = char_class
        norm = _normalize_name(name)
        feature.level = feature_levels.get(norm) or _prose_level(description) or 1
        feature.is_choice, placeholder = _class_feature_choice(name, description)
        if feature.is_choice:
            feature.subclass = placeholder
        if norm in resource_breakpoints:
            feature.uses = resource_breakpoints[norm]
        else:
            feature.uses = _uses_from_description(description)
        _merge_feature(features, feature)

    page_key = _class_page_key(char_class)
    subclasses = _find_subclass_keys(content, page_key)
    return list(features.values()), subclasses


def _subclass_href_re(class_page_key: str) -> re.Pattern:
    """regex matching an anchor href that points to a subclass page (e.g.
    "barbarian:ancestral-guardian" or a shared "multisubclass:mage-of-lorehold-ua")"""
    return re.compile(
        r"^(?:https?://dnd5e\.wikidot\.com)?/("
        + r"(?:"
        + re.escape(class_page_key)
        + r"|multisubclass)"
        + r":[a-z0-9-]+)$"
    )


def _find_subclass_keys(content: Tag, class_page_key: str) -> List[str]:
    """collect unique subclass page keys (e.g. "barbarian:ancestral-guardian" or
    a shared "multisubclass:mage-of-lorehold-ua")"""
    keys: List[str] = []
    seen = set()
    pattern = _subclass_href_re(class_page_key)
    for anchor in content.find_all("a", href=True):
        match = pattern.match(str(anchor["href"]).strip())
        if match:
            key = match.group(1)
            if key not in seen:
                seen.add(key)
                keys.append(key)
    return keys


def _parse_subclass(html: str, char_class: str) -> List[ClassFeature]:
    soup = BeautifulSoup(html, "html.parser")
    content = soup.find("div", id="page-content")
    if not isinstance(content, Tag):
        raise ValueError("page-content div not found")

    title = soup.find("div", class_="page-title")
    subclass_name = _clean_text(title) if isinstance(title, Tag) else ""
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
    for name, description in _iter_features(
        content, _subclass_href_re(_class_page_key(char_class))
    ):
        feature = ClassFeature()
        feature.name = _display_name(name)
        feature.description = description
        feature.character_class = char_class
        feature.subclass = subclass_name
        feature.level = _prose_level(description) or 3
        feature.uses = _uses_from_description(description)
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

    def run(for_class: CharacterClass):
        page_key = _class_page_key(for_class)
        html = _load_html(page_key, is_dry_run)
        if not html:
            print("could not load page for " + for_class)
            return []

        all_features, subclass_keys = _parse_base_class(html, for_class)

        for subclass_key in subclass_keys:
            subclass_html = _load_html(subclass_key, is_dry_run)
            if not subclass_html:
                print("skipping (no html): " + subclass_key)
                continue
            all_features.extend(_parse_subclass(subclass_html, for_class))

        if save:
            write_obj_to_json(
                all_features,
                os.path.join(
                    OUTPUT_DIR,
                    page_key + ("_DRY_RUN" if is_dry_run else "") + "_features.json",
                ),
            )
        return all_features

    if char_class == "all":
        all_feats = []
        for cc in CharacterClass:
            print("scraping ", cc)
            all_feats.append(run(cc))
            time.sleep(5)
    else:
        return run(CharacterClass[char_class.capitalize()])
