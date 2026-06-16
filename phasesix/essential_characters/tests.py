import tempfile
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.serializers.json import DjangoJSONEncoder
from django.http import QueryDict
from django.template.loader import render_to_string
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import resolve, reverse
from django.utils.functional import Promise
from django.utils.translation import override
from unfold.admin import ModelAdmin

from armory.models import Item, ItemType, RiotGear, RiotGearType, Weapon, WeaponType
from magic.models import BaseSpell, SpellOrigin
from homebrew.models import HomebrewModel
from rules.models import Extension, Lineage, Template, TemplateCategory

from .forms import (
    AttributesForm,
    CircleRadioSelect,
    ConceptForm,
    EquipmentForm,
    EssentialCharacterForm,
    EssentialSkillsEditForm,
    MarksForm,
    SearchableItemSelectMultiple,
    SearchableSpellSelect,
    SkillsForm,
    SupernaturalForm,
)
from .api import PublicEssentialCharacterApiView
from .models import (
    EssentialBond,
    EssentialCharacter,
    EssentialCharacterSkill,
)
from .rules import (
    CENTURY_LEVELS,
    magic_slots,
    valid_attribute_distribution,
    valid_skill_distribution,
)
from .views import (
    EquipmentSummaryView,
    EssentialAddSkillView,
    EssentialCharacterCreateWizard,
    EssentialCustomEquipmentCreateView,
    EssentialCustomMarkCreateView,
    EssentialCharacterDetailInfoView,
    EssentialCharacterDetailView,
    EssentialCharacterConditionView,
    EssentialCharacterEditSectionView,
    EssentialCharacterEditSearchView,
    EssentialCharacterImageView,
    EssentialCharacterUpdateView,
    MarkSummaryView,
    SupernaturalSummaryView,
    WIZARD_FORMS,
)


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

    def test_urls_use_class_based_views(self):
        view_classes = {
            "mark_summary": MarkSummaryView,
            "custom_mark_create": EssentialCustomMarkCreateView,
            "custom_equipment_create": EssentialCustomEquipmentCreateView,
            "add_skill": EssentialAddSkillView,
            "equipment_summary": EquipmentSummaryView,
            "supernatural_summary": SupernaturalSummaryView,
            "create": EssentialCharacterCreateWizard,
            "detail_info": EssentialCharacterDetailInfoView,
            "change_image": EssentialCharacterImageView,
            "edit_section": EssentialCharacterEditSectionView,
            "edit_search": EssentialCharacterEditSearchView,
            "set_condition": EssentialCharacterConditionView,
            "detail": EssentialCharacterDetailView,
            "edit": EssentialCharacterUpdateView,
            "api:essential_character": PublicEssentialCharacterApiView,
        }
        kwargs_by_name = {
            "custom_mark_create": {"mark_type": "bond"},
            "custom_equipment_create": {"equipment_type": "weapon"},
            "detail_info": {"slug": "joran", "section": "marks"},
            "change_image": {"slug": "joran"},
            "edit_section": {"slug": "joran", "section": "marks"},
            "edit_search": {"slug": "joran"},
            "set_condition": {"slug": "joran", "condition": "wounds"},
            "detail": {"slug": "joran"},
            "edit": {"slug": "joran"},
            "api:essential_character": {"character_hash": "joran"},
        }

        for name, view_class in view_classes.items():
            match = resolve(
                reverse(
                    name if name.startswith("api:") else f"essential_characters:{name}",
                    kwargs=kwargs_by_name.get(name),
                )
            )
            self.assertIs(match.func.view_class, view_class)

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

        for name in ("primary_weapon", "secondary_weapon", "armor"):
            field = form.fields[name]
            self.assertEqual(
                field.widget.attrs["hx-get"],
                reverse("essential_characters:equipment_summary"),
            )
            self.assertEqual(
                field.widget.attrs["hx-target"],
                f"#summary-id_{name}",
            )
        self.assertNotIn("hx-get", form.fields["items"].widget.attrs)
        self.assertNotIn("hx-target", form.fields["items"].widget.attrs)

    def test_equipment_form_uses_searchable_item_picker(self):
        widget = EquipmentForm().fields["items"].widget

        self.assertIsInstance(widget, SearchableItemSelectMultiple)
        self.assertEqual(
            widget.template_name,
            "essential_characters/widgets/searchable_item_select.html",
        )

    def test_supernatural_form_builds_fields_for_gift_slots(self):
        form = SupernaturalForm(gift=3)

        self.assertEqual(
            set(form.fields),
            {
                "focus",
                "regeneration_ritual",
                "magic_aspect_0",
                "magic_aspect_1",
                "spell_0",
                "spell_1",
                "spell_2",
                "spell_3",
                "spell_4",
            },
        )
        self.assertIsInstance(form.fields["spell_0"].widget, SearchableSpellSelect)
        self.assertFalse(form.fields["magic_aspect_0"].queryset.query.where.children)

    def test_mark_models_expose_translated_fields(self):
        self.assertEqual(
            {field.name for field in Lineage._meta.fields}
            & {
                "essential_description_de",
                "essential_description_en",
                "essential_benefit_de",
                "essential_benefit_en",
                "essential_vulnerability_de",
                "essential_vulnerability_en",
                "essential_skills_de",
                "essential_skills_en",
            },
            {
                "essential_description_de",
                "essential_description_en",
                "essential_benefit_de",
                "essential_benefit_en",
                "essential_vulnerability_de",
                "essential_vulnerability_en",
                "essential_skills_de",
                "essential_skills_en",
            },
        )
        self.assertTrue(
            {
                "essential_facet_de",
                "essential_facet_en",
                "essential_skills_de",
                "essential_skills_en",
            }
            <= {field.name for field in Template._meta.fields}
        )
        self.assertNotIn(
            "skills_de", {field.name for field in EssentialBond._meta.fields}
        )
        self.assertIn(HomebrewModel, EssentialBond.__mro__)
        self.assertIn(HomebrewModel, Lineage.__mro__)

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

    def test_detail_skill_editor_uses_circle_ranks_zero_through_four(self):
        form = EssentialSkillsEditForm(
            character=type(
                "Character",
                (),
                {
                    "essentialcharacterskill_set": type(
                        "Assignments",
                        (),
                        {"all": lambda self: []},
                    )()
                },
            )()
        )

        self.assertIsInstance(form.fields["skill_0_rank"].widget, CircleRadioSelect)
        self.assertEqual(
            list(form.fields["skill_0_rank"].choices),
            [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)],
        )

    def test_character_uses_direct_catalog_relations(self):
        related_models = {
            "ancestry": Lineage,
            "path": Template,
            "weapons": Weapon,
            "armor": RiotGear,
            "items": Item,
            "magic_aspects": SpellOrigin,
            "spells": BaseSpell,
        }
        for field_name, model in related_models.items():
            field = EssentialCharacter._meta.get_field(field_name)
            self.assertIs(field.remote_field.model, model)
            if field.many_to_many:
                self.assertIs(
                    field.remote_field.through._meta.auto_created, EssentialCharacter
                )

    def test_essential_catalog_fields_are_prefixed_and_nullable(self):
        for model in (
            Lineage,
            Template,
            Item,
            Weapon,
            RiotGear,
            SpellOrigin,
            BaseSpell,
        ):
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
                Lineage,
                (
                    "essential_description_de",
                    "essential_benefit_de",
                    "essential_vulnerability_de",
                    "essential_skills_de",
                ),
            ),
            (
                Template,
                (
                    "essential_description_de",
                    "essential_benefit_de",
                    "essential_vulnerability_de",
                    "essential_facet_de",
                    "essential_skills_de",
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
            ["id", "character", "name_de", "name_en", "rank"],
        )

    def test_essential_admins_use_unfold_model_admin(self):
        for model in (
            EssentialBond,
            EssentialCharacter,
            EssentialCharacterSkill,
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


class PublicEssentialCharacterApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        owner = get_user_model().objects.create_user(username="joran-player")
        cls.character = EssentialCharacter.objects.create(
            created_by=owner,
            name="Joran Ashpath",
            slug="joran-ashpath",
            birth_date="17. Tag des Nebelmonds",
            century=8,
            concept="A sworn guardian",
            oath_or_debt="Protect the last shrine.",
            notes="Carries an old map.",
            ancestry=Lineage.objects.create(
                name_de="Gasdaria",
                name_en="Gasdaria",
                essential_enabled=True,
            ),
            path=Template.objects.create(
                name_de="Paladin",
                name_en="Paladin",
                category=TemplateCategory.objects.create(
                    name_de="Pfade", name_en="Paths"
                ),
                essential_enabled=True,
            ),
            bond=EssentialBond.objects.create(
                name_de="Stimmen",
                name_en="Voices",
            ),
            mind=2,
            will=2,
            instinct=1,
            dexterity=3,
            body=1,
            presence=1,
            gift=0,
            perception=0,
            wounds=1,
            burden=2,
            omen=3,
            arkana=4,
            favor=5,
            corruption=1,
        )
        EssentialCharacterSkill.objects.create(
            character=cls.character, name_de="Ritus", name_en="Rite", rank=2
        )

    def test_anonymous_get_returns_nextjs_compatible_character(self):
        response = self.client.get(
            reverse(
                "api:essential_character",
                kwargs={"character_hash": self.character.slug},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Access-Control-Allow-Origin"], "*")
        self.assertEqual(
            response.json(),
            {
                "hash": "joran-ashpath",
                "name": "Joran Ashpath",
                "birthDate": "17. Tag des Nebelmonds",
                "century": 8,
                "campaign": None,
                "playerName": "joran-player",
                "concept": "A sworn guardian",
                "ancestry": "Gasdaria",
                "ancestryCustom": False,
                "path": "Paladin",
                "pathCustom": False,
                "bond": "Stimmen",
                "bondCustom": False,
                "oathOrDebt": "Protect the last shrine.",
                "mark": "keins",
                "attributes": {
                    "mind": 2,
                    "will": 2,
                    "instinct": 1,
                    "dexterity": 3,
                    "body": 1,
                    "presence": 1,
                    "gift": 0,
                    "perception": 0,
                },
                "skills": [{"name": "Ritus", "rank": 2}],
                "equipment": {
                    "primaryWeapon": "",
                    "secondaryWeapon": "",
                    "armor": "",
                    "items": [],
                    "customWeapons": {},
                    "customArmors": {},
                },
                "supernatural": {
                    "focus": "",
                    "regenerationRitual": "",
                    "aspects": [],
                    "spells": [],
                },
                "conditions": {
                    "wounds": 1,
                    "burden": 2,
                    "omen": 3,
                    "arkana": 4,
                    "favor": 5,
                    "corruption": 1,
                },
                "notes": "Carries an old map.",
                "portraitOriginalName": None,
                "portraitMimeType": None,
                "portraitSize": None,
                "portraitUpdatedAt": None,
                "woundThreshold": 4,
                "burdenThreshold": 6,
                "initiative": 60,
                "faithLevel": 4,
                "magicLevel": 2,
                "omenMax": 4,
                "invocationValue": 6,
                "favorLimit": 2,
                "arkanaMax": 5,
                "favorMax": 5,
                "createdAt": DjangoJSONEncoder().default(self.character.created_at),
                "updatedAt": DjangoJSONEncoder().default(self.character.modified_at),
            },
        )

    def test_missing_character_and_options_include_public_cors_headers(self):
        url = reverse(
            "api:essential_character", kwargs={"character_hash": "does-not-exist"}
        )

        missing_response = self.client.get(url)
        options_response = self.client.options(url)

        self.assertEqual(missing_response.status_code, 404)
        self.assertEqual(missing_response.json(), {"error": "Nicht gefunden"})
        self.assertEqual(missing_response["Access-Control-Allow-Origin"], "*")
        self.assertEqual(options_response.status_code, 204)
        self.assertEqual(
            options_response["Access-Control-Allow-Methods"], "GET, PATCH, OPTIONS"
        )
        self.assertEqual(
            options_response["Access-Control-Allow-Headers"], "Content-Type"
        )


class EssentialCharacterImageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(username="image-owner")
        cls.other_user = get_user_model().objects.create_user(username="image-other")
        cls.character = EssentialCharacter.objects.create(
            created_by=cls.owner,
            name="Joran Ashpath",
            slug="joran-ashpath",
            century=8,
            ancestry=Lineage.objects.create(
                name_de="Gasdaria",
                name_en="Gasdaria",
                essential_enabled=True,
            ),
            path=Template.objects.create(
                name_de="Paladin",
                name_en="Paladin",
                category=TemplateCategory.objects.create(
                    name_de="Pfade", name_en="Paths"
                ),
                essential_enabled=True,
            ),
            bond=EssentialBond.objects.create(
                name_de="Stimmen",
                name_en="Voices",
            ),
            mind=2,
            will=2,
            instinct=1,
            dexterity=3,
            body=1,
            presence=1,
            gift=0,
            perception=0,
        )

    def setUp(self):
        self.media_root = tempfile.TemporaryDirectory()
        self.settings_override = override_settings(MEDIA_ROOT=self.media_root.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.addCleanup(self.media_root.cleanup)

    def test_detail_shows_image_actions_only_to_editor(self):
        detail_url = self.character.get_absolute_url()

        anonymous_response = self.client.get(detail_url)
        self.client.force_login(self.owner)
        owner_response = self.client.get(detail_url)

        self.assertNotContains(anonymous_response, "data-essential-image-input")
        self.assertContains(owner_response, "data-essential-image-input")
        self.assertContains(
            owner_response,
            reverse(
                "essential_characters:change_image",
                kwargs={"slug": self.character.slug},
            ),
        )

    def test_owner_can_upload_and_remove_image(self):
        self.client.force_login(self.owner)
        image_url = reverse(
            "essential_characters:change_image", kwargs={"slug": self.character.slug}
        )
        image = SimpleUploadedFile(
            "portrait.gif",
            (
                b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00"
                b"\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,"
                b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
            ),
            content_type="image/gif",
        )

        upload_response = self.client.post(image_url, {"image": image})
        self.character.refresh_from_db()
        self.assertRedirects(upload_response, self.character.get_absolute_url())
        self.assertTrue(self.character.image)
        self.assertContains(
            self.client.get(self.character.get_absolute_url()),
            self.character.get_image_url("600x600"),
        )

        remove_response = self.client.post(image_url, {"remove_image": "1"})
        self.character.refresh_from_db()
        self.assertRedirects(remove_response, self.character.get_absolute_url())
        self.assertFalse(self.character.image)

    def test_non_editor_cannot_change_image(self):
        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse(
                "essential_characters:change_image",
                kwargs={"slug": self.character.slug},
            ),
            {"remove_image": "1"},
        )

        self.assertEqual(response.status_code, 403)

    def test_detail_shows_edit_controls_and_condition_actions_only_to_editor(self):
        detail_url = self.character.get_absolute_url()
        condition_url = reverse(
            "essential_characters:set_condition",
            kwargs={"slug": self.character.slug, "condition": "wounds"},
        )
        marks_url = reverse(
            "essential_characters:edit_section",
            kwargs={"slug": self.character.slug, "section": "marks"},
        )

        anonymous_response = self.client.get(detail_url)
        self.client.force_login(self.owner)
        owner_response = self.client.get(detail_url)

        self.assertNotContains(anonymous_response, marks_url)
        self.assertNotContains(anonymous_response, condition_url)
        self.assertContains(owner_response, marks_url)
        self.assertContains(owner_response, condition_url)

    def test_owner_can_set_condition_directly(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse(
                "essential_characters:set_condition",
                kwargs={"slug": self.character.slug, "condition": "wounds"},
            ),
            {"value": 2},
        )

        self.character.refresh_from_db()
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.character.wounds, 2)

    def test_condition_update_checks_permissions_and_bounds(self):
        condition_url = reverse(
            "essential_characters:set_condition",
            kwargs={"slug": self.character.slug, "condition": "wounds"},
        )
        self.client.force_login(self.other_user)
        self.assertEqual(self.client.post(condition_url, {"value": 1}).status_code, 403)

        self.client.force_login(self.owner)
        self.assertEqual(
            self.client.post(condition_url, {"value": 99}).status_code,
            400,
        )

    def test_owner_can_open_and_submit_focused_edit_form(self):
        self.client.force_login(self.owner)
        notes_url = reverse(
            "essential_characters:edit_section",
            kwargs={"slug": self.character.slug, "section": "notes"},
        )

        self.assertContains(self.client.get(notes_url), "textarea")
        response = self.client.post(notes_url, {"notes": "A changed note."})

        self.character.refresh_from_db()
        self.assertRedirects(response, self.character.get_absolute_url())
        self.assertEqual(self.character.notes, "A changed note.")

    def test_non_editor_cannot_open_focused_edit_form(self):
        self.client.force_login(self.other_user)

        response = self.client.get(
            reverse(
                "essential_characters:edit_section",
                kwargs={"slug": self.character.slug, "section": "marks"},
            )
        )

        self.assertEqual(response.status_code, 403)


class EssentialMarkSummaryTests(TestCase):
    def setUp(self):
        self.client.force_login(
            get_user_model().objects.create_user(username="marks-user")
        )
        self.path = Template.objects.create(
            name_de="Gelehrter",
            name_en="Scholar",
            category=TemplateCategory.objects.create(name_de="Pfade", name_en="Paths"),
            essential_enabled=True,
            essential_description_de="Sucht nach Wissen.",
            essential_description_en="Seeks knowledge.",
            essential_benefit_de="Kennt Geschichten.",
            essential_benefit_en="Knows stories.",
            essential_vulnerability_de="Zögert bei Gewalt.",
            essential_vulnerability_en="Hesitates at violence.",
            essential_facet_de="Erkennt seltene Quellen.",
            essential_facet_en="Recognizes rare sources.",
            essential_skills_de="Geschichte, Mythen",
            essential_skills_en="History, Myths",
        )

    def test_mark_summary_returns_selected_mark_details(self):
        response = self.client.get(
            reverse("essential_characters:mark_summary"),
            {"marks-path": self.path.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.path.name)
        self.assertContains(response, self.path.essential_benefit)
        self.assertContains(response, self.path.essential_vulnerability)
        self.assertContains(response, self.path.essential_facet)
        self.assertContains(response, self.path.essential_skills)

    def test_mark_summary_rejects_unknown_mark_type(self):
        response = self.client.get(
            reverse("essential_characters:mark_summary"),
            {"marks-unknown": self.path.pk},
        )

        self.assertEqual(response.status_code, 400)


class EssentialCustomMarkTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="mark-author")
        self.other_user = get_user_model().objects.create_user(username="other-author")
        self.client.force_login(self.user)
        category = TemplateCategory.objects.create(name_de="Pfade", name_en="Paths")
        Template.objects.create(
            name_de="Vorlage",
            name_en="Template",
            category=category,
            essential_enabled=True,
        )
        self.payload = {
            "name": "Eigene Marke",
            "description": "Eine eigene Beschreibung.",
            "benefit": "Ein eigener Vorteil.",
            "vulnerability": "Eine eigene Schwäche.",
            "skills": "Wissen, Auftreten",
            "facet": "Ein eigenes Facettenspiel.",
        }

    def test_custom_marks_are_created_as_player_homebrew(self):
        models = {
            "ancestry": Lineage,
            "path": Template,
            "bond": EssentialBond,
        }

        for mark_type, model in models.items():
            with self.subTest(mark_type=mark_type):
                response = self.client.post(
                    reverse(
                        "essential_characters:custom_mark_create",
                        kwargs={"mark_type": mark_type},
                    ),
                    self.payload,
                )

                self.assertEqual(response.status_code, 200)
                obj = model.objects.get(pk=response.json()["id"])
                self.assertTrue(obj.is_homebrew)
                self.assertEqual(obj.created_by, self.user)
                self.assertEqual(obj.name_de, self.payload["name"])
                self.assertEqual(obj.name_en, self.payload["name"])

    def test_player_homebrew_is_only_visible_to_its_author(self):
        response = self.client.post(
            reverse(
                "essential_characters:custom_mark_create",
                kwargs={"mark_type": "bond"},
            ),
            self.payload,
        )
        bond = EssentialBond.objects.get(pk=response.json()["id"])

        self.assertIn(bond, MarksForm(user=self.user).fields["bond"].queryset)
        self.assertNotIn(bond, MarksForm(user=self.other_user).fields["bond"].queryset)

    @override_settings(OPENAI_API_KEY="configured")
    @patch("essential_characters.views.translate_custom_mark")
    def test_staff_can_translate_custom_mark_into_both_languages(self, translate):
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])
        translate.return_value = {
            "de": {
                "name": "Eigene Bindung",
                "description": "Beschreibung",
                "benefit": "Vorteil",
                "vulnerability": "Schwäche",
            },
            "en": {
                "name": "Custom Bond",
                "description": "Description",
                "benefit": "Benefit",
                "vulnerability": "Vulnerability",
            },
        }

        response = self.client.post(
            reverse(
                "essential_characters:custom_mark_create",
                kwargs={"mark_type": "bond"},
            ),
            {**self.payload, "translate_with_openai": "on"},
        )

        self.assertEqual(response.status_code, 200)
        bond = EssentialBond.objects.get(pk=response.json()["id"])
        self.assertEqual(bond.name_de, "Eigene Bindung")
        self.assertEqual(bond.name_en, "Custom Bond")
        translate.assert_called_once()

    def test_openai_translation_control_is_staff_only(self):
        response = self.client.get(
            reverse(
                "essential_characters:custom_mark_create",
                kwargs={"mark_type": "bond"},
            )
        )
        self.assertNotContains(response, "translate_with_openai")


class EssentialSkillTranslationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="skill-author")
        self.client.force_login(self.user)
        self.character = EssentialCharacter.objects.create(
            created_by=self.user,
            name="Skill Tester",
            century=1,
            ancestry=Lineage.objects.create(
                name_de="Mensch", name_en="Human", essential_enabled=True
            ),
            path=Template.objects.create(
                name_de="Pfad",
                name_en="Path",
                category=TemplateCategory.objects.create(
                    name_de="Pfade", name_en="Paths"
                ),
                essential_enabled=True,
            ),
            bond=EssentialBond.objects.create(name_de="Bund", name_en="Bond"),
            mind=3,
            will=2,
            instinct=2,
            dexterity=1,
            body=1,
            presence=1,
            gift=0,
            perception=0,
        )

    @patch("essential_characters.openai.translate_skill_names")
    def test_replace_for_character_stores_both_translated_names(self, translate):
        translate.return_value = [
            {"de": "Heimlichkeit", "en": "Stealth"},
            {"de": "Wissen", "en": "Knowledge"},
        ]

        EssentialCharacterSkill.replace_for_character(
            self.character, [("Stealth", 3), ("Wissen", 2)]
        )

        skills = EssentialCharacterSkill.objects.order_by("rank")
        self.assertEqual(
            {(skill.name_de, skill.name_en, skill.rank) for skill in skills},
            {
                ("Heimlichkeit", "Stealth", 3),
                ("Wissen", "Knowledge", 2),
            },
        )
        translate.assert_called_once_with(["Stealth", "Wissen"])

    def test_add_skill_modal_accepts_name_and_rank(self):
        response = self.client.post(
            reverse("essential_characters:add_skill"),
            {"name": "Heimlichkeit", "rank": 3},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"name": "Heimlichkeit", "rank": 3})


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
            description_en="A balanced blade.",
            essential_enabled=True,
            essential_damage="2",
            essential_range="Nahkampf",
            essential_grip="10",
            essential_properties="Ausgewogen",
        )
        armor_type = RiotGearType.objects.create(name_de="Kleidung", name_en="Clothing")
        self.armor = RiotGear.objects.create(
            name_de="Ledermantel",
            name_en="Leather coat",
            type=armor_type,
            weight=2,
            price=15,
            description_en="A reinforced leather coat.",
            essential_enabled=True,
            essential_protection="1",
            essential_load="1",
            essential_sealing="0",
            essential_properties="Unauffällig",
        )
        self.item_type = ItemType.objects.create(name_de="Werkzeug", name_en="Tools")
        self.tirakan = Extension.objects.create(
            name_de="Tirakan", name_en="Tirakan", identifier="tirakan"
        )
        self.middleages = Extension.objects.create(
            name_de="Mittelalter", name_en="Middle Ages", identifier="middleages"
        )
        self.core = Extension.objects.create(
            name_de="Grundregeln",
            name_en="Core Rules",
            identifier="core",
            is_mandatory=True,
        )
        self.other_extension = Extension.objects.create(
            name_de="Nexus", name_en="Nexus", identifier="nexus"
        )
        self.tirakan_item = self.create_item("Seil", self.tirakan)
        self.middleages_item = self.create_item("Laterne", self.middleages)
        self.core_item = self.create_item("Rucksack", self.core)
        self.other_item = self.create_item("Scanner", self.other_extension)

    def create_item(self, name, extension):
        item = Item.objects.create(
            name_de=name,
            name_en=name,
            type=self.item_type,
            weight=1,
            price=1,
        )
        item.extensions.add(extension)
        return item

    def test_equipment_form_lists_tirakan_middleages_and_core_items(self):
        item_ids = set(
            EquipmentForm().fields["items"].queryset.values_list("pk", flat=True)
        )

        self.assertEqual(
            item_ids,
            {self.tirakan_item.pk, self.middleages_item.pk, self.core_item.pk},
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
        self.assertContains(response, self.weapon.description)

    def test_equipment_summary_returns_armor_description(self):
        response = self.client.get(
            reverse("essential_characters:equipment_summary"),
            {"equipment-armor": self.armor.pk},
        )

        self.assertContains(response, self.armor.name)
        self.assertContains(response, self.armor.essential_protection)
        self.assertContains(response, self.armor.description)

    def test_equipment_summary_rejects_unknown_equipment_type(self):
        response = self.client.get(
            reverse("essential_characters:equipment_summary"),
            {"equipment-unknown": self.weapon.pk},
        )

        self.assertEqual(response.status_code, 400)

    def test_equipment_summary_returns_extension_item_without_essential_flag(self):
        response = self.client.get(
            reverse("essential_characters:equipment_summary"),
            {"equipment-items": self.tirakan_item.pk},
        )

        self.assertContains(response, self.tirakan_item.name)

    def test_equipment_summary_excludes_items_from_other_extensions(self):
        response = self.client.get(
            reverse("essential_characters:equipment_summary"),
            {"equipment-items": self.other_item.pk},
        )

        self.assertNotContains(response, self.other_item.name)


class EssentialCustomEquipmentTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="equipment-author")
        self.other_user = get_user_model().objects.create_user(username="other-author")
        self.client.force_login(self.user)
        Extension.objects.create(
            name_de="Tirakan", name_en="Tirakan", identifier="tirakan"
        )
        self.types = {
            "weapon": WeaponType.objects.create(name_de="Nahkampf", name_en="Melee"),
            "armor": RiotGearType.objects.create(
                name_de="Kleidung", name_en="Clothing"
            ),
            "item": ItemType.objects.create(name_de="Werkzeug", name_en="Tools"),
        }

    def test_creates_and_returns_each_homebrew_equipment_type(self):
        cases = {
            "weapon": (
                Weapon,
                {
                    "damage": "2",
                    "range": "Nahkampf",
                    "grip": "10",
                    "properties": "Ausgewogen",
                },
                "secondary_weapon",
            ),
            "armor": (
                RiotGear,
                {
                    "protection": "1",
                    "load": "1",
                    "sealing": "0",
                    "properties": "Unauffällig",
                },
                "armor",
            ),
            "item": (Item, {}, "items"),
        }

        for equipment_type, (model, details, target) in cases.items():
            with self.subTest(equipment_type=equipment_type):
                response = self.client.post(
                    reverse(
                        "essential_characters:custom_equipment_create",
                        kwargs={"equipment_type": equipment_type},
                    )
                    + f"?target={target}",
                    {
                        "name": f"Custom {equipment_type}",
                        "description": "Custom description",
                        "type": self.types[equipment_type].pk,
                        **details,
                    },
                )

                self.assertEqual(response.status_code, 200)
                obj = model.objects.get(pk=response.json()["id"])
                self.assertTrue(obj.is_homebrew)
                self.assertTrue(obj.essential_enabled)
                self.assertEqual(obj.created_by, self.user)
                self.assertEqual(response.json()["target"], target)

    def test_private_homebrew_equipment_is_only_visible_to_author(self):
        response = self.client.post(
            reverse(
                "essential_characters:custom_equipment_create",
                kwargs={"equipment_type": "weapon"},
            ),
            {
                "name": "Private blade",
                "description": "",
                "type": self.types["weapon"].pk,
            },
        )
        weapon = Weapon.objects.get(pk=response.json()["id"])

        self.assertIn(
            weapon, EquipmentForm(user=self.user).fields["primary_weapon"].queryset
        )
        self.assertNotIn(
            weapon,
            EquipmentForm(user=self.other_user).fields["primary_weapon"].queryset,
        )

    @override_settings(OPENAI_API_KEY="configured")
    @patch("essential_characters.views.translate_custom_mark")
    def test_staff_can_translate_custom_equipment(self, translate):
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])
        translate.return_value = {
            "de": {"name": "Langschwert", "description": "Eine lange Klinge."},
            "en": {"name": "Longsword", "description": "A long blade."},
        }

        response = self.client.post(
            reverse(
                "essential_characters:custom_equipment_create",
                kwargs={"equipment_type": "weapon"},
            ),
            {
                "name": "Langschwert",
                "description": "Eine lange Klinge.",
                "type": self.types["weapon"].pk,
                "translate_with_openai": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        weapon = Weapon.objects.get(pk=response.json()["id"])
        self.assertEqual(weapon.name_de, "Langschwert")
        self.assertEqual(weapon.name_en, "Longsword")
        translate.assert_called_once()
