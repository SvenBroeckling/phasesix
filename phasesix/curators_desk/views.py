from functools import reduce
from operator import or_

from django.db import models
from django.db.models import Q, Sum, Count, Max, Min
from django.http import HttpResponse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import TemplateView

from armory.models import Weapon, Item, WeaponModification, RiotGear
from campaigns.models import Roll
from curators_desk.utils import get_models_with_translations, get_homebrew_models
from magic.models import BaseSpell
from rules.models import (
    Attribute,
    Skill,
    CHARACTER_ASPECT_CHOICES,
    Extension,
    Template,
    Lineage,
    TemplateModifier,
)


class DashboardView(TemplateView):
    template_name = "curators_desk/dashboard.html"


class RollStatisticsView(TemplateView):
    template_name = "curators_desk/fragments/roll_statistics.html"

    @staticmethod
    def _get_roll_statistics(model):
        d = []
        for a in model.objects.all():
            d.append(
                {
                    "object": a,
                    "roll_count": Roll.objects.filter(
                        header__in=[a.name_de, a.name_en]
                    ).count(),
                }
            )
        return d

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object_list"] = [
            {
                "title": _("Attributes"),
                "elements": self._get_roll_statistics(Attribute),
            },
            {"title": _("Skills"), "elements": self._get_roll_statistics(Skill)},
            {"title": _("Weapons"), "elements": self._get_roll_statistics(Weapon)},
            {"title": _("Spells"), "elements": self._get_roll_statistics(BaseSpell)},
        ]
        return context


class TemplateStatisticsView(TemplateView):
    template_name = "curators_desk/fragments/template_statistics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        extension_id = self.request.GET.get("e")
        templates_qs = Template.objects.all()
        if extension_id:
            try:
                active_extension = Extension.objects.get(id=extension_id)
                templates_qs = templates_qs.filter(extensions=active_extension)
            except Extension.DoesNotExist:
                active_extension = None
        else:
            active_extension = None

        modifiers_qs = TemplateModifier.objects.filter(template__in=templates_qs)

        def get_stats_for_field(field_name, modifier_field, all_items_map):
            agg_stats = (
                modifiers_qs.filter(**{f"{field_name}__isnull": False})
                .values(field_name)
                .annotate(
                    sum_val=Sum(modifier_field),
                    count_val=Count("id"),
                    max_val=Max(modifier_field),
                    min_val=Min(modifier_field),
                )
            )

            pos_agg_stats = (
                modifiers_qs.filter(
                    **{f"{field_name}__isnull": False, f"{modifier_field}__gt": 0}
                )
                .values(field_name)
                .annotate(pos_sum_val=Sum(modifier_field))
            )
            pos_sums = {item[field_name]: item["pos_sum_val"] for item in pos_agg_stats}

            stats_sum = {}
            stats_pos_sum = {}
            stats_count = {}
            stats_max = {}
            stats_min = {}

            max_min_queries = []
            for stat in agg_stats:
                item_id = stat[field_name]
                item_obj = all_items_map.get(item_id)
                if not item_obj:
                    continue

                stats_sum[item_obj] = [stat["sum_val"], []]
                stats_count[item_obj] = [stat["count_val"], []]
                stats_pos_sum[item_obj] = [pos_sums.get(item_id, 0), []]

                max_val = stat["max_val"]
                min_val = stat["min_val"]

                stats_max[item_obj] = [max_val, []]
                stats_min[item_obj] = [min_val, []]

                max_min_queries.append(
                    Q(**{field_name: item_id, modifier_field: max_val})
                )
                max_min_queries.append(
                    Q(**{field_name: item_id, modifier_field: min_val})
                )

            if not max_min_queries:
                for item_id, item_obj in all_items_map.items():
                    if item_obj not in stats_sum:
                        stats_sum[item_obj] = [0, []]
                        stats_pos_sum[item_obj] = [0, []]
                        stats_count[item_obj] = [0, []]
                        stats_max[item_obj] = [-999, []]
                        stats_min[item_obj] = [999, []]
                return (
                    stats_sum,
                    stats_pos_sum,
                    stats_count,
                    stats_max,
                    stats_min,
                )

            relevant_modifiers = modifiers_qs.filter(
                reduce(or_, max_min_queries)
            ).select_related("template")

            for mod in relevant_modifiers:
                item_id = getattr(mod, field_name)
                if isinstance(item_id, models.Model):
                    item_id = item_id.pk
                item_obj = all_items_map.get(item_id)
                mod_val = getattr(mod, modifier_field)

                if item_obj in stats_max and stats_max[item_obj][0] == mod_val:
                    if mod.template not in stats_max[item_obj][1]:
                        stats_max[item_obj][1].append(mod.template)

                if item_obj in stats_min and stats_min[item_obj][0] == mod_val:
                    if mod.template not in stats_min[item_obj][1]:
                        stats_min[item_obj][1].append(mod.template)

            return stats_sum, stats_pos_sum, stats_count, stats_max, stats_min

        aspect_map = {a[0]: a[0] for a in CHARACTER_ASPECT_CHOICES}
        (
            aspects_sum,
            aspects_positive_sum,
            aspects_count,
            aspects_max,
            aspects_min,
        ) = get_stats_for_field("aspect", "aspect_modifier", aspect_map)

        attribute_map = {obj.pk: obj for obj in Attribute.objects.all()}
        (
            attributes_sum,
            attributes_positive_sum,
            attributes_count,
            attributes_max,
            attributes_min,
        ) = get_stats_for_field("attribute", "attribute_modifier", attribute_map)

        skill_map = {obj.pk: obj for obj in Skill.objects.all()}
        (
            skills_sum,
            skills_positive_sum,
            skills_count,
            skills_max,
            skills_min,
        ) = get_stats_for_field("skill", "skill_modifier", skill_map)

        context.update(
            {
                "aspects_max": dict(
                    reversed(sorted(aspects_max.items(), key=lambda item: item[1][0]))
                ),
                "aspects_min": dict(
                    sorted(aspects_min.items(), key=lambda item: item[1][0])
                ),
                "aspects_count": dict(
                    reversed(sorted(aspects_count.items(), key=lambda item: item[1][0]))
                ),
                "aspects_sum": dict(
                    reversed(sorted(aspects_sum.items(), key=lambda item: item[1][0]))
                ),
                "aspects_positive_sum": dict(
                    reversed(
                        sorted(
                            aspects_positive_sum.items(), key=lambda item: item[1][0]
                        )
                    )
                ),
                "attributes_max": dict(
                    reversed(
                        sorted(attributes_max.items(), key=lambda item: item[1][0])
                    )
                ),
                "attributes_min": dict(
                    sorted(attributes_min.items(), key=lambda item: item[1][0])
                ),
                "attributes_count": dict(
                    reversed(
                        sorted(attributes_count.items(), key=lambda item: item[1][0])
                    )
                ),
                "attributes_sum": dict(
                    reversed(
                        sorted(attributes_sum.items(), key=lambda item: item[1][0])
                    )
                ),
                "attributes_positive_sum": dict(
                    reversed(
                        sorted(
                            attributes_positive_sum.items(), key=lambda item: item[1][0]
                        )
                    )
                ),
                "skills_max": dict(
                    reversed(sorted(skills_max.items(), key=lambda item: item[1][0]))
                ),
                "skills_min": dict(
                    sorted(skills_min.items(), key=lambda item: item[1][0])
                ),
                "skills_count": dict(
                    reversed(sorted(skills_count.items(), key=lambda item: item[1][0]))
                ),
                "skills_sum": dict(
                    reversed(sorted(skills_sum.items(), key=lambda item: item[1][0]))
                ),
                "skills_positive_sum": dict(
                    reversed(
                        sorted(skills_positive_sum.items(), key=lambda item: item[1][0])
                    )
                ),
                "all_extensions": Extension.objects.filter(is_active=True),
                "active_extension": active_extension,
            }
        )
        return context


class ExtensionGrid(TemplateView):
    template_name = "curators_desk/fragments/extension_grid.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["extensions"] = Extension.objects.all()
        context["type"] = kwargs.get("type")
        if kwargs.get("type") == "template":
            context["object_list"] = Template.objects.all()
            context["admin_url"] = "admin:rules_template_change"
        elif kwargs.get("type") == "lineage":
            context["object_list"] = Lineage.objects.all()
            context["admin_url"] = "admin:rules_lineage_change"
        elif kwargs.get("type") == "skill":
            context["object_list"] = Skill.objects.all()
            context["admin_url"] = "admin:rules_skill_change"
        elif kwargs.get("type") == "item":
            context["object_list"] = Item.objects.all()
            context["admin_url"] = "admin:armory_item_change"
        elif kwargs.get("type") == "weapon":
            context["object_list"] = Weapon.objects.all()
            context["admin_url"] = "admin:armory_weapon_change"
        elif kwargs.get("type") == "weaponmodification":
            context["object_list"] = WeaponModification.objects.all()
            context["admin_url"] = "admin:armory_weaponmodification_change"
        elif kwargs.get("type") == "riotgear":
            context["object_list"] = RiotGear.objects.all()
            context["admin_url"] = "admin:armory_riotgear_change"
        return context

    def post(self, request, *args, **kwargs):
        if kwargs.get("type") == "template":
            obj = Template.objects.get(id=request.POST.get("object"))
        elif kwargs.get("type") == "lineage":
            obj = Lineage.objects.get(id=request.POST.get("object"))
        elif kwargs.get("type") == "skill":
            obj = Skill.objects.get(id=request.POST.get("object"))
        elif kwargs.get("type") == "item":
            obj = Item.objects.get(id=request.POST.get("object"))
        elif kwargs.get("type") == "weapon":
            obj = Weapon.objects.get(id=request.POST.get("object"))
        elif kwargs.get("type") == "weaponmodification":
            obj = WeaponModification.objects.get(id=request.POST.get("object"))
        elif kwargs.get("type") == "riotgear":
            obj = RiotGear.objects.get(id=request.POST.get("object"))
        else:
            return HttpResponse(
                mark_safe('<i class="fas fa-question text-warning"></i>')
            )
        extension = Extension.objects.get(id=request.POST.get("extension"))

        if extension in obj.extensions.all():
            obj.extensions.remove(extension)
            return HttpResponse(mark_safe('<i class="fas fa-times text-danger"></i>'))
        else:
            obj.extensions.add(extension)
            return HttpResponse(mark_safe('<i class="fas fa-check text-success"></i>'))


class TranslationStatusView(TemplateView):
    template_name = "curators_desk//fragments/translation_status.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["translation_models"] = [
            {
                "name": model._meta.verbose_name,
                "id": model.__mro__[0].__name__,
                "admin_url_name": f"admin:{model._meta.app_label}_{model.__mro__[0].__name__.lower()}_change",
                "qs": model.objects.all(),
                "translatable_fields": [
                    field for field in model._meta.translatable_fields
                ],
            }
            for model in get_models_with_translations()
        ]

        return context


class ReviewHomebrewView(TemplateView):
    template_name = "curators_desk/fragments/review_homebrew.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["homebrew_querysets"] = [
            model.objects.filter(is_homebrew=True, keep_as_homebrew=False)
            for model in get_homebrew_models()
        ]
        return context


class KeepHomebrewView(View):
    def post(self, request, *args, **kwargs):
        model_name = request.POST.get("model_name")
        object_id = request.POST.get("object_id")

        model = None
        for m in get_homebrew_models():
            if m.__name__ == model_name:
                model = m
                break

        if model:
            try:
                obj = model.objects.get(id=object_id)
                obj.keep_as_homebrew = True
                obj.save()

                response = HttpResponse(status=204)
                response["HX-Trigger"] = "refresh-curators-desk-review-homebrew"
                return response
            except model.DoesNotExist:
                return HttpResponse("Object not found", status=404)

        return HttpResponse("Model not found", status=400)
