import tempfile

from django.contrib.auth import get_user_model
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import QueryDict
from django.template.loader import render_to_string
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import resolve, reverse
from django.utils.functional import Promise
from django.utils.translation import override
from unfold.admin import ModelAdmin

from armory.models import Item, ItemType, RiotGear, Weapon, WeaponType
from magic.models import BaseSpell, SpellOrigin
from rules.models import Extension, Lineage, Template, TemplateCategory

from .forms import (
    AttributesForm,
    ConceptForm,
    EquipmentForm,
    EssentialCharacterForm,
    MarksForm,
    SearchableItemSelectMultiple,
    SearchableSpellSelect,
    SkillsForm,
    SupernaturalForm,
)
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
    EssentialCharacterCreateWizard,
    EssentialCharacterDetailInfoView,
    EssentialCharacterDetailView,
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
            "equipment_summary": EquipmentSummaryView,
            "supernatural_summary": SupernaturalSummaryView,
            "create": EssentialCharacterCreateWizard,
            "detail_info": EssentialCharacterDetailInfoView,
            "change_image": EssentialCharacterImageView,
            "detail": EssentialCharacterDetailView,
            "edit": EssentialCharacterUpdateView,
        }
        kwargs_by_name = {
            "detail_info": {"slug": "joran", "section": "marks"},
            "change_image": {"slug": "joran"},
            "detail": {"slug": "joran"},
            "edit": {"slug": "joran"},
        }

        for name, view_class in view_classes.items():
            match = resolve(
                reverse(
                    f"essential_characters:{name}",
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
            ["id", "character", "name", "rank"],
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
