from django.contrib import admin
from unfold.admin import ModelAdmin

from rulebook.models import Book, Chapter, WorldBook


@admin.register(Chapter)
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


@admin.register(WorldBook)
class WorldBookAdmin(ModelAdmin):
    list_display = "world", "book", "book_title", "ordering"
    list_editable = ("ordering",)
    filter_horizontal = ("disabled_chapters",)


admin.site.register(Book, ModelAdmin)
