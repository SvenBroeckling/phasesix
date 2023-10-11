from django.template import Library

from worlds.models import WikiPageGameAction

register = Library()


@register.simple_tag
def entity_work(character, priest_action):
    if character.entity is None or priest_action.work_type is None:
        return []
    return WikiPageGameAction.objects.filter(
        entity_work_type=priest_action.work_type,
        wiki_page__entity=character.entity

    )
