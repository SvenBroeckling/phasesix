from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import (
    EssentialBond,
    EssentialCharacter,
    EssentialCharacterSkill,
)

admin.site.register(
    [
        EssentialBond,
        EssentialCharacter,
        EssentialCharacterSkill,
    ],
    ModelAdmin,
)
