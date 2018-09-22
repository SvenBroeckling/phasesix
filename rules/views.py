# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.generic import ListView

from rules.models import Template


class TemplateListView(ListView):
    model = Template

