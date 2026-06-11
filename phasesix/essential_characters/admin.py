from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import (
    EssentialAncestry,
    EssentialBond,
    EssentialCharacter,
    EssentialCharacterSkill,
    EssentialPath,
)

admin.site.register(
    [
        EssentialAncestry,
        EssentialBond,
        EssentialCharacter,
        EssentialCharacterSkill,
        EssentialPath,
    ],
    ModelAdmin,
)
