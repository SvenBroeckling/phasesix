from django.contrib import admin

from magic.models import BaseSpell, SpellType, SpellVariant

admin.site.register(BaseSpell)
admin.site.register(SpellType)
admin.site.register(SpellVariant)
