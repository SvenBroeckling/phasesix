from django.template import Library

from homebrew.models import HomebrewQuerySet

register = Library()


@register.filter
def without_homebrew(qs: HomebrewQuerySet):
    return qs.without_homebrew()
