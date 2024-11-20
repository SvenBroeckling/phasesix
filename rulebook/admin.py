from django.contrib import admin
from unfold.admin import ModelAdmin

from rulebook.models import Book, Chapter, WorldBook


class ChapterAdmin(ModelAdmin):
    list_display = (
        "name_de",
        "name_en",
        "identifier",
        "number",
        "fa_icon_class",
        "image",
    )
    list_editable = ("number", "identifier")


admin.site.register(WorldBook, ModelAdmin)
admin.site.register(Book, ModelAdmin)
admin.site.register(Chapter, ChapterAdmin)
