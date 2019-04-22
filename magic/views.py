from django.http import JsonResponse
from django.views.generic import TemplateView

from characters.models import Character


class XhrSpellView(TemplateView):
    template_name = 'magic/_spell.html'

    def get_context_data(self, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        context = super(XhrSpellView, self).get_context_data(**kwargs)
        context['object'] = character
        return context

    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        if not character.may_edit(request.user):
            return JsonResponse({'status': 'forbidden'})
        return JsonResponse({'status': 'ok'})

