"""
Generate artifacts/classes/class_icons.json: one icon entry per unique class
feature name.

Each entry is {"key": <feature name>, "value": <icon>, "color": <color>}. Icons
are chosen by keyword-matching the feature's name and description against the
valid icon set in artifacts/icons.json; colors come from the allowed Notion
palette and are varied by theme. Features that match no keyword fall back to
"hexagon-three-sixths" / "brown".

The existing "Spellcasting" entry (magic-wand / blue) is preserved as-is.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Pattern, Tuple

ARTIFACTS = Path(__file__).resolve().parent.parent / "artifacts"
CLASSES_DIR = ARTIFACTS / "classes"
ICONS_FILE = ARTIFACTS / "icons.json"
OUTPUT_FILE = ARTIFACTS / "feature_icons.json"

# entries we must not regenerate / overwrite (curated by hand)
PRESERVE = {
    "Spellcasting": {"key": "Spellcasting", "value": "magic-wand", "color": "blue"},
}

FALLBACK_ICON = "hexagon-three-sixths"
FALLBACK_COLOR = "lightgray"

# allowed Notion colors for generated entries
COLORS = {
    "brown",
    "green",
    "purple",
    "pink",
    "red",
    "orange",
    "yellow",
    "lightgray",
    "white",
}

# ordered keyword rules: (keywords, candidate icons, candidate colors).
# each feature is scored against every rule (see _match): a keyword in the
# feature name counts heavily, a distinct keyword in the description counts a
# little, and the highest-scoring rule wins (earlier rules break ties). icon and
# color are chosen from the winning rule's candidate lists by a hash of the
# feature name so features in the same theme still vary in both icon and color.
RULES: List[Tuple[List[str], List[str], List[str]]] = [
    # --- elemental / damage themes -------------------------------------------
    (
        ["rage", "frenzy", "berserk", "fury", "reckless"],
        ["fire", "emoji-angry", "volcano"],
        ["red", "orange"],
    ),
    (
        ["fire", "flame", "burning", "ignite", "ember", "inferno"],
        ["fire", "forest-fire", "volcano"],
        ["red", "orange"],
    ),
    (
        ["cold", "frost", "ice", "freezing", "chill", "frozen"],
        ["snowflake", "temperature-cool"],
        ["lightgray", "white"],
    ),
    (
        ["lightning", "thunder", "storm", "shock", "electric"],
        ["flash", "storm"],
        ["yellow", "purple"],
    ),
    (["acid", "poison", "venom", "toxic"], ["snake", "bug", "chemistry"], ["green"]),
    (
        ["gust", "gale", "cyclone", "tempest", "whirlwind", "windstorm"],
        ["wind", "tornado", "hurricane"],
        ["lightgray", "green"],
    ),
    (
        ["water", "tide", "wave", "aquatic", "sea", "ocean"],
        ["water", "sailboat", "anchor"],
        ["lightgray", "white"],
    ),
    # --- divine / holy / radiant ---------------------------------------------
    (
        [
            "radiant",
            "holy",
            "divine",
            "sacred",
            "blessing",
            "bless",
            "sanctuary",
            "consecrate",
            "oath",
            "tenet",
            "paladin",
            "saint",
        ],
        ["church", "temple", "star-of-life", "torii", "sun", "asterisk"],
        ["yellow", "white", "brown"],
    ),
    (
        ["channel divinity", "turn undead", "smite"],
        ["judicial-scales", "star-of-life", "sword"],
        ["yellow", "white"],
    ),
    (
        ["light", "shining", "sunlight", "dawn", "beacon"],
        ["sun", "light-bulb", "brightness-high", "sunrise", "asterisk"],
        ["yellow", "white"],
    ),
    # --- death / shadow / fear -----------------------------------------------
    (
        [
            "necro",
            "undead",
            "death",
            "grave",
            "corpse",
            "bone",
            "skeleton",
            "wraith",
            "revenant",
        ],
        ["skull", "skull-profile", "grave", "bone", "long-bone"],
        ["brown", "lightgray"],
    ),
    (
        ["shadow", "dark", "night", "gloom", "umbral", "eldritch"],
        ["moon", "partly-cloudy-night", "ghost", "asterisk"],
        ["purple", "brown"],
    ),
    (
        ["fear", "frighten", "terror", "dread", "intimidat"],
        ["ghost", "skull", "emoji-surprised"],
        ["purple", "brown"],
    ),
    (
        ["curse", "hex", "doom", "malediction"],
        ["skull", "ghost", "bomb"],
        ["purple", "brown"],
    ),
    # --- arcane / psionic / sorcery ------------------------------------------
    (
        ["psionic", "psychic", "psi", "telepath", "mind"],
        ["brain", "thought"],
        ["purple", "pink"],
    ),
    (
        [
            "arcane",
            "sorcer",
            "spell point",
            "font of magic",
            "wild magic",
            "eldritch invocation",
            "magic",
            "mystic",
            "conjur",
            "enchant",
            "evocation",
            "abjur",
            "transmut",
            "illusion",
            "necromanc",
            "alchemy",
            "sculpt",
        ],
        ["magic-wand", "gem", "stars", "flash"],
        ["purple", "pink"],
    ),
    (
        ["ritual", "rune", "sigil", "glyph", "ward"],
        ["hashtag", "reference", "gem"],
        ["purple", "brown"],
    ),
    (
        ["summon", "conjure", "invoke", "manifest", "echo", "avatar"],
        ["stars", "orbit", "magic-wand"],
        ["purple", "pink"],
    ),
    (
        ["teleport", "blink", "misty step", "planar", "portal", "plane"],
        ["orbit", "ringed-planet", "flash"],
        ["purple", "pink"],
    ),
    # --- nature / beast ------------------------------------------------------
    (
        ["wild shape", "beast", "animal", "companion", "primal", "wild", "swarm"],
        ["cat", "hare", "fish", "butterfly", "bug"],
        ["green", "orange"],
    ),
    (
        [
            "plant",
            "forest",
            "grove",
            "nature",
            "leaf",
            "bloom",
            "thorn",
            "vine",
            "entangle",
            "land's stride",
            "circle of",
        ],
        ["leaf", "tree", "conifer-tree", "clover", "mushroom", "cactus", "grain"],
        ["green", "brown"],
    ),
    (
        [
            "track",
            "hunter",
            "quarry",
            "prey",
            "favored",
            "explorer",
            "terrain",
            "natural",
            "conclave",
        ],
        ["compass", "binoculars", "map", "target"],
        ["green", "orange"],
    ),
    # --- combat / martial ----------------------------------------------------
    (
        [
            "extra attack",
            "attack",
            "strike",
            "weapon",
            "martial",
            "blade",
            "melee",
            "maneuver",
            "superiority",
            "cleave",
            "fighting style",
            "fighting",
        ],
        ["sword", "chess-knight"],
        ["red", "yellow", "lightgray"],
    ),
    (
        ["archery", "ranged", "arrow", "bow", "shot", "sharpshoot"],
        ["archery", "target", "bullseye"],
        ["red", "orange", "lightgray"],
    ),
    (
        [
            "armor",
            "shield",
            "guard",
            "defense",
            "defence",
            "protect",
            "resist",
            "parry",
            "deflect",
            "block",
            "indomitable",
        ],
        ["shield"],
        ["lightgray", "brown", "yellow", "purple"],
    ),
    (
        [
            "stealth",
            "sneak",
            "hide",
            "hidden",
            "cunning",
            "ambush",
            "assassin",
            "shadow step",
            "roguish",
            "disguise",
            "mask",
            "myriad",
        ],
        ["view-off", "conceal", "shade-contrast"],
        ["lightgray", "purple", "white"],
    ),
    (
        [
            "perception",
            "sight",
            "vision",
            "insight",
            "detect",
            "sense",
            "awareness",
            "darkvision",
        ],
        ["view", "binoculars", "telescope"],
        ["yellow", "lightgray"],
    ),
    # --- movement / speed ----------------------------------------------------
    (
        [
            "speed",
            "dash",
            "step",
            "movement",
            "swift",
            "fleet",
            "mobility",
            "nimble",
            "sprint",
        ],
        ["run", "walk"],
        ["orange", "green"],
    ),
    (
        ["fly", "flight", "wing", "soar", "aerial"],
        ["feather", "hot-air-balloon", "airplane"],
        ["lightgray", "white"],
    ),
    (
        ["climb", "swim", "jump", "leap"],
        ["mountains", "sailboat"],
        ["green", "lightgray"],
    ),
    # --- mind / social -------------------------------------------------------
    (
        [
            "persuas",
            "deception",
            "charm",
            "charisma",
            "social",
            "diplomat",
            "influence",
            "command",
            "leadership",
            "inspire",
            "inspiration",
        ],
        ["chat", "conversation", "dialogue", "megaphone"],
        ["pink", "orange"],
    ),
    (
        [
            "knowledge",
            "lore",
            "study",
            "learn",
            "research",
            "wisdom",
            "intelligence",
            "arcana",
            "recall",
            "memory",
            "spell list",
        ],
        ["book", "book-closed", "library", "gradebook"],
        ["brown", "yellow", "lightgray", "white"],
    ),
    # --- craft / tools -------------------------------------------------------
    (
        [
            "craft",
            "tool",
            "artific",
            "infus",
            "forge",
            "tinker",
            "construct",
            "invent",
            "engineer",
        ],
        ["gear", "gears", "wrench", "hammer", "screwdriver"],
        ["lightgray", "orange"],
    ),
    (
        ["firearm", "gun", "cannon", "explos", "bomb", "grenade", "alchemist"],
        ["bomb", "flash"],
        ["orange", "red"],
    ),
    # --- healing / life ------------------------------------------------------
    (
        [
            "heal",
            "cure",
            "restore",
            "recover",
            "revive",
            "life",
            "vitality",
            "mending",
            "second wind",
            "regain",
        ],
        ["first-aid", "first-aid-kit", "heart-rate", "star-of-life"],
        ["pink", "red"],
    ),
    (
        [
            "health",
            "hit point",
            "hit dice",
            "endurance",
            "tough",
            "hardy",
            "constitution",
            "durable",
            "stamina",
        ],
        ["heart", "heart-rate", "bone"],
        ["red", "pink"],
    ),
    # --- music / bard --------------------------------------------------------
    (
        ["song", "music", "melody", "tune", "bard", "performance", "instrument"],
        ["music", "guitar", "violin", "trumpet", "note-quarter", "piano"],
        ["pink", "purple"],
    ),
    # --- fortune / resources -------------------------------------------------
    (
        ["luck", "fortune", "fate", "chance", "reroll", "lucky"],
        ["clover-four-leaf", "die6", "cards"],
        ["green", "yellow"],
    ),
    (
        ["gold", "treasure", "wealth", "coin", "money"],
        ["currency-coin", "gem", "cash"],
        ["yellow"],
    ),
    # --- utility / meta ------------------------------------------------------
    (
        ["ability score improvement", "improvement"],
        ["star", "chart-line"],
        ["yellow", "orange"],
    ),
    (
        [
            "ki",
            "monk",
            "monastic",
            "martial arts",
            "flurry",
            "patient",
            "empty body",
            "stillness",
        ],
        ["yin-yang", "hand"],
        ["orange", "brown"],
    ),
    (
        ["sleep", "meditat", "trance", "long rest", "short rest", "slumber"],
        ["bed", "moon", "hourglass"],
        ["lightgray", "purple"],
    ),
    (
        ["action surge", "bonus action", "reaction", "haste", "quick"],
        ["flash", "stopwatch", "alarm"],
        ["yellow", "orange"],
    ),
    (
        ["aura", "radius", "nearby", "allies within", "presence"],
        ["orbit", "circle-dashed"],
        ["yellow", "purple"],
    ),
    (
        ["blood", "hemocraft", "crimson", "sanguine", "hunter's", "violent"],
        ["heart", "skull", "water"],
        ["red", "brown"],
    ),
    (["channel"], ["skull"], ["white", "lightgray"]),
    (
        ["pact", "warlock", "patron", "otherworld", "fiend", "genie"],
        ["gem", "ghost", "skull"],
        ["purple", "pink"],
    ),
    (
        ["key", "lock", "unlock", "thieves", "lockpick"],
        ["key", "lock", "unlock", "key-antique"],
        ["lightgray", "yellow"],
    ),
    (
        ["trap", "snare", "hazard", "danger", "alarm"],
        ["warning", "alert"],
        ["orange", "red"],
    ),
    (
        ["base features", "proficien", "equipment", "hit points"],
        ["list", "checklist"],
        ["lightgray", "brown"],
    ),
]


def _compile(keyword: str) -> Pattern[str]:
    """leading word-boundary (prefix/stem) match; whole-word for <=2 chars"""
    if len(keyword) <= 2:
        return re.compile(r"\b" + re.escape(keyword) + r"\b")
    return re.compile(r"\b" + re.escape(keyword))


# precompile each rule's keyword patterns once
COMPILED: List[Tuple[List[Pattern[str]], List[str], List[str]]] = [
    ([_compile(kw) for kw in keywords], icons, colors)
    for keywords, icons, colors in RULES
]


def _pick(options: List[str], seed: str, salt: int) -> str:
    return options[(hash((seed, salt)) & 0x7FFFFFFF) % len(options)]


# a keyword found in the feature *name* is far stronger evidence of its theme than
# one buried in the description, where unrelated mechanics (e.g. "charmed",
# "frightened") are frequently mentioned in passing. Scoring by the number of
# distinct keywords a rule matches also favours the rule a feature is genuinely
# about over one that happens to share a single incidental word.
NAME_WEIGHT = 5
DESC_WEIGHT = 1


def _rule_score(
    patterns: List[Pattern[str]], name: str, description: str
) -> Tuple[int, int]:
    """(name keyword hits, distinct description keyword hits) for a rule."""
    name_hits = sum(1 for p in patterns if p.search(name))
    desc_hits = sum(1 for p in patterns if p.search(description))
    return name_hits, desc_hits


def _unique_feature_names() -> List[str]:
    names: Dict[str, str] = {}
    files = sorted(CLASSES_DIR.glob("*_features.json"))
    for path in files:
        if path.name in {"class_icons.json"}:
            continue
        for feature in json.load(open(path)):
            name = feature["name"]
            if name not in names:
                names[name] = feature.get("description") or ""
    return list(names.items())  # type: ignore[return-value]


def _match(name: str, description: str, valid: set) -> Optional[Tuple[str, str]]:
    """choose the highest-scoring rule; earlier (more specific) rules win ties."""
    name_l, description_l = name.lower(), description.lower()
    best_score = 0
    best: Optional[Tuple[List[str], List[str]]] = None
    for patterns, icons, colors in COMPILED:
        candidates = [i for i in icons if i in valid]
        if not candidates:
            continue
        name_hits, desc_hits = _rule_score(patterns, name_l, description_l)
        score = name_hits * NAME_WEIGHT + desc_hits * DESC_WEIGHT
        if score > best_score:
            best_score = score
            best = (candidates, colors)
    if best is None:
        return None
    icons, colors = best
    icon = _pick(icons, name, 1)
    color = _pick([c for c in colors if c in COLORS] or [FALLBACK_COLOR], name, 2)
    return icon, color


def _choose(name: str, description: str, valid: set) -> Tuple[str, str]:
    return _match(name, description, valid) or (FALLBACK_ICON, FALLBACK_COLOR)


def generate() -> None:
    valid = set(json.load(open(ICONS_FILE)))
    entries: List[dict] = []
    fallback = 0
    for name, description in _unique_feature_names():
        if name in PRESERVE:
            entries.append(PRESERVE[name])
            continue
        icon, color = _choose(name, description, valid)
        if icon == FALLBACK_ICON:
            fallback += 1
        entries.append({"key": name, "value": icon, "color": color})

    with open(OUTPUT_FILE, "w") as fp:
        json.dump(entries, fp, indent=4)

    print(f"wrote {len(entries)} icon entries -> {OUTPUT_FILE.name}")
    print(f"{fallback} used the {FALLBACK_ICON} fallback")


if __name__ == "__main__":
    generate()
