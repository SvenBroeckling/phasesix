from django.contrib import admin

from rulebook.models import Book, Chapter


class ChapterAdmin(admin.ModelAdmin):
    list_display = 'name_de', 'name_en', 'number', 'fa_icon_class'


admin.site.register(Book)
admin.site.register(Chapter, ChapterAdmin)


