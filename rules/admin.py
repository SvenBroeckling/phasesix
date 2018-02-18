# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from rules.models import Skill, Extension, Quirk, Gift, Knowledge

admin.site.register(Extension)
admin.site.register(Skill)
admin.site.register(Knowledge)
admin.site.register(Quirk)
admin.site.register(Gift)
