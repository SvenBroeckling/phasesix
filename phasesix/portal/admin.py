from django.db.models import Value, Q
from django.db.models.functions import Length, Coalesce
from django.utils.translation import gettext_lazy as _
from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User, Group
from unfold.admin import ModelAdmin, StackedInline

from portal.models import Profile


class ShortValueListFilter(admin.SimpleListFilter):
    title = _("Short or no value")
    parameter_name = "short_value"
    field_name = "field"

    def lookups(self, request, model_admin):
        return [
            ("yes", _("Yes")),
            ("no", _("No")),
        ]

    def queryset(self, request, queryset):
        qs = queryset.annotate(
            de_length=Coalesce(Length(f"{self.field_name}_de"), Value(0))
        ).annotate(en_length=Coalesce(Length(f"{self.field_name}_en"), Value(0)))
        if self.value() == "yes":
            return qs.filter(Q(de_length__lte=10) | Q(en_length__lte=10))
        if self.value() == "no":
            return qs.filter(Q(de_length__gt=10) & Q(en_length__gt=10))
        return queryset


class ShortDescriptionListFilter(ShortValueListFilter):
    title = _("Short or no description")
    parameter_name = "short_description"
    field_name = "description"


class ShortShortDescriptionListFilter(ShortValueListFilter):
    title = _("Short or no short description")
    parameter_name = "short_short_description"
    field_name = "short_description"


class ShortRulesListFilter(ShortValueListFilter):
    title = _("Short or no description")
    parameter_name = "short_rules"
    field_name = "rules"


class ProfileInline(StackedInline):
    model = Profile


class UserAdmin(ModelAdmin, BaseUserAdmin):
    inlines = [ProfileInline]


class GroupAdmin(ModelAdmin, BaseGroupAdmin):
    pass


admin.site.unregister(User)
admin.site.unregister(Group)
admin.site.register(User, UserAdmin)
admin.site.register(Group, GroupAdmin)


@admin.register(Profile)
class ProfileAdmin(ModelAdmin):
    list_display = ("user", "may_use_ai", "created_at", "updated_at")
    list_filter = ("may_use_ai",)
