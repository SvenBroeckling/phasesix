from django.contrib import admin

from forum.models import Board, Thread, Post

admin.site.register(Board)
admin.site.register(Thread)
admin.site.register(Post)
