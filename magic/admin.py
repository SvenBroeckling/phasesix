from django.contrib import admin

from magic.models import SpellCost, SpellRange, SpellAreaOfEffect, SpellComponents, SpellCastingTime, SpellType, \
    SpellPower, SpellFlavour

admin.site.register(SpellCost)
admin.site.register(SpellRange)
admin.site.register(SpellAreaOfEffect)
admin.site.register(SpellComponents)
admin.site.register(SpellCastingTime)
admin.site.register(SpellType)
admin.site.register(SpellPower)
admin.site.register(SpellFlavour)

