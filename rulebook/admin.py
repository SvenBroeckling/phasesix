from django.contrib import admin
from reversion.admin import VersionAdmin

from rulebook.models import Book, Chapter


class ChapterAdmin(VersionAdmin):
    list_display = "name_de", "name_en", "number", "fa_icon_class"
    list_editable = ("number",)


admin.site.register(Book, VersionAdmin)
admin.site.register(Chapter, ChapterAdmin)
