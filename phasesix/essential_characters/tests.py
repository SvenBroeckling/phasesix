from django.contrib.auth import get_user_model
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.http import QueryDict
from django.template.loader import render_to_string
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils.functional import Promise
from django.utils.translation import override
from unfold.admin import ModelAdmin

from armory.models import Item, RiotGear, Weapon, WeaponType
from magic.models import BaseSpell, SpellOrigin

from .definitions import ANCESTRIES, BONDS, PATHS
from .forms import (
    AttributesForm,
    ConceptForm,
    EquipmentForm,
    EssentialCharacterForm,
    MarksForm,
    SkillsForm,
)
from .models import (
    EssentialAncestry,
    EssentialBond,
    EssentialCharacter,
    EssentialCharacterSkill,
    EssentialPath,
)
from .rules import (
    CENTURY_LEVELS,
    magic_slots,
    valid_attribute_distribution,
    valid_skill_distribution,
)
from .views import EssentialCharacterCreateWizard, WIZARD_FORMS


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

    def test_attribute_form_renders_circle_inputs_and_validates_distribution(self):
        form = AttributesForm()
        self.assertIn("essential-rank-circle", form.as_p())
        self.assertFalse(
            AttributesForm(
                data={
                    name: 0
                    for name in (
                        "mind",
                        "will",
                        "instinct",
                        "dexterity",
                        "body",
                        "presence",
                        "gift",
                        "perception",
                    )
                }
            ).is_valid()
        )

    def test_rank_field_template_preserves_custom_circle_widget(self):
        rendered = render_to_string(
            "essential_characters/_rank_field.html",
            {"field": AttributesForm()["mind"]},
        )
        self.assertIn("essential-rank-circle", rendered)
        self.assertNotIn("form-check-input", rendered)

    def test_skill_form_validates_distribution(self):
        data = {}
        ranks = [3, 2, 2, 2, 1, 1, 1, 1, 1]
        for index, rank in enumerate(ranks):
            data[f"skill_{index}_name"] = f"Skill {index}"
            data[f"skill_{index}_rank"] = rank
        self.assertTrue(SkillsForm(data=data).is_valid())

    def test_create_url_uses_wizard(self):
        self.assertEqual(reverse("essential_characters:create"), "/essential/new/")

    def test_wizard_concept_excludes_player_name_and_image(self):
        form = ConceptForm()
        self.assertNotIn("player_name", form.fields)
        self.assertNotIn("image", form.fields)
        self.assertNotIn("notes", form.fields)
        self.assertIn("oath_or_debt", form.fields)

    def test_wizard_has_no_separate_oath_step(self):
        self.assertNotIn("oath", dict(WIZARD_FORMS))

    def test_marks_form_requires_predefined_marks(self):
        form = MarksForm()
        self.assertEqual(set(form.fields), {"ancestry", "path", "bond"})
        self.assertTrue(all(field.required for field in form.fields.values()))
        self.assertEqual(
            form.fields["ancestry"].widget.attrs["hx-get"],
            reverse("essential_characters:mark_summary"),
        )
        self.assertEqual(
            form.fields["ancestry"].widget.attrs["hx-target"],
            "#summary-id_ancestry",
        )

    def test_equipment_form_loads_preview_for_each_field(self):
        form = EquipmentForm()

        for name, field in form.fields.items():
            self.assertEqual(
                field.widget.attrs["hx-get"],
                reverse("essential_characters:equipment_summary"),
            )
            self.assertEqual(
                field.widget.attrs["hx-target"],
                f"#summary-id_{name}",
            )

    def test_mark_models_expose_translated_fields(self):
        self.assertEqual(
            {field.name for field in EssentialAncestry._meta.fields}
            & {
                "name_de",
                "name_en",
                "description_de",
                "description_en",
                "benefit_de",
                "benefit_en",
                "vulnerability_de",
                "vulnerability_en",
                "skills_de",
                "skills_en",
            },
            {
                "name_de",
                "name_en",
                "description_de",
                "description_en",
                "benefit_de",
                "benefit_en",
                "vulnerability_de",
                "vulnerability_en",
                "skills_de",
                "skills_en",
            },
        )
        self.assertTrue(
            {"facet_de", "facet_en", "skills_de", "skills_en"}
            <= {field.name for field in EssentialPath._meta.fields}
        )
        self.assertNotIn(
            "skills_de", {field.name for field in EssentialBond._meta.fields}
        )

    def test_mark_definitions_include_english_for_every_german_value(self):
        self.assertEqual(
            (len(ANCESTRIES), len(PATHS), len(BONDS)),
            (31, 44, 37),
        )
        for definition in (*ANCESTRIES, *PATHS, *BONDS):
            for field, value in definition.items():
                if field.endswith("_de") and value:
                    self.assertTrue(definition[field.removesuffix("_de") + "_en"])

    def test_birth_date_is_free_text_with_localized_month_suggestions(self):
        with override("de"):
            german = ConceptForm()["birth_date"].as_widget()
        with override("en"):
            english = ConceptForm()["birth_date"].as_widget()

        self.assertIn("<datalist", german)
        self.assertIn('value="Schneemond"', german)
        self.assertNotIn('value="Snowmoon"', german)
        self.assertIn('value="Snowmoon"', english)
        self.assertEqual(
            ConceptForm.base_fields["birth_date"].clean("13. Nebelmond 612"),
            "13. Nebelmond 612",
        )

    def test_sheet_edit_keeps_image_upload_and_excludes_player_name(self):
        form = EssentialCharacterForm()
        self.assertIn("image", form.fields)
        self.assertNotIn("player_name", form.fields)

    def test_character_uses_direct_catalog_relations(self):
        related_models = {
            "weapons": Weapon,
            "armor": RiotGear,
            "items": Item,
            "magic_aspects": SpellOrigin,
            "spells": BaseSpell,
        }
        for field_name, model in related_models.items():
            field = EssentialCharacter._meta.get_field(field_name)
            self.assertIs(field.remote_field.model, model)
            self.assertIs(
                field.remote_field.through._meta.auto_created, EssentialCharacter
            )

    def test_essential_catalog_fields_are_prefixed_and_nullable(self):
        for model in (Item, Weapon, RiotGear, SpellOrigin, BaseSpell):
            self.assertFalse(model._meta.get_field("essential_enabled").default)
        for model, fields in (
            (
                Weapon,
                (
                    "essential_damage",
                    "essential_range",
                    "essential_grip",
                    "essential_properties",
                ),
            ),
            (
                RiotGear,
                (
                    "essential_protection",
                    "essential_load",
                    "essential_sealing",
                    "essential_properties",
                ),
            ),
            (SpellOrigin, ("essential_description",)),
        ):
            for field_name in fields:
                self.assertTrue(model._meta.get_field(field_name).null)

    def test_bounded_essential_text_uses_char_fields(self):
        for model, fields in (
            (
                EssentialAncestry,
                (
                    "name_de",
                    "description_de",
                    "benefit_de",
                    "vulnerability_de",
                    "skills_de",
                ),
            ),
            (
                EssentialPath,
                (
                    "name_de",
                    "description_de",
                    "benefit_de",
                    "vulnerability_de",
                    "facet_de",
                    "skills_de",
                ),
            ),
            (
                EssentialBond,
                ("name_de", "description_de", "benefit_de", "vulnerability_de"),
            ),
            (EssentialCharacter, ("name", "birth_date", "concept", "focus")),
            (Weapon, ("essential_properties",)),
            (RiotGear, ("essential_properties",)),
            (SpellOrigin, ("essential_description",)),
        ):
            for field_name in fields:
                self.assertEqual(
                    model._meta.get_field(field_name).get_internal_type(), "CharField"
                )

    def test_essential_fields_have_translatable_verbose_names(self):
        models = (
            EssentialAncestry,
            EssentialPath,
            EssentialBond,
            EssentialCharacter,
            EssentialCharacterSkill,
        )
        for model in models:
            for field in model._meta.get_fields():
                if field.auto_created:
                    continue
                self.assertIsInstance(field._verbose_name, Promise)

    def test_skill_is_direct_free_text_assignment(self):
        self.assertEqual(
            [field.name for field in EssentialCharacterSkill._meta.fields],
            ["id", "character", "name", "rank"],
        )

    def test_essential_admins_use_unfold_model_admin(self):
        for model in (
            EssentialAncestry,
            EssentialBond,
            EssentialCharacter,
            EssentialCharacterSkill,
            EssentialPath,
        ):
            self.assertIsInstance(admin.site._registry[model], ModelAdmin)

    def test_wizard_step_url_preserves_query_parameters(self):
        wizard = EssentialCharacterCreateWizard()
        wizard.request = type(
            "Request",
            (),
            {
                "GET": QueryDict("campaign=3&plot=8&source=invite&step=concept"),
            },
        )()
        self.assertEqual(
            wizard.get_step_url("attributes"),
            "/essential/new/?campaign=3&plot=8&source=invite&step=attributes",
        )


class EssentialCharacterDerivedValueTests(SimpleTestCase):
    def setUp(self):
        self.character = EssentialCharacter(
            name="Mara",
            century=7,
            ancestry_id=1,
            path_id=1,
            bond_id=1,
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


class EssentialMarkSummaryTests(TestCase):
    def setUp(self):
        self.client.force_login(
            get_user_model().objects.create_user(username="marks-user")
        )
        self.path = EssentialPath.objects.create(
            name_de="Gelehrter",
            name_en="Scholar",
            description_de="Sucht nach Wissen.",
            description_en="Seeks knowledge.",
            benefit_de="Kennt Geschichten.",
            benefit_en="Knows stories.",
            vulnerability_de="Zögert bei Gewalt.",
            vulnerability_en="Hesitates at violence.",
            facet_de="Erkennt seltene Quellen.",
            facet_en="Recognizes rare sources.",
            skills_de="Geschichte, Mythen",
            skills_en="History, Myths",
        )

    def test_mark_summary_returns_selected_mark_details(self):
        response = self.client.get(
            reverse("essential_characters:mark_summary"),
            {"marks-path": self.path.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.path.name)
        self.assertContains(response, self.path.benefit)
        self.assertContains(response, self.path.vulnerability)
        self.assertContains(response, self.path.facet)
        self.assertContains(response, self.path.skills)

    def test_mark_summary_rejects_unknown_mark_type(self):
        response = self.client.get(
            reverse("essential_characters:mark_summary"),
            {"marks-unknown": self.path.pk},
        )

        self.assertEqual(response.status_code, 400)


class EssentialEquipmentSummaryTests(TestCase):
    def setUp(self):
        self.client.force_login(
            get_user_model().objects.create_user(username="equipment-user")
        )
        weapon_type = WeaponType.objects.create(name_de="Nahkampf", name_en="Melee")
        self.weapon = Weapon.objects.create(
            name_de="Schwert",
            name_en="Sword",
            type=weapon_type,
            weight=1,
            price=10,
            essential_enabled=True,
            essential_damage="2",
            essential_range="Nahkampf",
            essential_grip="10",
            essential_properties="Ausgewogen",
        )

    def test_equipment_summary_returns_selected_equipment_details(self):
        response = self.client.get(
            reverse("essential_characters:equipment_summary"),
            {"equipment-primary_weapon": self.weapon.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.weapon.name)
        self.assertContains(response, self.weapon.essential_damage)
        self.assertContains(response, self.weapon.essential_properties)

    def test_equipment_summary_rejects_unknown_equipment_type(self):
        response = self.client.get(
            reverse("essential_characters:equipment_summary"),
            {"equipment-unknown": self.weapon.pk},
        )

        self.assertEqual(response.status_code, 400)
