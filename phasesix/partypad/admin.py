from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from partypad.models import Pad, PadObject


class PadObjectInline(TabularInline):
    model = PadObject


@admin.register(Pad)
class PadAdmin(ModelAdmin):
    list_display = ("id", "created_at", "created_by", "campaign")
    list_filter = ("campaign", "created_by", "created_at")
    search_fields = ("id",)
    inlines = [PadObjectInline]
