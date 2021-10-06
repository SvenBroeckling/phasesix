import os

import yaml
from django.conf import settings
from django.utils.translation import get_language
from django.views.generic import TemplateView
from markdown import markdown


class ChapterDetailView(TemplateView):
    template_name = 'rulebook/chapter_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        language = get_language()

        with open(os.path.join(settings.RULEBOOK_ROOT, f'structure_{language}.yml'), 'r') as yml_file:
            structure = yaml.load(yml_file, Loader=yaml.Loader)

        chapter = structure[int(kwargs['pk']) - 1]
        with open(os.path.join(settings.RULEBOOK_ROOT, 'src', 'md', chapter['file'])) as chapter_file:
            chapter['content'] = markdown(chapter_file.read(), extensions=['markdown.extensions.tables'])
            chapter['image_url'] = 'rulebook/src/img/{}'.format(chapter['image'])

        context['object'] = chapter
        context['structure'] = structure

        return context
