from unittest import TestCase

from misc_loader.class_features import _class_feature_choice


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
