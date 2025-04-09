from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User, Group
from unfold.admin import ModelAdmin


class UserAdmin(ModelAdmin, BaseUserAdmin):
    pass


class GroupAdmin(ModelAdmin, BaseGroupAdmin):
    pass


admin.site.unregister(User)
admin.site.unregister(Group)
admin.site.register(User, UserAdmin)
admin.site.register(Group, GroupAdmin)
