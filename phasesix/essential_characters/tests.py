from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.http import QueryDict
from django.template.loader import render_to_string
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils.translation import override

from .definitions import ANCESTRIES, BONDS, PATHS
from .forms import (
    AttributesForm,
    ConceptForm,
    EssentialCharacterForm,
    MarksForm,
    SkillsForm,
)
from .models import EssentialAncestry, EssentialBond, EssentialCharacter, EssentialPath
from .rules import (
    CENTURY_LEVELS,
    magic_slots,
    valid_attribute_distribution,
    valid_skill_distribution,
)
from .views import EssentialCharacterCreateWizard


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
