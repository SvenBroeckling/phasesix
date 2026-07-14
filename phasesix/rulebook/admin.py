from django.contrib import admin
from django.utils.translation import gettext_lazy as _
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
    fieldsets = [
        (None, {"fields": (("name_de", "name_en"), ("book", "number", "identifier"), "fa_icon_class", ("rules_file_de", "rules_file_en"))}),
        (_("Image"), {"fields": ("image", ("image_copyright", "image_copyright_url"), ("image_focal_x", "image_focal_y")), "classes": ("collapse",)}),
        (_("Homebrew"), {"fields": (("is_homebrew", "keep_as_homebrew"), "created_by", ("homebrew_campaign", "homebrew_character")), "classes": ("collapse",)}),
    ]


@admin.register(WorldBook)
class WorldBookAdmin(ModelAdmin):
    list_display = "world", "book", "book_title", "ordering"
    list_editable = ("ordering",)
    filter_horizontal = ("disabled_chapters",)
    fieldsets = [
        (None, {"fields": (("world", "book", "ordering"), ("book_title_de", "book_title_en"), ("book_claim_de", "book_claim_en"), ("description_de", "description_en"), "disabled_chapters")}),
        (_("Downloads"), {"fields": (("pdf_online_de", "pdf_online_en"), ("pdf_print_de", "pdf_print_en"), ("preview_image_de", "preview_image_en")), "classes": ("collapse",)}),
        (_("Presentation"), {"fields": ("book_title_image", "book_website", ("book_heading_font", "book_body_font")), "classes": ("collapse",)}),
    ]


admin.site.register(Book, ModelAdmin)
