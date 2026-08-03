from unittest import TestCase

import os

from misc_loader.class_features import (
    _class_feature_choice,
    _parse_base_class,
    _parse_subclass,
)
from shared.model import ClassFeature

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "test_html")


def _load_fixture(page_key: str) -> str:
    with open(os.path.join(FIXTURE_DIR, page_key + ".html")) as fp:
        return fp.read()


def _by_name(features, name) -> ClassFeature:
    for feature in features:
        if feature.name == name:
            return feature
    raise Exception(f"Feature not found: {name}")


class TestSpellScraper(TestCase):
    def test_detects_subclass_choice_features(self):
        choice, placeholder = _class_feature_choice(
            "Roguish Archetype",
            "At 3rd level, you choose an archetype that you emulate in the exercise of your rogue abilities.",
        )
        self.assertTrue(choice)
        self.assertEqual(
            placeholder,
            "Pick your subclass where you set your class (top left)",
        )

    def test_detects_artificer_specialist_choice(self):
        choice, placeholder = _class_feature_choice(
            "Artificer Specialist",
            "At 3rd level, you choose the type of specialist you are. Your choice grants you features at 5th level and again at 9th and 15th level.",
        )
        self.assertTrue(choice)
        self.assertEqual(
            placeholder,
            "Pick your subclass where you set your class (top left)",
        )

    def test_ignores_non_choice_features(self):
        choice, placeholder = _class_feature_choice(
            "Cunning Action",
            "Starting at 2nd level, your quick thinking and agility allow you to move and act quickly.",
        )
        self.assertFalse(choice)
        self.assertIsNone(placeholder)

    def test_detects_choice_noun_phrasing(self):
        # "a bard college of your choice" uses the noun "choice", not "choose"
        choice, placeholder = _class_feature_choice(
            "Bard College",
            "At 3rd level, you delve into the advanced techniques of a bard college of your choice.",
        )
        self.assertTrue(choice)
        self.assertEqual(
            placeholder,
            "Pick your subclass where you set your class (top left)",
        )


class TestBaseClassFixture(TestCase):
    """regression tests for _parse_base_class against fixtures/test_html/barbarian.html"""

    @classmethod
    def setUpClass(cls):
        cls.features, cls.subclass_keys = _parse_base_class(
            _load_fixture("barbarian"), "Barbarian"
        )

    def test_parses_expected_feature_names(self):
        names = [f.name for f in self.features]
        self.assertEqual(
            names,
            [
                "Hit Points",
                "Proficiencies",
                "Equipment",
                "Rage",
                "Unarmored Defense",
                "Danger Sense",
                "Reckless Attack",
                "Primal Path",
                "Primal Knowledge",
                "Ability Score Improvement",
                "Extra Attack",
                "Fast Movement",
                "Feral Instinct",
                "Instinctive Pounce",
                "Brutal Critical",
                "Relentless Rage",
                "Persistent Rage",
                "Indomitable Might",
                "Primal Champion",
            ],
        )

    def test_levels_come_from_progression_table(self):
        self.assertEqual(_by_name(self.features, "Reckless Attack").level, 2)
        self.assertEqual(_by_name(self.features, "Extra Attack").level, 5)
        self.assertEqual(_by_name(self.features, "Primal Champion").level, 20)

    def test_rage_uses_are_table_breakpoints(self):
        res = _by_name(self.features, "Rage")
        self.assertEqual(
            res.uses,
            {1: 2, 3: 3, 6: 4, 12: 5, 17: 6, 20: "Unlimited"},
        )

    def test_primal_path_is_a_subclass_choice(self):
        self.assertTrue(_by_name(self.features, "Primal Path").is_choice)

    def test_optional_suffix_stripped_from_name(self):
        # "Primal Knowledge (Optional)" -> "Primal Knowledge"
        names = [f.name for f in self.features]
        self.assertIn("Primal Knowledge", names)
        self.assertNotIn("Primal Knowledge (Optional)", names)

    def test_subclass_index_table_not_in_description(self):
        primal_path = _by_name(self.features, "Primal Path")
        self.assertNotIn("Ancestral Guardian", primal_path.description)

    def test_discovers_subclass_page_keys(self):
        self.assertIn("barbarian:ancestral-guardian", self.subclass_keys)
        self.assertIn("barbarian:zealot", self.subclass_keys)
        # unearthed arcana subclasses are discovered too
        self.assertIn("barbarian:beast-ua", self.subclass_keys)


class TestSubclassFixtures(TestCase):
    """regression tests for _parse_subclass across several fixture pages"""

    def test_ancestral_guardian_metadata_and_uses(self):
        features = _parse_subclass(
            _load_fixture("barbarian:ancestral-guardian"), "Barbarian"
        )
        self.assertEqual(features[0].subclass, "Path of the Ancestral Guardian")
        self.assertEqual(features[0].source, "Xanathar's Guide to Everything")
        names = [f.name for f in features]
        self.assertEqual(
            names,
            [
                "Ancestral Protectors",
                "Spirit Shield",
                "Consult the Spirits",
                "Vengeful Ancestors",
            ],
        )
        # "you can't use it again until you finish a short or long rest" -> 1 use
        self.assertEqual(_by_name(features, "Consult the Spirits").uses, 1)

    def test_subsection_headers_fold_into_parent_feature(self):
        features = _parse_subclass(_load_fixture("bard:creation-ua"), "Bard")
        names = [f.name for f in features]
        # the h5 "Dancing Item" and h6 "Actions" stat-block sub-headers must NOT
        # become their own features
        self.assertEqual(
            names,
            ["Note of Potential", "Animating Performance", "Performance of Creation"],
        )
        animating = _by_name(features, "Animating Performance")
        self.assertIn("Dancing Item", animating.description)
        self.assertIn("Actions (Require Your Bonus Action)", animating.description)
        self.assertIn("Force-Empowered Slam", animating.description)

    def test_level_uses_first_ordinal_not_minimum(self):
        features = _parse_subclass(_load_fixture("bard:creation-ua"), "Bard")
        # "By 6th level ... expend a spell slot of 3rd level or higher" -> 6, not 3
        self.assertEqual(_by_name(features, "Animating Performance").level, 6)
        # "At 14th level ... a spell slot of 5th level or higher" -> 14, not 5
        self.assertEqual(_by_name(features, "Performance of Creation").level, 14)

    def test_content_table_included_in_description(self):
        features = _parse_subclass(_load_fixture("warlock:celestial"), "Warlock")
        expanded = _by_name(features, "Expanded Spell List")
        self.assertIn("Cure Wounds", expanded.description)
        self.assertIn("Flame Strike", expanded.description)
        self.assertIn(
            "[Cure Wounds](http://dnd5e.wikidot.com/spell:cure-wounds)",
            expanded.description,
        )
        self.assertIn(
            "[Flame Strike](http://dnd5e.wikidot.com/spell:flame-strike)",
            expanded.description,
        )
        # once-per-rest feature
        self.assertEqual(_by_name(features, "Searing Vengeance").uses, 1)

    def test_multiclass_subclass_level_header(self):
        features = _parse_subclass(
            _load_fixture("multisubclass:mage-of-lorehold-ua"), "Warlock"
        )
        self.assertEqual(features[0].subclass, "Mage of Lorehold UA")
        # "Level 6+ Mage of Lorehold Feature ..." header sets the level
        self.assertEqual(_by_name(features, "Lessons of the Past").level, 6)
        self.assertEqual(_by_name(features, "War Echoes").level, 10)
