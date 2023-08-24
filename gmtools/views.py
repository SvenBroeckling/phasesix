from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView

from armory.models import (
    Item,
    Weapon,
    WeaponModification,
    RiotGear,
)
from gmtools.utils import get_models_with_translations
from magic.models import BaseSpell
from rules.models import (
    Extension,
    Template,
    Lineage,
    Skill,
    CHARACTER_ASPECT_CHOICES,
    Attribute,
)


class TranslationStatusView(TemplateView):
    template_name = "gmtools/translation_status.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["translation_models"] = [
            {
                "name": model._meta.verbose_name,
                "id": model.__mro__[0].__name__,
                "admin_url_name": f"admin:{model._meta.app_label}_{model.__mro__[0].__name__.lower()}_change",
                "qs": model.objects.all(),
                "translatable_fields": [field for field in model._meta.translatable_fields],
            }
            for model in get_models_with_translations()
        ]

        return context


class TemplateStatisticsView(TemplateView):
    template_name = "gmtools/template_statistics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        aspects_sum = {}
        aspects_positive_sum = {}
        aspects_count = {}
        aspects_max = {}
        aspects_min = {}
        attributes_sum = {}
        attributes_positive_sum = {}
        attributes_count = {}
        attributes_max = {}
        attributes_min = {}
        skills_sum = {}
        skills_positive_sum = {}
        skills_count = {}
        skills_max = {}
        skills_min = {}

        for a in CHARACTER_ASPECT_CHOICES:
            aspects_sum[a[0]] = [0, []]  # Sum, Templates
            aspects_positive_sum[a[0]] = [0, []]
            aspects_count[a[0]] = [0, []]
            aspects_max[a[0]] = [-999, []]
            aspects_min[a[0]] = [999, []]

        for s in Skill.objects.all():
            skills_sum[s] = [0, []]  # Sum, Templates
            skills_positive_sum[s] = [0, []]
            skills_count[s] = [0, []]
            skills_max[s] = [-999, []]
            skills_min[s] = [999, []]

        for a in Attribute.objects.all():
            attributes_sum[a] = [0, []]  # Sum, Templates
            attributes_positive_sum[a] = [0, []]  # Sum, Templates
            attributes_count[a] = [0, []]
            attributes_max[a] = [-999, []]
            attributes_min[a] = [999, []]

        extension_id = self.request.GET.get("e", None)
        if extension_id is not None:
            active_extension = Extension.objects.get(id=extension_id)
            templates = Template.objects.filter(extensions=active_extension)
        else:
            active_extension = None
            templates = Template.objects.all()

        for t in templates:
            for m in t.templatemodifier_set.all():
                if m.aspect:
                    aspects_sum[m.aspect][0] += m.aspect_modifier
                    aspects_sum[m.aspect][1].append(t)

                    if m.aspect_modifier > 0:
                        aspects_positive_sum[m.aspect][0] += m.aspect_modifier
                        aspects_positive_sum[m.aspect][1].append(t)

                    aspects_count[m.aspect][0] += 1
                    aspects_count[m.aspect][1].append(t)

                    if m.aspect_modifier > aspects_max[m.aspect][0]:
                        aspects_max[m.aspect][0] = m.aspect_modifier
                        aspects_max[m.aspect][1] = [t]
                    elif m.aspect_modifier == aspects_max[m.aspect][0]:
                        aspects_max[m.aspect][1].append(t)
                    if m.aspect_modifier < aspects_max[m.aspect][0]:
                        aspects_min[m.aspect][0] = m.aspect_modifier
                        aspects_min[m.aspect][1] = [t]
                    elif m.aspect_modifier == aspects_min[m.aspect][0]:
                        aspects_min[m.aspect][1].append(t)

                if m.skill:
                    skills_sum[m.skill][0] += m.skill_modifier
                    skills_sum[m.skill][1].append(t)

                    if m.skill_modifier > 0:
                        skills_positive_sum[m.skill][0] += m.skill_modifier
                        skills_positive_sum[m.skill][1].append(t)

                    skills_count[m.skill][0] += 1
                    skills_count[m.skill][1].append(t)

                    if m.skill_modifier > skills_max[m.skill][0]:
                        skills_max[m.skill][0] = m.skill_modifier
                        skills_max[m.skill][1] = [t]
                    elif m.skill_modifier == skills_max[m.skill][0]:
                        skills_max[m.skill][1].append(t)
                    if m.skill_modifier < skills_min[m.skill][0]:
                        skills_min[m.skill][0] = m.skill_modifier
                        skills_min[m.skill][1] = [t]
                    elif m.skill_modifier == skills_min[m.skill][0]:
                        skills_min[m.skill][1].append(t)

                if m.attribute:
                    attributes_sum[m.attribute][0] += m.attribute_modifier
                    attributes_sum[m.attribute][1].append(t)

                    if m.attribute_modifier > 0:
                        attributes_positive_sum[m.attribute][0] += m.attribute_modifier
                        attributes_positive_sum[m.attribute][1].append(t)

                    attributes_count[m.attribute][0] += 1
                    attributes_count[m.attribute][1].append(t)

                    if m.attribute_modifier > attributes_max[m.attribute][0]:
                        attributes_max[m.attribute][0] = m.attribute_modifier
                        attributes_max[m.attribute][1] = [t]
                    elif m.attribute_modifier == attributes_max[m.attribute][0]:
                        attributes_max[m.attribute][1].append(t)
                    if m.attribute_modifier < attributes_min[m.attribute][0]:
                        attributes_min[m.attribute][0] = m.attribute_modifier
                        attributes_min[m.attribute][1] = [t]
                    elif m.attribute_modifier == attributes_min[m.attribute][0]:
                        attributes_min[m.attribute][1].append(t)

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
    template_name = "gmtools/extension_grid.html"

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
