from django.contrib import admin
from .models import (
    EssentialAncestry, EssentialArmorProfile, EssentialBond, EssentialCharacter,
    EssentialCharacterArmor, EssentialCharacterItem, EssentialCharacterSkill,
    EssentialCharacterSpell, EssentialCharacterWeapon, EssentialMagicAspectProfile,
    EssentialPath, EssentialSkill, EssentialSpellProfile, EssentialWeaponProfile,
)

admin.site.register([
    EssentialAncestry, EssentialArmorProfile, EssentialBond, EssentialCharacter,
    EssentialCharacterArmor, EssentialCharacterItem, EssentialCharacterSkill,
    EssentialCharacterSpell, EssentialCharacterWeapon, EssentialMagicAspectProfile,
    EssentialPath, EssentialSkill, EssentialSpellProfile, EssentialWeaponProfile,
])
