from django.contrib import admin
from unfold.admin import ModelAdmin

from forum.models import Board, Thread, Post

admin.site.register(Board, ModelAdmin)
admin.site.register(Thread, ModelAdmin)
admin.site.register(Post, ModelAdmin)
