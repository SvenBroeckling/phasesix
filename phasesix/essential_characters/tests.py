from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from .models import EssentialCharacter
from .rules import CENTURY_LEVELS, magic_slots, valid_attribute_distribution, valid_skill_distribution


class EssentialRuleTests(SimpleTestCase):
    def test_attribute_distribution(self):
        self.assertTrue(valid_attribute_distribution([3, 2, 2, 1, 1, 1, 0, 0]))
        self.assertFalse(valid_attribute_distribution([3, 3, 2, 1, 1, 1, 0, 0]))

    def test_skill_distribution(self):
        self.assertTrue(valid_skill_distribution([3, 2, 2, 2, 1, 1, 1, 1, 1]))
        self.assertFalse(valid_skill_distribution([3, 3, 2, 2, 1, 1, 1, 1, 1]))

    def test_magic_slots(self):
        self.assertEqual(magic_slots(0), {"aspects": 0, "spells": 0})
        self.assertEqual(magic_slots(1), {"aspects": 1, "spells": 3})
        self.assertEqual(magic_slots(3), {"aspects": 2, "spells": 5})

    def test_century_levels(self):
        self.assertEqual(CENTURY_LEVELS[1], (1, 1))
        self.assertEqual(CENTURY_LEVELS[10], (6, 0))


class EssentialCharacterDerivedValueTests(SimpleTestCase):
    def setUp(self):
        self.character = EssentialCharacter(
            name="Mara",
            century=7,
            ancestry_custom="Human",
            path_custom="Wanderer",
            bond_custom="Home",
            mind=2,
            will=2,
            instinct=1,
            dexterity=3,
            body=1,
            presence=1,
            gift=0,
            perception=0,
        )

    def test_derived_values(self):
        self.assertEqual(self.character.wound_threshold, 4)
        self.assertEqual(self.character.burden_threshold, 6)
        self.assertEqual(self.character.initiative, 60)
        self.assertEqual(self.character.faith_level, 3)
        self.assertEqual(self.character.magic_level, 3)
        self.assertEqual(self.character.omen_max, 3)
        self.assertEqual(self.character.favor_limit, 2)
        self.assertEqual(self.character.arkana_max, 5)
        self.assertEqual(self.character.favor_max, 5)

    def test_rejects_invalid_attributes(self):
        self.character.gift = 3
        with self.assertRaises(ValidationError):
            self.character.clean()
