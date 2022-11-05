from django.template import Library

from worlds.models import World

register = Library()


@register.simple_tag
def get_all_worlds():
    return World.objects.all()
