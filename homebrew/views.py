from django.views.generic import TemplateView, CreateView

from armory.models import Item


class IndexView(TemplateView):
    template_name = 'homebrew/index.html'


class CreateItemView(CreateView):
    model = Item
    template_name = 'homebrew/item_form.html'
    fields = ('name_de', 'name_en', 'description_de', 'description_en', 'type', 'weight', 'price',
              'concealment', 'extensions', 'usable_in_combat')
